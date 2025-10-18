from pydantic import Field
from .base_model import BaseModel
from .fragments import CustomRecipeData

class CreateCustomRecipe(BaseModel):
    """@public"""
    create_custom_recipe: 'CreateCustomRecipeCreateCustomRecipe' = Field(alias='createCustomRecipe')

class CreateCustomRecipeCreateCustomRecipe(CustomRecipeData):
    """@public"""
    pass
CreateCustomRecipe.model_rebuild()