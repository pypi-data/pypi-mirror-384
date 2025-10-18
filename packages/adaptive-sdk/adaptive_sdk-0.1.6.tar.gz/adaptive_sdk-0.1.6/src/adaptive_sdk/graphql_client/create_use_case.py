from pydantic import Field
from .base_model import BaseModel
from .fragments import UseCaseData

class CreateUseCase(BaseModel):
    """@public"""
    create_use_case: 'CreateUseCaseCreateUseCase' = Field(alias='createUseCase')

class CreateUseCaseCreateUseCase(UseCaseData):
    """@public"""
    pass
CreateUseCase.model_rebuild()