from pydantic import Field
from .base_model import BaseModel

class CancelABCampaign(BaseModel):
    """@public"""
    cancel_ab_campaign: str = Field(alias='cancelAbCampaign')