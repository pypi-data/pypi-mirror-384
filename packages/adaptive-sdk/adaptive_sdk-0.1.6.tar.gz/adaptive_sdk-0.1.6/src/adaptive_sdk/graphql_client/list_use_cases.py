from typing import List
from pydantic import Field
from .base_model import BaseModel
from .fragments import UseCaseData

class ListUseCases(BaseModel):
    """@public"""
    use_cases: List['ListUseCasesUseCases'] = Field(alias='useCases')

class ListUseCasesUseCases(UseCaseData):
    """@public"""
    pass
ListUseCases.model_rebuild()