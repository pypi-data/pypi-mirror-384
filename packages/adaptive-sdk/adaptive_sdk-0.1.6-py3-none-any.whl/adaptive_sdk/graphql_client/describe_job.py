from typing import Optional
from .base_model import BaseModel
from .fragments import JobData

class DescribeJob(BaseModel):
    """@public"""
    job: Optional['DescribeJobJob']

class DescribeJobJob(JobData):
    """@public"""
    pass
DescribeJob.model_rebuild()