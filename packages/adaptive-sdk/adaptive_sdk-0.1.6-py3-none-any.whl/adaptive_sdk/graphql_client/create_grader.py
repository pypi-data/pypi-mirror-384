from pydantic import Field
from .base_model import BaseModel
from .fragments import GraderData

class CreateGrader(BaseModel):
    """@public"""
    create_grader: 'CreateGraderCreateGrader' = Field(alias='createGrader')

class CreateGraderCreateGrader(GraderData):
    """@public"""
    pass
CreateGrader.model_rebuild()