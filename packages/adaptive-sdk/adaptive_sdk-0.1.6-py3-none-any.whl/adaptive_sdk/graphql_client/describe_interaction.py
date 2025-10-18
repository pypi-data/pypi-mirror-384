from typing import Optional
from .base_model import BaseModel
from .fragments import CompletionData

class DescribeInteraction(BaseModel):
    """@public"""
    completion: Optional['DescribeInteractionCompletion']

class DescribeInteractionCompletion(CompletionData):
    """@public"""
    pass
DescribeInteraction.model_rebuild()