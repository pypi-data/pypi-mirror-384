from pydantic import Field
from .base_model import BaseModel
from .fragments import DatasetData

class LoadDataset(BaseModel):
    """@public"""
    create_dataset: 'LoadDatasetCreateDataset' = Field(alias='createDataset')

class LoadDatasetCreateDataset(DatasetData):
    """@public"""
    pass
LoadDataset.model_rebuild()