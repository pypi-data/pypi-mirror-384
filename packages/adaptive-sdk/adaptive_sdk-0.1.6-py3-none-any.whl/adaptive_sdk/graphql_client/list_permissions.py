from typing import List
from .base_model import BaseModel

class ListPermissions(BaseModel):
    """@public"""
    permissions: List[str]