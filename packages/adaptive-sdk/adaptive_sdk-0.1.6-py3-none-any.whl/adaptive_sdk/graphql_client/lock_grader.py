from pydantic import Field
from .base_model import BaseModel
from .fragments import GraderData

class LockGrader(BaseModel):
    """@public"""
    lock_grader: 'LockGraderLockGrader' = Field(alias='lockGrader')

class LockGraderLockGrader(GraderData):
    """@public"""
    pass
LockGrader.model_rebuild()