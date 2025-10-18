from typing import Optional
from .base_model import BaseModel
from .fragments import MetricDataAdmin

class DescribeMetricAdmin(BaseModel):
    """@public"""
    metric: Optional['DescribeMetricAdminMetric']

class DescribeMetricAdminMetric(MetricDataAdmin):
    """@public"""
    pass
DescribeMetricAdmin.model_rebuild()