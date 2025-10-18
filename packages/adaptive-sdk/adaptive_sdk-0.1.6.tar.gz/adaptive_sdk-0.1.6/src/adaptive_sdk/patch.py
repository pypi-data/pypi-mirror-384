from .graphql_client import BaseModel
from pprint import pformat


def pretty_pydantic_print(self):
    return pformat(self.model_dump(), indent=2)


BaseModel.__str__ = pretty_pydantic_print  # type: ignore[method-assign]
