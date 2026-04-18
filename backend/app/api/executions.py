import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db, User, Case, Execution, ExecutionLog, ExecutionStatus
from app.core.security import get_current_user, require_user
from app.schemas import ExecutionCreate, ExecutionResponse, ExecutionListResponse, ExecutionDetailResponse

router = APIRouter(prefix="/api/executions", tags=["执行管理"])


@router.get("", response_model=ExecutionListResponse)
async def get_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    case_id: Optional[int] = None,
    executor_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Execution).options(
        selectinload(Execution.case),
        selectinload(Execution.executor)
    )
    
    if status:
        query = query.where(Execution.status == status)
    if case_id:
        query = query.where(Execution.case_id == case_id)
    if executor_id:
        query = query.where(Execution.executor_id == executor_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Execution.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    items = []
    for exec in executions:
        exec_dict = ExecutionResponse.model_validate(exec).model_dump()
        exec_dict["case_name"] = exec.case.name if exec.case else None
        exec_dict["executor_name"] = exec.executor.username if exec.executor else None
        items.append(ExecutionResponse(**exec_dict))
    
    return ExecutionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Execution).options(
        selectinload(Execution.case),
        selectinload(Execution.executor),
        selectinload(Execution.logs)
    ).where(Execution.id == execution_id)
    
    result = await db.execute(query)
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    exec_dict = ExecutionDetailResponse.model_validate(execution).model_dump()
    exec_dict["case_name"] = execution.case.name if execution.case else None
    exec_dict["executor_name"] = execution.executor.username if execution.executor else None
    exec_dict["yaml_content"] = execution.case.yaml_content if execution.case else None
    
    return ExecutionDetailResponse(**exec_dict)


@router.post("", response_model=ExecutionResponse)
async def create_execution(
    execution_data: ExecutionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Case).where(Case.id == execution_data.case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    execution = Execution(
        case_id=case.id,
        executor_id=current_user.id,
        status=ExecutionStatus.PENDING.value,
        log_file_path=f"/app/logs/executions/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{case.id}.log"
    )
    
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    from app.tasks.execution_task import execute_case_task
    execute_case_task.delay(execution.id)
    
    exec_dict = ExecutionResponse.model_validate(execution).model_dump()
    exec_dict["case_name"] = case.name
    exec_dict["executor_name"] = current_user.username
    
    return ExecutionResponse(**exec_dict)


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status not in [ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value]:
        raise HTTPException(status_code=400, detail="Cannot cancel execution in current status")
    
    execution.status = ExecutionStatus.CANCELLED.value
    execution.end_time = datetime.now()
    await db.commit()
    
    return {"message": "Execution cancelled"}


@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ExecutionLog)
        .where(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.timestamp)
    )
    logs = result.scalars().all()
    
    return [{"level": log.level, "message": log.message, "timestamp": log.timestamp.isoformat()} for log in logs]


@router.get("/{execution_id}/report")
async def download_report(
    execution_id: int,
    format: str = Query("html", regex="^(html|pdf|excel)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import FileResponse
    
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if not execution.report_path or not os.path.exists(execution.report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        execution.report_path,
        filename=f"report_{execution_id}.{format}",
        media_type="application/octet-stream"
    )


@router.delete("/{execution_id}")
async def delete_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status == ExecutionStatus.RUNNING.value:
        raise HTTPException(status_code=400, detail="Cannot delete running execution")
    
    if execution.log_file_path and os.path.exists(execution.log_file_path):
        os.remove(execution.log_file_path)
    if execution.report_path and os.path.exists(execution.report_path):
        os.remove(execution.report_path)
    
    await db.delete(execution)
    await db.commit()
    
    return {"message": "Execution deleted"}


@router.delete("")
async def delete_executions(
    execution_ids: str = Query(..., description="Comma-separated execution IDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    ids = [int(id.strip()) for id in execution_ids.split(',') if id.strip()]
    for exec_id in ids:
        result = await db.execute(select(Execution).where(Execution.id == exec_id))
        execution = result.scalar_one_or_none()
        
        if execution and execution.status != ExecutionStatus.RUNNING.value:
            if execution.log_file_path and os.path.exists(execution.log_file_path):
                os.remove(execution.log_file_path)
            if execution.report_path and os.path.exists(execution.report_path):
                os.remove(execution.report_path)
            await db.delete(execution)
    
    await db.commit()
    
    return {"message": f"Deleted {len(ids)} executions"}
