from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from app.core.database import ExecutionStatus


class ExecutionCreate(BaseModel):
    case_id: int


class ExecutionResponse(BaseModel):
    id: int
    case_id: Optional[int] = None
    case_name: Optional[str] = None
    executor_id: Optional[int] = None
    executor_name: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    report_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    items: List[ExecutionResponse]
    total: int
    page: int
    page_size: int


class ExecutionLogResponse(BaseModel):
    id: int
    execution_id: int
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ExecutionDetailResponse(ExecutionResponse):
    logs: List[ExecutionLogResponse] = []
    yaml_content: Optional[str] = None
