from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ScheduleBase(BaseModel):
    name: str
    case_id: int
    cron_expr: str


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    cron_expr: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduleResponse(ScheduleBase):
    id: int
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    case_name: Optional[str] = None
    is_active: bool
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    items: List[ScheduleResponse]
    total: int
    page: int
    page_size: int
