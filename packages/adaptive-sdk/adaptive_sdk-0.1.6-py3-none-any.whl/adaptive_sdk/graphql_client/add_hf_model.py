from pydantic import Field
from .base_model import BaseModel
from .fragments import JobData

class AddHFModel(BaseModel):
    """@public"""
    import_hf_model: 'AddHFModelImportHfModel' = Field(alias='importHfModel')

class AddHFModelImportHfModel(JobData):
    """@public"""
    pass
AddHFModel.model_rebuild()