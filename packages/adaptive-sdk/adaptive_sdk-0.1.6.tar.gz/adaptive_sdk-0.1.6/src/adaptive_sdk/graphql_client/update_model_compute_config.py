from pydantic import Field
from .base_model import BaseModel
from .fragments import ModelData

class UpdateModelComputeConfig(BaseModel):
    """@public"""
    update_model_compute_config: 'UpdateModelComputeConfigUpdateModelComputeConfig' = Field(alias='updateModelComputeConfig')

class UpdateModelComputeConfigUpdateModelComputeConfig(ModelData):
    """@public"""
    pass
UpdateModelComputeConfig.model_rebuild()