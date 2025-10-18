from pydantic import Field
from .base_model import BaseModel
from .fragments import JudgeData

class UpdateJudge(BaseModel):
    """@public"""
    update_judge: 'UpdateJudgeUpdateJudge' = Field(alias='updateJudge')

class UpdateJudgeUpdateJudge(JudgeData):
    """@public"""
    pass
UpdateJudge.model_rebuild()