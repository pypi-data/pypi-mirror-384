from typing import Optional
from .base_model import BaseModel
from .fragments import ModelDataAdmin

class DescribeModelAdmin(BaseModel):
    """@public"""
    model: Optional['DescribeModelAdminModel']

class DescribeModelAdminModel(ModelDataAdmin):
    """@public"""
    backbone: Optional['DescribeModelAdminModelBackbone']

class DescribeModelAdminModelBackbone(ModelDataAdmin):
    """@public"""
    pass
DescribeModelAdmin.model_rebuild()
DescribeModelAdminModel.model_rebuild()