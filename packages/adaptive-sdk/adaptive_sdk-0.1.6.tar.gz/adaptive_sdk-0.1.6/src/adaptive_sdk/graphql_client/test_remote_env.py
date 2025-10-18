from typing import Literal, Union
from pydantic import Field
from .base_model import BaseModel

class TestRemoteEnv(BaseModel):
    """@public"""
    test_remote_env: Union['TestRemoteEnvTestRemoteEnvRemoteEnvTestOffline', 'TestRemoteEnvTestRemoteEnvRemoteEnvTestOnline'] = Field(alias='testRemoteEnv', discriminator='typename__')

class TestRemoteEnvTestRemoteEnvRemoteEnvTestOffline(BaseModel):
    """@public"""
    typename__: Literal['RemoteEnvTestOffline'] = Field(alias='__typename')
    error: str

class TestRemoteEnvTestRemoteEnvRemoteEnvTestOnline(BaseModel):
    """@public"""
    typename__: Literal['RemoteEnvTestOnline'] = Field(alias='__typename')
    name: str
    version: str
    description: str
TestRemoteEnv.model_rebuild()