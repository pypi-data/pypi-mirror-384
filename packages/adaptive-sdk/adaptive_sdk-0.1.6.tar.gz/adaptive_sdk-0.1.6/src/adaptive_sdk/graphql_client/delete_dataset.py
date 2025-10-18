from pydantic import Field
from .base_model import BaseModel

class DeleteDataset(BaseModel):
    """@public"""
    delete_dataset: bool = Field(alias='deleteDataset')