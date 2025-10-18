from pydantic import Field
from .base_model import BaseModel
from .fragments import JobData

class CancelJob(BaseModel):
    """@public"""
    cancel_job: 'CancelJobCancelJob' = Field(alias='cancelJob')

class CancelJobCancelJob(JobData):
    """@public"""
    pass
CancelJob.model_rebuild()