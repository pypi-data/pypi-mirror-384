from __future__ import annotations
from typing import TYPE_CHECKING, List

from adaptive_sdk.graphql_client import ListRolesRoles, RoleCreate, CreateRoleCreateRole

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class Roles(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to manage roles.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def list(self) -> List[ListRolesRoles]:
        return self._gql_client.list_roles().roles

    def create(
        self, key: str, permissions: List[str], name: str | None = None
    ) -> CreateRoleCreateRole:
        """
        Creates new role.

        Args:
            key: Role key.
            permissions: List of permission identifiers such as `use_case:read`. You can list all possible permissions with client.permissions.list().
            name: Role name; if not provided, defaults to `key`.
        """
        input = RoleCreate(key=key, name=name or key, permissions=permissions)
        return self._gql_client.create_role(input).create_role


class AsyncRoles(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to manage roles.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def list(self) -> List[ListRolesRoles]:
        return (await self._gql_client.list_roles()).roles

    async def create(
        self, key: str, permissions: List[str], name: str | None = None
    ) -> CreateRoleCreateRole:
        """
        Creates new role.

        Args:
            key: Role key.
            permissions: List of permission identifiers such as `use_case:read`. You can list all possible permissions with client.permissions.list().
            name: Role name; if not provided, defaults to `key`.
        """
        input = RoleCreate(key=key, name=name or key, permissions=permissions)
        return (await self._gql_client.create_role(input)).create_role
