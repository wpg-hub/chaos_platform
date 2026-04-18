import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db, User, Case, Tag, CaseTag, Folder
from app.core.security import get_current_user, require_admin, require_user
from app.schemas import (
    CaseCreate, CaseUpdate, CaseResponse, CaseListResponse,
    CaseValidateRequest, CaseValidateResponse, CaseImportRequest,
    FolderResponse, TagCreate, TagResponse,
    CaseCopyRequest, CaseMoveRequest, CaseRenameRequest
)

router = APIRouter(prefix="/api/cases", tags=["用例管理"])


@router.get("", response_model=CaseListResponse)
async def get_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    folder_id: Optional[int] = None,
    tag: Optional[str] = None,
    keyword: Optional[str] = None,
    is_template: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Case).options(selectinload(Case.tags), selectinload(Case.creator))
    
    if folder_id is not None:
        query = query.where(Case.folder_id == folder_id)
    if tag:
        query = query.join(CaseTag).join(Tag).where(Tag.name == tag)
    if keyword:
        query = query.where(or_(Case.name.contains(keyword), Case.description.contains(keyword)))
    if is_template is not None:
        query = query.where(Case.is_template == is_template)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Case.sort_order, Case.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    items = []
    for case in cases:
        case_dict = {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "yaml_content": case.yaml_content,
            "file_path": case.file_path,
            "case_type": case.case_type,
            "folder_id": case.folder_id,
            "is_template": case.is_template,
            "sort_order": case.sort_order,
            "creator_id": case.creator_id,
            "tags": [TagResponse.model_validate(t) for t in case.tags],
            "created_at": case.created_at,
            "updated_at": case.updated_at
        }
        items.append(CaseResponse(**case_dict))
    
    return CaseListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/tags", response_model=List[TagResponse])
async def get_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Tag))
    tags = result.scalars().all()
    return [TagResponse.model_validate(t) for t in tags]


@router.post("/tags", response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Tag).where(Tag.name == tag_data.name))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    tag = Tag(name=tag_data.name, color=tag_data.color)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse.model_validate(tag)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Case).options(selectinload(Case.tags), selectinload(Case.creator)).where(Case.id == case_id)
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return CaseResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        yaml_content=case.yaml_content,
        file_path=case.file_path,
        case_type=case.case_type,
        folder_id=case.folder_id,
        is_template=case.is_template,
        sort_order=case.sort_order,
        creator_id=case.creator_id,
        tags=[TagResponse.model_validate(t) for t in case.tags],
        created_at=case.created_at,
        updated_at=case.updated_at
    )


@router.post("", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    case = Case(
        name=case_data.name,
        description=case_data.description,
        yaml_content=case_data.yaml_content,
        folder_id=case_data.folder_id,
        is_template=case_data.is_template,
        creator_id=current_user.id
    )
    
    if case_data.tags:
        for tag_name in case_data.tags:
            tag_result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            case.tags.append(tag)
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return await get_case(case.id, db, current_user)


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    query = select(Case).options(selectinload(Case.tags)).where(Case.id == case_id)
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    update_data = case_data.model_dump(exclude_unset=True, exclude={"tags"})
    for key, value in update_data.items():
        setattr(case, key, value)
    
    if case_data.tags is not None:
        case.tags.clear()
        for tag_name in case_data.tags:
            tag_result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            case.tags.append(tag)
    
    await db.commit()
    return await get_case(case_id, db, current_user)


@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    await db.delete(case)
    await db.commit()
    
    return {"message": "Case deleted successfully"}


@router.post("/validate", response_model=CaseValidateResponse)
async def validate_yaml(
    request: CaseValidateRequest,
    current_user: User = Depends(get_current_user)
):
    import yaml
    
    try:
        data = yaml.safe_load(request.yaml_content)
        if not data:
            return CaseValidateResponse(valid=False, error="Empty YAML content")
        
        if "workflow" in data:
            case_type = "workflow"
        elif "name" in data:
            case_type = "case"
        else:
            return CaseValidateResponse(valid=False, error="Invalid case format: missing 'name' or 'workflow'")
        
        return CaseValidateResponse(valid=True, case_type=case_type)
    except yaml.YAMLError as e:
        return CaseValidateResponse(valid=False, error=str(e))


@router.post("/import", response_model=CaseResponse)
async def import_case(
    request: CaseImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    import yaml
    
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(request.file_path, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    
    name = request.name or data.get("name") or data.get("workflow", {}).get("name") or os.path.basename(request.file_path)
    
    case_type = "workflow" if "workflow" in data else "case"
    
    case = Case(
        name=name,
        description=data.get("description", ""),
        yaml_content=yaml_content,
        file_path=request.file_path,
        case_type=case_type,
        folder_id=request.folder_id,
        creator_id=current_user.id
    )
    
    if request.tags:
        for tag_name in request.tags:
            tag_result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            case.tags.append(tag)
    
    db.add(case)
    await db.commit()
    
    return await get_case(case.id, db, current_user)


@router.post("/{case_id}/copy", response_model=CaseResponse)
async def copy_case(
    case_id: int,
    request: CaseCopyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    query = select(Case).options(selectinload(Case.tags)).where(Case.id == case_id)
    result = await db.execute(query)
    original_case = result.scalar_one_or_none()
    
    if not original_case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    new_name = request.name or f"{original_case.name} - 副本"
    new_folder_id = request.folder_id if request.folder_id is not None else original_case.folder_id
    
    new_case = Case(
        name=new_name,
        description=original_case.description,
        yaml_content=original_case.yaml_content,
        file_path=original_case.file_path,
        case_type=original_case.case_type,
        folder_id=new_folder_id,
        is_template=original_case.is_template,
        creator_id=current_user.id
    )
    
    for tag in original_case.tags:
        new_case.tags.append(tag)
    
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    
    return await get_case(new_case.id, db, current_user)


@router.put("/{case_id}/rename", response_model=CaseResponse)
async def rename_case(
    case_id: int,
    request: CaseRenameRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.name = request.name
    await db.commit()
    
    return await get_case(case_id, db, current_user)


@router.put("/{case_id}/move", response_model=CaseResponse)
async def move_case(
    case_id: int,
    request: CaseMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if request.folder_id is not None:
        if request.folder_id != 0:
            folder_result = await db.execute(select(Folder).where(Folder.id == request.folder_id))
            folder = folder_result.scalar_one_or_none()
            if not folder:
                raise HTTPException(status_code=400, detail="Target folder not found")
        case.folder_id = request.folder_id if request.folder_id != 0 else None
    
    if request.sort_order is not None:
        case.sort_order = request.sort_order
    
    await db.commit()
    
    return await get_case(case_id, db, current_user)
