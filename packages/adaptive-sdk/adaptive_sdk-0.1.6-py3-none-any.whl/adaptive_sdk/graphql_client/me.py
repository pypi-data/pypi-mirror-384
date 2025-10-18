from typing import List, Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import UserData

class Me(BaseModel):
    """@public"""
    me: Optional['MeMe']

class MeMe(UserData):
    """@public"""
    api_keys: List['MeMeApiKeys'] = Field(alias='apiKeys')

class MeMeApiKeys(BaseModel):
    """@public"""
    key: str
    created_at: int = Field(alias='createdAt')
Me.model_rebuild()
MeMe.model_rebuild()