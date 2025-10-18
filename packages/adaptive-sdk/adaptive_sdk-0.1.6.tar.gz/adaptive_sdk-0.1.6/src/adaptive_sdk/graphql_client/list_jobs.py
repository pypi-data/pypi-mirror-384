from typing import List, Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import JobData

class ListJobs(BaseModel):
    """@public"""
    jobs: 'ListJobsJobs'

class ListJobsJobs(BaseModel):
    """@public"""
    total_count: int = Field(alias='totalCount')
    page_info: 'ListJobsJobsPageInfo' = Field(alias='pageInfo')
    nodes: List['ListJobsJobsNodes']

class ListJobsJobsPageInfo(BaseModel):
    """@public"""
    has_next_page: bool = Field(alias='hasNextPage')
    has_previous_page: bool = Field(alias='hasPreviousPage')
    start_cursor: Optional[str] = Field(alias='startCursor')
    end_cursor: Optional[str] = Field(alias='endCursor')

class ListJobsJobsNodes(JobData):
    """@public"""
    pass
ListJobs.model_rebuild()
ListJobsJobs.model_rebuild()