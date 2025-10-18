from pydantic import Field
from .base_model import BaseModel
from .fragments import GraderData

class UpdateGrader(BaseModel):
    """@public"""
    update_grader: 'UpdateGraderUpdateGrader' = Field(alias='updateGrader')

class UpdateGraderUpdateGrader(GraderData):
    """@public"""
    pass
UpdateGrader.model_rebuild()