from pydantic import Field
from .base_model import BaseModel

class UnlinkMetric(BaseModel):
    """@public"""
    unlink_metric: str = Field(alias='unlinkMetric')