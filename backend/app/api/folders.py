from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db, User, Folder, Case
from app.core.security import get_current_user, require_user
from app.schemas import FolderCreate, FolderUpdate, FolderResponse

router = APIRouter(prefix="/api/folders", tags=["目录管理"])


async def build_folder_tree(folders: List[Folder], case_counts: dict) -> List[dict]:
    folder_map = {f.id: {
        "id": f.id,
        "name": f.name,
        "parent_id": f.parent_id,
        "creator_id": f.creator_id,
        "sort_order": f.sort_order,
        "created_at": f.created_at,
        "updated_at": f.updated_at,
        "children": [],
        "case_count": case_counts.get(f.id, 0)
    } for f in folders}
    
    root_folders = []
    for f in folders:
        folder_data = folder_map[f.id]
        if f.parent_id is None:
            root_folders.append(folder_data)
        else:
            parent = folder_map.get(f.parent_id)
            if parent:
                parent["children"].append(folder_data)
    
    def sort_folders(items: List[dict]) -> List[dict]:
        items.sort(key=lambda x: (x["sort_order"], x["name"]))
        for item in items:
            item["children"] = sort_folders(item["children"])
        return items
    
    return sort_folders(root_folders)


@router.get("", response_model=List[FolderResponse])
async def get_folders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Folder).order_by(Folder.sort_order, Folder.name))
    folders = result.scalars().all()
    
    case_count_result = await db.execute(
        select(Case.folder_id, func.count(Case.id)).group_by(Case.folder_id)
    )
    case_counts = {row[0]: row[1] for row in case_count_result.all() if row[0] is not None}
    
    tree = await build_folder_tree(list(folders), case_counts)
    return [FolderResponse(**item) for item in tree]


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    case_count_result = await db.execute(
        select(func.count(Case.id)).where(Case.folder_id == folder_id)
    )
    case_count = case_count_result.scalar() or 0
    
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        creator_id=folder.creator_id,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        children=[],
        case_count=case_count
    )


@router.post("", response_model=FolderResponse)
async def create_folder(
    folder_data: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    if folder_data.parent_id:
        result = await db.execute(select(Folder).where(Folder.id == folder_data.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent folder not found")
    
    folder = Folder(
        name=folder_data.name,
        parent_id=folder_data.parent_id,
        creator_id=current_user.id
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        creator_id=folder.creator_id,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        children=[],
        case_count=0
    )


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: int,
    folder_data: FolderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if folder_data.parent_id is not None:
        if folder_data.parent_id == folder_id:
            raise HTTPException(status_code=400, detail="Cannot set folder as its own parent")
        
        if folder_data.parent_id:
            parent_result = await db.execute(select(Folder).where(Folder.id == folder_data.parent_id))
            parent = parent_result.scalar_one_or_none()
            if not parent:
                raise HTTPException(status_code=400, detail="Parent folder not found")
            
            def check_descendant(f: Folder, target_id: int) -> bool:
                if f.parent_id == target_id:
                    return True
                if f.parent_id:
                    return check_descendant(next((p for p in [f] if f.parent_id), None), target_id)
                return False
        
    update_data = folder_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(folder, key, value)
    
    await db.commit()
    await db.refresh(folder)
    
    case_count_result = await db.execute(
        select(func.count(Case.id)).where(Case.folder_id == folder_id)
    )
    case_count = case_count_result.scalar() or 0
    
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        creator_id=folder.creator_id,
        sort_order=folder.sort_order,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
        children=[],
        case_count=case_count
    )


async def delete_folder_recursive(db: AsyncSession, folder_id: int):
    children_result = await db.execute(select(Folder).where(Folder.parent_id == folder_id))
    children = children_result.scalars().all()
    for child in children:
        await delete_folder_recursive(db, child.id)
    
    await db.execute(Case.__table__.delete().where(Case.folder_id == folder_id))
    
    await db.execute(Folder.__table__.delete().where(Folder.id == folder_id))


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    await delete_folder_recursive(db, folder_id)
    await db.commit()
    
    return {"message": "Folder deleted successfully"}
