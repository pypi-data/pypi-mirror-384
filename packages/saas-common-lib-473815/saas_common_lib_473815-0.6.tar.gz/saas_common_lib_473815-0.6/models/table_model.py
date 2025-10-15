from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class Table(BaseModel):
    id:            Optional[int] = None
    client_id:     Optional[str] = None
    name:          Optional[str] = None
    table_type:    Optional[str]
    slug:          Optional[str] = None
    qr_code_url:   Optional[str] = None
    description:   Optional[str] = None
    status:        Optional[str] = "Vacant"
    section:       Optional[str] = None
    location_zone: Optional[str] = None
    sort_order:    Optional[int] = None
    is_active:     Optional[bool] = True
    created_by:    Optional[str] = None
    updated_by:    Optional[str] = None
    created_at:    Optional[datetime] = None
    updated_at:    Optional[datetime] = None

    class Config:
        orm_mode=True
        extend_existing=True
        from_attribute = True
