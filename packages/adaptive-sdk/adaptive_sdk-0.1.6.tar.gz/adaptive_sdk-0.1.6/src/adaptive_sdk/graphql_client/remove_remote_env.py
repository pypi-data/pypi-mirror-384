from pydantic import Field
from .base_model import BaseModel

class RemoveRemoteEnv(BaseModel):
    """@public"""
    remove_remote_env: str = Field(alias='removeRemoteEnv')