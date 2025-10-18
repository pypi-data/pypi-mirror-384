from pydantic import Field
from .base_model import BaseModel
from .fragments import MetricWithContextData

class LinkMetric(BaseModel):
    """@public"""
    link_metric: 'LinkMetricLinkMetric' = Field(alias='linkMetric')

class LinkMetricLinkMetric(MetricWithContextData):
    """@public"""
    pass
LinkMetric.model_rebuild()