from typing import Optional, List
from pydantic import BaseModel

class AuthControllerReadDto(BaseModel):
    org_id: Optional[str] = None
    bus_id: Optional[str] = None 
    app_id: Optional[str] = None 
    shared_resource_id: Optional[str] = None
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    role_id: Optional[str] = None
    tenant_id: Optional[str] = None
    permissions: Optional[List[str]] = None
    shared_resource_id: Optional[str] = None
    resource_id: Optional[str] = None

class AuthServiceReadDto(AuthControllerReadDto):
    pass
