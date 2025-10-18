from typing import Optional
from .base_model import BaseModel
from .fragments import MetricData

class DescribeMetric(BaseModel):
    """@public"""
    metric: Optional['DescribeMetricMetric']

class DescribeMetricMetric(MetricData):
    """@public"""
    pass
DescribeMetric.model_rebuild()