from typing import List, Optional
from pydantic import Field
from .base_model import BaseModel
from .enums import CompletionGroupBy
from .fragments import CompletionData, MetricData

class ListGroupedInteractions(BaseModel):
    """@public"""
    completions_grouped: 'ListGroupedInteractionsCompletionsGrouped' = Field(alias='completionsGrouped')

class ListGroupedInteractionsCompletionsGrouped(BaseModel):
    """@public"""
    total_count: int = Field(alias='totalCount')
    group_by: CompletionGroupBy = Field(alias='groupBy')
    page_info: 'ListGroupedInteractionsCompletionsGroupedPageInfo' = Field(alias='pageInfo')
    nodes: List['ListGroupedInteractionsCompletionsGroupedNodes']

class ListGroupedInteractionsCompletionsGroupedPageInfo(BaseModel):
    """@public"""
    has_next_page: bool = Field(alias='hasNextPage')
    end_cursor: Optional[str] = Field(alias='endCursor')

class ListGroupedInteractionsCompletionsGroupedNodes(BaseModel):
    """@public"""
    key: Optional[str]
    count: int
    direct_feedbacks_stats: List['ListGroupedInteractionsCompletionsGroupedNodesDirectFeedbacksStats'] = Field(alias='directFeedbacksStats')
    completions: 'ListGroupedInteractionsCompletionsGroupedNodesCompletions'

class ListGroupedInteractionsCompletionsGroupedNodesDirectFeedbacksStats(BaseModel):
    """@public"""
    metric: 'ListGroupedInteractionsCompletionsGroupedNodesDirectFeedbacksStatsMetric'
    feedbacks: int
    average: Optional[float]
    max: Optional[float]
    min: Optional[float]
    stddev: Optional[float]
    sum: Optional[float]

class ListGroupedInteractionsCompletionsGroupedNodesDirectFeedbacksStatsMetric(MetricData):
    """@public"""
    pass

class ListGroupedInteractionsCompletionsGroupedNodesCompletions(BaseModel):
    """@public"""
    nodes: List['ListGroupedInteractionsCompletionsGroupedNodesCompletionsNodes']

class ListGroupedInteractionsCompletionsGroupedNodesCompletionsNodes(CompletionData):
    """@public"""
    pass
ListGroupedInteractions.model_rebuild()
ListGroupedInteractionsCompletionsGrouped.model_rebuild()
ListGroupedInteractionsCompletionsGroupedNodes.model_rebuild()
ListGroupedInteractionsCompletionsGroupedNodesDirectFeedbacksStats.model_rebuild()
ListGroupedInteractionsCompletionsGroupedNodesCompletions.model_rebuild()