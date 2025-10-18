from typing import List
from .base_model import BaseModel
from .fragments import JudgeData

class ListJudges(BaseModel):
    """@public"""
    judges: List['ListJudgesJudges']

class ListJudgesJudges(JudgeData):
    """@public"""
    pass
ListJudges.model_rebuild()