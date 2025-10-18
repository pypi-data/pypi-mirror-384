import httpx
from typing import Callable
from pydantic import BaseModel
from .graphql_client.exceptions import GraphQLClientGraphQLMultiError


class EntityNotFoundDescriptor(BaseModel):
    entity: str
    error_message: str
    code_suggestions: list[str]

    def __post_init__(self):
        if self.error_message.count("{}") != len(self.code_suggestions):
            raise ValueError("# of code suggestions must match # of placeholders in error message template")


class AdaptiveEntityNotFoundError(Exception):
    def __init__(self, original_error: str):
        self.entity_descriptors = [
            EntityNotFoundDescriptor(
                entity="use_case",
                error_message="Use case key does not exist. You can create it with `{}`",
                code_suggestions=["client.use_cases.create"],
            ),
            EntityNotFoundDescriptor(
                entity="metric",
                error_message="Feedback key does not exist, or is not linked to the target use case. You can create it with `{}` or link it with `{}`",
                code_suggestions=[
                    "client.feedback.register_key",
                    "client.feedback.link",
                ],
            ),
            EntityNotFoundDescriptor(
                entity="model",
                error_message="Model key does not exist, or is not attached to the target use case. You can attach it with `{}`",
                code_suggestions=["client.models.attach"],
            ),
            EntityNotFoundDescriptor(entity="user", error_message="User does not exist.", code_suggestions=[]),
        ]

        new_error_message = None
        for descriptor in self.entity_descriptors:
            if descriptor.entity in original_error.lower():
                new_error_message = descriptor.error_message.format(*descriptor.code_suggestions)
                break

        super().__init__(new_error_message or original_error)


def adaptive_error_message_triage(error_message: str) -> Callable | None:
    if "EntityNotFound:" in error_message:
        return AdaptiveEntityNotFoundError
    else:
        return None


def graphql_multi_error_handler(fn: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except GraphQLClientGraphQLMultiError as e:
            error_message = str(e.errors[0])
            exception_type = adaptive_error_message_triage(error_message)
            if exception_type is not None:
                raise exception_type(error_message)
            else:
                raise

    return wrapper


def rest_error_handler(response: httpx.Response):
    if response.is_client_error:
        try:
            response_json = response.json()
            error_message = response_json.get("error", f"Unknown error: {response.text}")
            exception_type = adaptive_error_message_triage(error_message)
            if exception_type is not None:
                raise exception_type(error_message)
            else:
                raise Exception(f"Client error {response.status_code}: {error_message}")
        except Exception:
            # Handle any exception when processing the response
            raise Exception(f"Client error {response.status_code}: {response.text}")
    else:
        response.raise_for_status()
