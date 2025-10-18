from pydantic import Field
from .base_model import BaseModel
from .fragments import JudgeData

class CreateJudge(BaseModel):
    """@public"""
    create_judge: 'CreateJudgeCreateJudge' = Field(alias='createJudge')

class CreateJudgeCreateJudge(JudgeData):
    """@public"""
    pass
CreateJudge.model_rebuild()