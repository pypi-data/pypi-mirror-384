from typing import List, Optional
from .base_model import BaseModel
from .fragments import ModelDataAdmin

class ListModels(BaseModel):
    """@public"""
    models: List['ListModelsModels']

class ListModelsModels(ModelDataAdmin):
    """@public"""
    backbone: Optional['ListModelsModelsBackbone']

class ListModelsModelsBackbone(ModelDataAdmin):
    """@public"""
    pass
ListModels.model_rebuild()
ListModelsModels.model_rebuild()