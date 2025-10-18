from typing import Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import UseCaseData

class DescribeUseCase(BaseModel):
    """@public"""
    use_case: Optional['DescribeUseCaseUseCase'] = Field(alias='useCase')

class DescribeUseCaseUseCase(UseCaseData):
    """@public"""
    pass
DescribeUseCase.model_rebuild()