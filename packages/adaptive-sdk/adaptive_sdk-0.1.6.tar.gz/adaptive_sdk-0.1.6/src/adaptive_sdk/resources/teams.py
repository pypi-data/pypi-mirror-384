from __future__ import annotations
from typing import TYPE_CHECKING, List

from adaptive_sdk.graphql_client import CreateTeamCreateTeam, ListTeamsTeams, TeamCreate

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Teams(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to manage teams.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self) -> List[ListTeamsTeams]:
        return self._gql_client.list_teams().teams

    def create(self, key: str, name: str | None = None) -> CreateTeamCreateTeam:
        input = TeamCreate(key=key, name=name or key)
        return self._gql_client.create_team(input).create_team


class AsyncTeams(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to manage teams.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self) -> List[ListTeamsTeams]:
        return (await self._gql_client.list_teams()).teams

    async def create(self, key: str, name: str | None = None) -> CreateTeamCreateTeam:
        input = TeamCreate(key=key, name=name or key)
        return (await self._gql_client.create_team(input)).create_team
