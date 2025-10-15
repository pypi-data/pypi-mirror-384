from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class Document(BaseModel):
    id: Optional[UUID] = None
    client_id: Optional[str] = None
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    realm: Optional[str] = None
    filetype: Optional[str] = None
    extension: Optional[str] = None
    size_kb: Optional[str] = None
    is_protected: Optional[bool] = None
    is_active: Optional[bool] = None
    uuid_name: Optional[str] = None
    path: Optional[str] = None
    storage_type: Optional[str] = None
    checksum_md5: Optional[str] = None
    created_by: Optional[str] = None
    last_read_by: Optional[str] = None
    created_date_time: Optional[datetime] = None
    last_read_date_time: Optional[datetime] = None
    deleted: Optional[bool] = None
    deleted_at: Optional[datetime] = None

    class Config:
        orm_mode = True
