from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from adaptive_sdk.graphql_client import (
    UserData,
    TeamMemberSet,
    UpdateUserSetTeamMember,
    TeamMemberRemove,
    UserCreate,
    UserCreateTeamWithRole,
)

from .base_resource import SyncAPIResource, AsyncAPIResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Users(SyncAPIResource):  # type: ignore[misc]
    """
    Resource to manage users and permissions.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)

    def me(self) -> UserData | None:
        """
        Get details of current user.
        """
        return self._gql_client.me().me

    def list(self) -> Sequence[UserData]:
        """
        List all users registered to Adaptive deployment.
        """
        return self._gql_client.list_users().users

    def create(
        self, email: str, name: str, teams_with_role: Sequence[tuple[str, str]]
    ) -> UserData:
        """
        Create a user and with preset teams and role
        """
        return self._gql_client.create_user(
            input=UserCreate(
                email=email,
                name=name,
                teams=[
                    UserCreateTeamWithRole(team=team, role=role)
                    for (team, role) in teams_with_role
                ],
            )
        ).create_user

    def add_to_team(self, email: str, team: str, role: str) -> UpdateUserSetTeamMember:
        """
        Update team and role for user.

        Args:
            email: User email.
            team: Key of team to which user will be added to.
            role: Assigned role

        """
        input = TeamMemberSet(user=email, team=team, role=role)
        return self._gql_client.update_user(input).set_team_member

    def remove_from_team(self, email: str, team: str) -> UserData:
        """
        Remove user from team.

        Args:
            email: User email.
            team: Key of team to remove user from.
        """
        input = TeamMemberRemove(user=email, team=team)
        return self._gql_client.remove_team_member(input).remove_team_member

    def delete(self, email: str):
        self._gql_client.delete_user(email)


class AsyncUsers(AsyncAPIResource):  # type: ignore[misc]
    """
    Resource to manage users and permissions.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)

    async def me(self) -> UserData | None:
        """
        Get details of current user.
        """
        result = await self._gql_client.me()
        return result.me

    async def list(self) -> Sequence[UserData]:
        """
        List all users registered to Adaptive deployment.
        """
        result = await self._gql_client.list_users()
        return result.users

    async def create(
        self, email: str, name: str, teams_with_role: Sequence[tuple[str, str]]
    ) -> UserData:
        """
        Create a user and with preset teams and role
        """
        result = await self._gql_client.create_user(
            input=UserCreate(
                email=email,
                name=name,
                teams=[
                    UserCreateTeamWithRole(team=team, role=role)
                    for (team, role) in teams_with_role
                ],
            )
        )
        return result.create_user

    async def add_to_team(
        self, email: str, team: str, role: str
    ) -> UpdateUserSetTeamMember:
        """
        Update team and role for user.

        Args:
            email: User email.
            team: Key of team to which user will be added to.
            role: Assigned role

        """
        input = TeamMemberSet(user=email, team=team, role=role)
        result = await self._gql_client.update_user(input)
        return result.set_team_member

    async def remove_from_team(self, email: str, team: str) -> UserData:
        """
        Remove user from team.

        Args:
            email: User email.
            team: Key of team to remove user from.
        """
        input = TeamMemberRemove(user=email, team=team)
        return (await self._gql_client.remove_team_member(input)).remove_team_member

    async def delete(self, email: str):
        await self._gql_client.delete_user(email)
