from __future__ import annotations
from uuid import UUID
from typing import overload

from adaptive_sdk import input_types
from .rest import rest_types


@overload
def convert_optional_UUID(input_param: str | UUID) -> UUID: ...


@overload
def convert_optional_UUID(input_param: str | UUID | None) -> UUID | None: ...


def convert_optional_UUID(input_param: str | UUID | None) -> UUID | None:
    if not input_param:
        return None
    if isinstance(input_param, UUID):
        return input_param
    try:
        return UUID(input_param)
    except ValueError as e:
        raise e


def validate_comparison_completion(
    completion: str | UUID | input_types.ComparisonCompletion,
) -> UUID | rest_types.CompletionIdOrText1:

    if isinstance(completion, dict):
        return rest_types.CompletionIdOrText1(
            text=completion["text"], model=completion["model"]
        )
    else:
        return convert_optional_UUID(completion)


def get_full_model_path(use_case_key: str, model_key: str | None):
    return f"{use_case_key}{'/' + model_key if model_key is not None else ''}"
