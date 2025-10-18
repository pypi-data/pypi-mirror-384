# type: ignore

from __future__ import annotations
from typing import TYPE_CHECKING

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class ComputePools(SyncAPIResource, UseCaseResource):
    """
    Resource to interact with compute pools.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self):
        return self._gql_client.list_compute_pools()


class AsyncComputePools(AsyncAPIResource, UseCaseResource):
    """
    Resource to interact with compute pools.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self):
        return await self._gql_client.list_compute_pools()
