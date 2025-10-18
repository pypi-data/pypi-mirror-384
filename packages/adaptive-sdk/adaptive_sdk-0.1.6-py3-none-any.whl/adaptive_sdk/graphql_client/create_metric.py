from pydantic import Field
from .base_model import BaseModel
from .fragments import MetricData

class CreateMetric(BaseModel):
    """@public"""
    create_metric: 'CreateMetricCreateMetric' = Field(alias='createMetric')

class CreateMetricCreateMetric(MetricData):
    """@public"""
    pass
CreateMetric.model_rebuild()