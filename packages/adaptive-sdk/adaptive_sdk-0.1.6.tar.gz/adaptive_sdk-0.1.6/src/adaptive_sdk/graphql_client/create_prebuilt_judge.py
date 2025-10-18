from pydantic import Field
from .base_model import BaseModel
from .fragments import JudgeData

class CreatePrebuiltJudge(BaseModel):
    """@public"""
    create_prebuilt_judge: 'CreatePrebuiltJudgeCreatePrebuiltJudge' = Field(alias='createPrebuiltJudge')

class CreatePrebuiltJudgeCreatePrebuiltJudge(JudgeData):
    """@public"""
    pass
CreatePrebuiltJudge.model_rebuild()