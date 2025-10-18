from typing import Optional
from pydantic import Field
from .base_model import BaseModel

class DeleteGrader(BaseModel):
    """@public"""
    delete_grader: 'DeleteGraderDeleteGrader' = Field(alias='deleteGrader')

class DeleteGraderDeleteGrader(BaseModel):
    """@public"""
    success: bool
    details: Optional[str]
DeleteGrader.model_rebuild()