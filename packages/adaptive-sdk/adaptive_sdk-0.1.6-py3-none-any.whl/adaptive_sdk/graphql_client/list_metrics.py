from typing import List
from .base_model import BaseModel
from .fragments import MetricDataAdmin

class ListMetrics(BaseModel):
    """@public"""
    metrics: List['ListMetricsMetrics']

class ListMetricsMetrics(MetricDataAdmin):
    """@public"""
    pass
ListMetrics.model_rebuild()