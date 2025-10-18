from pydantic import Field
from .base_model import BaseModel
from .fragments import ModelServiceData

class UpdateModel(BaseModel):
    """@public"""
    update_model_service: 'UpdateModelUpdateModelService' = Field(alias='updateModelService')

class UpdateModelUpdateModelService(ModelServiceData):
    """@public"""
    pass
UpdateModel.model_rebuild()