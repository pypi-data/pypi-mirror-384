from typing import List
from pydantic import Field
from .base_model import BaseModel
from .fragments import CustomRecipeData

class ListCustomRecipes(BaseModel):
    """@public"""
    custom_recipes: List['ListCustomRecipesCustomRecipes'] = Field(alias='customRecipes')

class ListCustomRecipesCustomRecipes(CustomRecipeData):
    """@public"""
    pass
ListCustomRecipes.model_rebuild()