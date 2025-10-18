from pydantic import Field
from .base_model import BaseModel
from .fragments import JobData

class CreateJob(BaseModel):
    """@public"""
    create_job: 'CreateJobCreateJob' = Field(alias='createJob')

class CreateJobCreateJob(JobData):
    """@public"""
    pass
CreateJob.model_rebuild()