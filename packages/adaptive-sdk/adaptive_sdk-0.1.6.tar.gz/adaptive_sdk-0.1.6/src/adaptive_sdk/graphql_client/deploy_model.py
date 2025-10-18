from pydantic import Field
from .base_model import BaseModel

class DeployModel(BaseModel):
    """@public"""
    deploy_model: str = Field(alias='deployModel')