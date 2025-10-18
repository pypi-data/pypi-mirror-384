from typing import List
from pydantic import Field
from .base_model import BaseModel
from .fragments import RemoteEnvData

class ListRemoteEnvs(BaseModel):
    """@public"""
    remote_envs: List['ListRemoteEnvsRemoteEnvs'] = Field(alias='remoteEnvs')

class ListRemoteEnvsRemoteEnvs(RemoteEnvData):
    """@public"""
    pass
ListRemoteEnvs.model_rebuild()