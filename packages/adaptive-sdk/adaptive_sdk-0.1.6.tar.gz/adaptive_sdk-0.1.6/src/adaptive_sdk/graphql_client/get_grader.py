from .base_model import BaseModel
from .fragments import GraderData

class GetGrader(BaseModel):
    """@public"""
    grader: 'GetGraderGrader'

class GetGraderGrader(GraderData):
    """@public"""
    pass
GetGrader.model_rebuild()