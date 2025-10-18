from pydantic import Field
from .base_model import BaseModel

class TerminateModel(BaseModel):
    """@public"""
    terminate_model: str = Field(alias='terminateModel')