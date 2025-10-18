from typing import Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import ModelData

class AddModel(BaseModel):
    """@public"""
    add_model: 'AddModelAddModel' = Field(alias='addModel')

class AddModelAddModel(ModelData):
    """@public"""
    backbone: Optional['AddModelAddModelBackbone']

class AddModelAddModelBackbone(ModelData):
    """@public"""
    pass
AddModel.model_rebuild()
AddModelAddModel.model_rebuild()