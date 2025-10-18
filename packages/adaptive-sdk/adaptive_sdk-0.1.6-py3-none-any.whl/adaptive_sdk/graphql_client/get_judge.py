from .base_model import BaseModel
from .fragments import JudgeData

class GetJudge(BaseModel):
    """@public"""
    judge: 'GetJudgeJudge'

class GetJudgeJudge(JudgeData):
    """@public"""
    pass
GetJudge.model_rebuild()