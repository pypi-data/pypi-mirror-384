from pydantic import Field
from .base_model import BaseModel
from .fragments import UseCaseData

class ShareUseCase(BaseModel):
    """@public"""
    share_use_case: 'ShareUseCaseShareUseCase' = Field(alias='shareUseCase')

class ShareUseCaseShareUseCase(UseCaseData):
    """@public"""
    pass
ShareUseCase.model_rebuild()