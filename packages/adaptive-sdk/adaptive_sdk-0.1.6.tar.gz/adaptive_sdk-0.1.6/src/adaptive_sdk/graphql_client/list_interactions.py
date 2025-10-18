from typing import List, Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import CompletionData

class ListInteractions(BaseModel):
    """@public"""
    completions: 'ListInteractionsCompletions'

class ListInteractionsCompletions(BaseModel):
    """@public"""
    total_count: int = Field(alias='totalCount')
    page_info: 'ListInteractionsCompletionsPageInfo' = Field(alias='pageInfo')
    nodes: List['ListInteractionsCompletionsNodes']

class ListInteractionsCompletionsPageInfo(BaseModel):
    """@public"""
    has_next_page: bool = Field(alias='hasNextPage')
    end_cursor: Optional[str] = Field(alias='endCursor')

class ListInteractionsCompletionsNodes(CompletionData):
    """@public"""
    pass
ListInteractions.model_rebuild()
ListInteractionsCompletions.model_rebuild()