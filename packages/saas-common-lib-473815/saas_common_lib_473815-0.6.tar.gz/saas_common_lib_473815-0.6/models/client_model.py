from pydantic import BaseModel
from typing import Optional


class ClientModel(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    realm: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    logo: Optional[str] = None

