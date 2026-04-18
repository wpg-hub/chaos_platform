import os
import sys
import json
import traceback
from datetime import datetime
from typing import Optional

from celery import Celery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app.core.config import settings
from app.core.database import sync_session_maker, Execution, ExecutionLog, ExecutionStatus, Case, Schedule

celery_app = Celery(
    "chaos_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)


def sync_send_log(execution_id: int, level: str, message: str, log_file: Optional[str] = None):
    with sync_session_maker() as db:
        log = ExecutionLog(
            execution_id=execution_id,
            level=level,
            message=message
        )
        db.add(log)
        db.commit()
    
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{level}] {timestamp} {message}\n")


def sync_update_status(execution_id: int, status: str, error_message: Optional[str] = None):
    with sync_session_maker() as db:
        execution = db.execute(select(Execution).where(Execution.id == execution_id)).scalar_one_or_none()
        if execution:
            execution.status = status
            if status in [ExecutionStatus.SUCCESS.value, ExecutionStatus.FAILED.value, 
                         ExecutionStatus.CANCELLED.value, ExecutionStatus.TIMEOUT.value]:
                execution.end_time = datetime.now()
                if execution.start_time:
                    execution.duration = (execution.end_time - execution.start_time).total_seconds()
            if error_message:
                execution.error_message = error_message
            db.commit()


@celery_app.task(bind=True)
def execute_case_task(self, execution_id: int):
    with sync_session_maker() as db:
        execution = db.execute(
            select(Execution)
            .options(selectinload(Execution.case))
            .where(Execution.id == execution_id)
        ).scalar_one_or_none()
        
        if not execution:
            return
        
        case = execution.case
        if not case:
            sync_update_status(execution_id, ExecutionStatus.FAILED.value, "Case not found")
            return
        
        log_file = execution.log_file_path
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        sync_send_log(execution_id, "INFO", f"开始执行用例: {case.name}", log_file)
        sync_update_status(execution_id, ExecutionStatus.RUNNING.value)
        
        execution.start_time = datetime.now()
        db.commit()
        
        try:
            import tempfile
            import yaml
            from chaos.case.base import CaseManager, CaseExecutor
            from chaos.config import ConfigManager
            from chaos.fault.base import FaultFactory
            from chaos.state.manager import StateManager, FileFaultRepository
            from chaos.utils.logger import Logger
            from chaos.workflow import WorkflowParser, WorkflowExecutor
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(case.yaml_content)
                temp_file = f.name
            
            sync_send_log(execution_id, "INFO", f"创建临时用例文件: {temp_file}", log_file)
            
            try:
                case_data = yaml.safe_load(case.yaml_content)
                
                if "workflow" in case_data:
                    sync_send_log(execution_id, "INFO", "检测到 Workflow 类型用例", log_file)
                    
                    logger = Logger(name=f"workflow_{execution_id}")
                    parser = WorkflowParser(logger)
                    workflow = parser.parse(temp_file)
                    
                    config_manager = ConfigManager()
                    fault_factory = FaultFactory()
                    state_manager = StateManager(FileFaultRepository(), logger)
                    
                    executor = WorkflowExecutor(
                        config_manager,
                        fault_factory,
                        state_manager,
                        logger,
                        max_workers=10
                    )
                    
                    result = executor.execute(workflow)
                    
                    if result.status.value == "success":
                        sync_send_log(execution_id, "INFO", "Workflow 执行成功", log_file)
                        sync_update_status(execution_id, ExecutionStatus.SUCCESS.value)
                    else:
                        sync_send_log(execution_id, "ERROR", f"Workflow 执行失败: {result.error_message}", log_file)
                        sync_update_status(execution_id, ExecutionStatus.FAILED.value, result.error_message)
                else:
                    sync_send_log(execution_id, "INFO", "检测到 Case 类型用例", log_file)
                    
                    logger = Logger(name=f"case_{execution_id}")
                    config_manager = ConfigManager()
                    fault_factory = FaultFactory()
                    state_manager = StateManager(FileFaultRepository(), logger)
                    case_executor = CaseExecutor(config_manager, fault_factory, state_manager, logger)
                    case_manager = CaseManager(case_executor, logger)
                    
                    success = case_manager.execute_single(temp_file)
                    
                    if success:
                        sync_send_log(execution_id, "INFO", "Case 执行成功", log_file)
                        sync_update_status(execution_id, ExecutionStatus.SUCCESS.value)
                    else:
                        sync_send_log(execution_id, "ERROR", "Case 执行失败", log_file)
                        sync_update_status(execution_id, ExecutionStatus.FAILED.value, "Case execution failed")
                
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    sync_send_log(execution_id, "INFO", "清理临时文件", log_file)
            
        except Exception as e:
            error_msg = f"执行异常: {str(e)}"
            sync_send_log(execution_id, "ERROR", error_msg, log_file)
            sync_send_log(execution_id, "ERROR", traceback.format_exc(), log_file)
            sync_update_status(execution_id, ExecutionStatus.FAILED.value, error_msg)
        
        sync_send_log(execution_id, "INFO", "执行结束", log_file)


@celery_app.task
def check_scheduled_tasks():
    from croniter import croniter
    
    with sync_session_maker() as db:
        now = datetime.now()
        schedules = db.execute(
            select(Schedule)
            .options(selectinload(Schedule.case))
            .where(Schedule.is_active == True)
            .where(Schedule.next_run <= now)
        ).scalars().all()
        
        for schedule in schedules:
            execute_case_task.delay(schedule.case_id)
            
            cron = croniter(schedule.cron_expr)
            schedule.next_run = cron.get_next(datetime)
            schedule.last_run = now
            
            db.commit()
    
    return "Checked scheduled tasks"


celery_app.conf.beat_schedule = {
    "check-scheduled-tasks": {
        "task": "app.tasks.execution_task.check_scheduled_tasks",
        "schedule": 60.0,
    },
}
