from typing import List
from .base_model import BaseModel
from .fragments import UserData

class ListUsers(BaseModel):
    """@public"""
    users: List['ListUsersUsers']

class ListUsersUsers(UserData):
    """@public"""
    pass
ListUsers.model_rebuild()