from typing import List
from pydantic import Field
from .base_model import BaseModel
from .fragments import JudgeData

class ListJudgeVersions(BaseModel):
    """@public"""
    judge_versions: List['ListJudgeVersionsJudgeVersions'] = Field(alias='judgeVersions')

class ListJudgeVersionsJudgeVersions(JudgeData):
    """@public"""
    pass
ListJudgeVersions.model_rebuild()