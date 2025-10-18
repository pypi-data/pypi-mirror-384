from typing import List
from .base_model import BaseModel
from .fragments import DatasetData

class ListDatasets(BaseModel):
    """@public"""
    datasets: List['ListDatasetsDatasets']

class ListDatasetsDatasets(DatasetData):
    """@public"""
    pass
ListDatasets.model_rebuild()