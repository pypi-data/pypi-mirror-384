from typing import Any, List
from pydantic import Field
from .base_model import BaseModel

class ListRoles(BaseModel):
    """@public"""
    roles: List['ListRolesRoles']

class ListRolesRoles(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
    permissions: List[str]
ListRoles.model_rebuild()