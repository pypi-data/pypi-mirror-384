from typing import Any, List
from pydantic import Field
from .base_model import BaseModel

class ListTeams(BaseModel):
    """@public"""
    teams: List['ListTeamsTeams']

class ListTeamsTeams(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
ListTeams.model_rebuild()