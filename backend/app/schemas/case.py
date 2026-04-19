from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class TagBase(BaseModel):
    name: str
    color: Optional[str] = "#409EFF"


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class FolderResponse(FolderBase):
    id: int
    creator_id: Optional[int] = None
    sort_order: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: List["FolderResponse"] = []
    case_count: int = 0

    class Config:
        from_attributes = True


class CaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    yaml_content: str
    folder_id: Optional[int] = None
    is_template: bool = False


class CaseCreate(CaseBase):
    tags: List[str] = []


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    yaml_content: Optional[str] = None
    case_type: Optional[str] = None
    folder_id: Optional[int] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None


class CaseCopyRequest(BaseModel):
    name: Optional[str] = None
    folder_id: Optional[int] = None


class CaseMoveRequest(BaseModel):
    folder_id: Optional[int] = None
    sort_order: Optional[int] = None


class CaseRenameRequest(BaseModel):
    name: str


class CaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    yaml_content: str
    file_path: Optional[str] = None
    case_type: Optional[str] = None
    folder_id: Optional[int] = None
    is_template: bool = False
    sort_order: int = 0
    creator_id: Optional[int] = None
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int


class CaseValidateRequest(BaseModel):
    yaml_content: str


class CaseValidateResponse(BaseModel):
    valid: bool
    error: Optional[str] = None
    case_type: Optional[str] = None


class CaseImportRequest(BaseModel):
    file_path: str
    name: Optional[str] = None
    folder_id: Optional[int] = None
    tags: List[str] = []


FolderResponse.model_rebuild()
