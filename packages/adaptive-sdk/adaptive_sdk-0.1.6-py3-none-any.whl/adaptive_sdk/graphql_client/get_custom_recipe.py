from typing import Optional
from pydantic import Field
from .base_model import BaseModel
from .fragments import CustomRecipeData

class GetCustomRecipe(BaseModel):
    """@public"""
    custom_recipe: Optional['GetCustomRecipeCustomRecipe'] = Field(alias='customRecipe')

class GetCustomRecipeCustomRecipe(CustomRecipeData):
    """@public"""
    pass
GetCustomRecipe.model_rebuild()