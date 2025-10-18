from typing import Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import AbCampaignDetailData, AbCampaignReportData

class DescribeAbCampaign(BaseModel):
    """@public"""
    ab_campaign: Optional['DescribeAbCampaignAbCampaign'] = Field(alias='abCampaign')

class DescribeAbCampaignAbCampaign(AbCampaignDetailData):
    """@public"""
    report: 'DescribeAbCampaignAbCampaignReport'

class DescribeAbCampaignAbCampaignReport(AbCampaignReportData):
    """@public"""
    pass
DescribeAbCampaign.model_rebuild()
DescribeAbCampaignAbCampaign.model_rebuild()