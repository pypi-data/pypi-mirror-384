from typing import Optional
from pydantic import Field
from .base_model import BaseModel

class DeleteJudge(BaseModel):
    """@public"""
    delete_judge: 'DeleteJudgeDeleteJudge' = Field(alias='deleteJudge')

class DeleteJudgeDeleteJudge(BaseModel):
    """@public"""
    success: bool
    details: Optional[str]
DeleteJudge.model_rebuild()