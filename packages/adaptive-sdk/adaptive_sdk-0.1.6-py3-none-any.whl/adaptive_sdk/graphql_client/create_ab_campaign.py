from pydantic import Field
from .base_model import BaseModel
from .fragments import AbCampaignCreateData

class CreateAbCampaign(BaseModel):
    """@public"""
    create_ab_campaign: 'CreateAbCampaignCreateAbCampaign' = Field(alias='createAbCampaign')

class CreateAbCampaignCreateAbCampaign(AbCampaignCreateData):
    """@public"""
    pass
CreateAbCampaign.model_rebuild()