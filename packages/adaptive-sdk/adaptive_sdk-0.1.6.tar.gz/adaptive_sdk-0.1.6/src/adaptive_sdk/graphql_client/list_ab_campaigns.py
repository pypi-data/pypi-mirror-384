from typing import List
from pydantic import Field
from .base_model import BaseModel
from .fragments import AbCampaignDetailData

class ListAbCampaigns(BaseModel):
    """@public"""
    ab_campaigns: List['ListAbCampaignsAbCampaigns'] = Field(alias='abCampaigns')

class ListAbCampaignsAbCampaigns(AbCampaignDetailData):
    """@public"""
    pass
ListAbCampaigns.model_rebuild()