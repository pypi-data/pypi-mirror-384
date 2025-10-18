from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adaptive_sdk.base_client import BaseAsyncClient, BaseSyncClient, UseCaseClient


class SyncAPIResource:
    def __init__(self, client: BaseSyncClient) -> None:
        self._client = client
        self._rest_client = client._rest_client
        self._gql_client = client._gql_client


class AsyncAPIResource:
    def __init__(self, client: BaseAsyncClient) -> None:
        self._client = client
        self._rest_client = client._rest_client
        self._gql_client = client._gql_client


class UseCaseResource:
    def __init__(self, client: UseCaseClient) -> None:
        self._client = client

    def use_case_key(self, use_case: str | None) -> str:
        target_use_case = use_case or self._client.default_use_case
        if target_use_case is None:
            raise ValueError(
                """This method is use case-specific. Either set a default use case for the client with `client.set_default_use_case`, \
or explicitly pass `use_case` as an input parameter."""
            )
        elif not bool(target_use_case.strip()):
            raise ValueError("use_case must be a non-empty string")

        return target_use_case

    def optional_use_case_key(self, use_case: str | None) -> str | None:
        if use_case:
            return use_case
        elif self._client.default_use_case:
            return self._client.default_use_case
        else:
            return None
