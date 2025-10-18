from typing import List
from pydantic import Field
from .base_model import BaseModel
from .fragments import HarmonyGroupData

class ListHarmonyGroups(BaseModel):
    """@public"""
    harmony_groups: List['ListHarmonyGroupsHarmonyGroups'] = Field(alias='harmonyGroups')

class ListHarmonyGroupsHarmonyGroups(HarmonyGroupData):
    """@public"""
    pass
ListHarmonyGroups.model_rebuild()