from pydantic import Field
from .base_model import BaseModel
from .fragments import UserData

class CreateUser(BaseModel):
    """@public"""
    create_user: 'CreateUserCreateUser' = Field(alias='createUser')

class CreateUserCreateUser(UserData):
    """@public"""
    pass
CreateUser.model_rebuild()