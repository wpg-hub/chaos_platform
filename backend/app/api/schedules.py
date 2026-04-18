from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from croniter import croniter

from app.core.database import get_db, User, Case, Schedule
from app.core.security import get_current_user, require_user
from app.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse

router = APIRouter(prefix="/api/schedules", tags=["定时任务"])


@router.get("", response_model=ScheduleListResponse)
async def get_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Schedule).options(
        selectinload(Schedule.case),
        selectinload(Schedule.creator)
    )
    
    if is_active is not None:
        query = query.where(Schedule.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Schedule.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    items = []
    for schedule in schedules:
        schedule_dict = ScheduleResponse.model_validate(schedule).model_dump()
        schedule_dict["case_name"] = schedule.case.name if schedule.case else None
        schedule_dict["creator_name"] = schedule.creator.username if schedule.creator else None
        items.append(ScheduleResponse(**schedule_dict))
    
    return ScheduleListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Schedule).options(
        selectinload(Schedule.case),
        selectinload(Schedule.creator)
    ).where(Schedule.id == schedule_id)
    
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule_dict = ScheduleResponse.model_validate(schedule).model_dump()
    schedule_dict["case_name"] = schedule.case.name if schedule.case else None
    schedule_dict["creator_name"] = schedule.creator.username if schedule.creator else None
    
    return ScheduleResponse(**schedule_dict)


@router.post("", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Case).where(Case.id == schedule_data.case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    try:
        cron = croniter(schedule_data.cron_expr)
        next_run = cron.get_next(datetime)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {e}")
    
    schedule = Schedule(
        name=schedule_data.name,
        case_id=schedule_data.case_id,
        cron_expr=schedule_data.cron_expr,
        creator_id=current_user.id,
        next_run=next_run
    )
    
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    
    return await get_schedule(schedule.id, db, current_user)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    update_data = schedule_data.model_dump(exclude_unset=True)
    
    if "cron_expr" in update_data:
        try:
            cron = croniter(update_data["cron_expr"])
            update_data["next_run"] = cron.get_next(datetime)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {e}")
    
    for key, value in update_data.items():
        setattr(schedule, key, value)
    
    await db.commit()
    
    return await get_schedule(schedule_id, db, current_user)


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.is_active = not schedule.is_active
    
    if schedule.is_active:
        cron = croniter(schedule.cron_expr)
        schedule.next_run = cron.get_next(datetime)
    else:
        schedule.next_run = None
    
    await db.commit()
    
    return {"message": f"Schedule {'enabled' if schedule.is_active else 'disabled'}"}


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    await db.delete(schedule)
    await db.commit()
    
    return {"message": "Schedule deleted"}
