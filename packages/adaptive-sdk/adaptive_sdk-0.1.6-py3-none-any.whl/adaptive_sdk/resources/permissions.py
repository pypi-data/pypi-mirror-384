from __future__ import annotations
from typing import TYPE_CHECKING, List

from adaptive_sdk.graphql_client import ListPermissions

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Permissions(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to list permissions.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self) -> List[str]:
        return self._gql_client.list_permissions().permissions


class AsyncPermissions(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to list permissions.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self) -> List[str]:
        return (await self._gql_client.list_permissions()).permissions
