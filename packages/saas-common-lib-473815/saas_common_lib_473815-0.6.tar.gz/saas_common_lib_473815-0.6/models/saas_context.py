from typing import List, Optional
from pydantic import BaseModel
import contextvars
from models.user_model import PageDefinitionModel

saasContext = contextvars.ContextVar("saasContext", default={})


class SaasContext(BaseModel):
    client_id: Optional[str] = None
    roles: List[str] = []
    grants: List[str] = []
    user_id: Optional[str] = None
    module: Optional[str] = None
    operation: Optional[str] = None
    screen_id: Optional[str] = None

    def __init__(self, client_id: Optional[str] = None, module: Optional[str] = None, operation: Optional[str] = None,
                 user_id: Optional[str] = None, roles: List[str] = None, grants: List[str] = None, screen_id: Optional[str] = None):
        roles = roles or []
        grants = grants or []
        super().__init__(client_id=client_id, module=module, operation=operation, user_id=user_id, roles=roles, grants=grants, screen_id=screen_id)