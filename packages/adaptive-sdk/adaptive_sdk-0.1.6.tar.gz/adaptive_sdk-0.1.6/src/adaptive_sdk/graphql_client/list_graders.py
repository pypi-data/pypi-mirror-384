from typing import List
from .base_model import BaseModel
from .fragments import GraderData

class ListGraders(BaseModel):
    """@public"""
    graders: List['ListGradersGraders']

class ListGradersGraders(GraderData):
    """@public"""
    pass
ListGraders.model_rebuild()