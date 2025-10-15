from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import date

class ResetpasswordRequest(BaseModel):
    username: str
    otp: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password:  Optional[str] = None
   
class LoginRequest(BaseModel):
    username: str
    password: str

class PersonModel(BaseModel):
    id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes  = True

class UserModel(PersonModel):
    id: Optional[UUID] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = []
    grants: Optional[List[str]] = []
    hashed_password: Optional[str] = None

    class Config:
        from_attributes  = True



class PageDefinitionModel(BaseModel):
    id: Optional[int] = None
    client_id: Optional[str] = None
    module: Optional[str] = None
    operations: Optional[list[str]] = []
    role: Optional[str] = None
    screen_id: Optional[str] = None
    load_type: Optional[str] = None


class DelegatedAccessRequest(BaseModel):
    requester_id: str   # waiter user_id
    page: str           # e.g., "orders"
    admin_username: str
    admin_password: str
