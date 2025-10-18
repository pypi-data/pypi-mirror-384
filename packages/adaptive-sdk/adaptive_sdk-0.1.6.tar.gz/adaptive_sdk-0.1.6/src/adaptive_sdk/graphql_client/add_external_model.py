from pydantic import Field
from .base_model import BaseModel
from .fragments import ModelData

class AddExternalModel(BaseModel):
    """@public"""
    add_external_model: 'AddExternalModelAddExternalModel' = Field(alias='addExternalModel')

class AddExternalModelAddExternalModel(ModelData):
    """@public"""
    pass
AddExternalModel.model_rebuild()