from typing import Optional
from .base_model import BaseModel
from .fragments import ModelData

class DescribeModel(BaseModel):
    """@public"""
    model: Optional['DescribeModelModel']

class DescribeModelModel(ModelData):
    """@public"""
    backbone: Optional['DescribeModelModelBackbone']

class DescribeModelModelBackbone(ModelData):
    """@public"""
    pass
DescribeModel.model_rebuild()
DescribeModelModel.model_rebuild()