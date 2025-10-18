from pydantic import Field
from .base_model import BaseModel
from .fragments import UserData

class DeleteUser(BaseModel):
    """@public"""
    delete_user: 'DeleteUserDeleteUser' = Field(alias='deleteUser')

class DeleteUserDeleteUser(UserData):
    """@public"""
    pass
DeleteUser.model_rebuild()