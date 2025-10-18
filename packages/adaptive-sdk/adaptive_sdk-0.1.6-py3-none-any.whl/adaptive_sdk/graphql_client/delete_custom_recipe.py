from pydantic import Field
from .base_model import BaseModel

class DeleteCustomRecipe(BaseModel):
    """@public"""
    delete_custom_recipe: bool = Field(alias='deleteCustomRecipe')