from pydantic import Field
from .base_model import BaseModel
from .fragments import UserData

class RemoveTeamMember(BaseModel):
    """@public"""
    remove_team_member: 'RemoveTeamMemberRemoveTeamMember' = Field(alias='removeTeamMember')

class RemoveTeamMemberRemoveTeamMember(UserData):
    """@public"""
    pass
RemoveTeamMember.model_rebuild()