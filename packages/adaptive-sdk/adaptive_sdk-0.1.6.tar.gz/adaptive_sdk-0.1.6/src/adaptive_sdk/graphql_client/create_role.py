from typing import Any, List
from pydantic import Field
from .base_model import BaseModel

class CreateRole(BaseModel):
    """@public"""
    create_role: 'CreateRoleCreateRole' = Field(alias='createRole')

class CreateRoleCreateRole(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
    permissions: List[str]
CreateRole.model_rebuild()