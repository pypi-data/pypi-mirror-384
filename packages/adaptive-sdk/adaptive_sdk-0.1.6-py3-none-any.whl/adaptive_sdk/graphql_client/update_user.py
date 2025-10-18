from typing import Any, List
from pydantic import Field
from .base_model import BaseModel
from .fragments import UserData

class UpdateUser(BaseModel):
    """@public"""
    set_team_member: 'UpdateUserSetTeamMember' = Field(alias='setTeamMember')

class UpdateUserSetTeamMember(BaseModel):
    """@public"""
    user: 'UpdateUserSetTeamMemberUser'
    team: 'UpdateUserSetTeamMemberTeam'
    role: 'UpdateUserSetTeamMemberRole'

class UpdateUserSetTeamMemberUser(UserData):
    """@public"""
    pass

class UpdateUserSetTeamMemberTeam(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')

class UpdateUserSetTeamMemberRole(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
    permissions: List[str]
UpdateUser.model_rebuild()
UpdateUserSetTeamMember.model_rebuild()