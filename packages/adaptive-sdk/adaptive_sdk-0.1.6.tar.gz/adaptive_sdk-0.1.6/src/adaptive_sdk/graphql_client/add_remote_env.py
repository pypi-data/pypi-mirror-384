from pydantic import Field
from .base_model import BaseModel
from .fragments import RemoteEnvData

class AddRemoteEnv(BaseModel):
    """@public"""
    add_remote_env: 'AddRemoteEnvAddRemoteEnv' = Field(alias='addRemoteEnv')

class AddRemoteEnvAddRemoteEnv(RemoteEnvData):
    """@public"""
    pass
AddRemoteEnv.model_rebuild()