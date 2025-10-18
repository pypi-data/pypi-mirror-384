from typing import Any
from pydantic import Field
from .base_model import BaseModel

class CreateTeam(BaseModel):
    """@public"""
    create_team: 'CreateTeamCreateTeam' = Field(alias='createTeam')

class CreateTeamCreateTeam(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
CreateTeam.model_rebuild()