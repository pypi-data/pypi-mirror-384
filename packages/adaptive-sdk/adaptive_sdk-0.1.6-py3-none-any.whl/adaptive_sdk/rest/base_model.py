from uuid import UUID
from pydantic import BaseModel as PydanticBaseModel, ConfigDict

class BaseModel(PydanticBaseModel):
    """@public"""
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True, arbitrary_types_allowed=True, protected_namespaces=())

    def model_dump(self, *args, **kwargs) -> dict:
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
        return data