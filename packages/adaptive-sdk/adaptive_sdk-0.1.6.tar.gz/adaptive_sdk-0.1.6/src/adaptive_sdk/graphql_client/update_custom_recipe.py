from pydantic import Field
from .base_model import BaseModel
from .fragments import CustomRecipeData

class UpdateCustomRecipe(BaseModel):
    """@public"""
    update_custom_recipe: 'UpdateCustomRecipeUpdateCustomRecipe' = Field(alias='updateCustomRecipe')

class UpdateCustomRecipeUpdateCustomRecipe(CustomRecipeData):
    """@public"""
    pass
UpdateCustomRecipe.model_rebuild()