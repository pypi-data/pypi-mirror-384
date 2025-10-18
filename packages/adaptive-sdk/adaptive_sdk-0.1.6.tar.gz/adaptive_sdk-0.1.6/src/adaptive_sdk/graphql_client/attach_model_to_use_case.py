from pydantic import Field
from .base_model import BaseModel
from .fragments import ModelServiceData

class AttachModelToUseCase(BaseModel):
    """@public"""
    attach_model: 'AttachModelToUseCaseAttachModel' = Field(alias='attachModel')

class AttachModelToUseCaseAttachModel(ModelServiceData):
    """@public"""
    pass
AttachModelToUseCase.model_rebuild()