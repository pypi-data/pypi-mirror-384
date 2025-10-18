from typing import Optional
from .base_model import BaseModel
from .fragments import DatasetData

class DescribeDataset(BaseModel):
    """@public"""
    dataset: Optional['DescribeDatasetDataset']

class DescribeDatasetDataset(DatasetData):
    """@public"""
    pass
DescribeDataset.model_rebuild()