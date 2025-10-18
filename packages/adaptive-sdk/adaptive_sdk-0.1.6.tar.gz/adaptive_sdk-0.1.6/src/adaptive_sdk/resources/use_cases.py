from __future__ import annotations
from typing import Sequence, TYPE_CHECKING
from loguru import logger

from adaptive_sdk.graphql_client import (
    UseCaseCreate,
    UseCaseSettingsInput,
    UseCaseData,
    UseCaseShares,
    UseCaseShareInput,
)

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class UseCase(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with use cases.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def create(
        self,
        key: str,
        name: str | None = None,
        description: str | None = None,
        team: str | None = None,
    ) -> UseCaseData:
        """
        Create new use case.

        Args:
            key: Use case key.
            name: Human-readable use case name which will be rendered in the UI.
                If not set, will be the same as `key`.
            description: Description of model which will be rendered in the UI.
        """

        input = UseCaseCreate(
            name=name if name else key,
            key=key,
            description=description,
            team=team,
            settings=UseCaseSettingsInput(defaultMetric=None),
        )
        return self._gql_client.create_use_case(input).create_use_case

    def list(self) -> Sequence[UseCaseData]:
        """
        List all use cases.
        """
        return self._gql_client.list_use_cases().use_cases

    def get(
        self,
        use_case: str | None = None,
    ) -> UseCaseData | None:
        """
        Get details for the client's use case.
        """

        return self._gql_client.describe_use_case(self.use_case_key(use_case)).use_case

    def share(self, use_case: str, team: str, role: str, is_owner: bool = False) -> UseCaseData | None:
        """
        Share use case with another team.
        Requires use_case:share permissions on the target use case.

        Args:
            use_case: Use case key.
            team: Team key.
            role: Role key.
        """
        use_case_details = self.get(use_case)
        share_inputs = []
        if use_case_details is None:
            logger.error(f"Use case key {use_case} not found")
            return None
        else:
            shares = use_case_details.shares
            team_exists_in_shares = False
            for share in shares:
                if share.team.key == team:
                    team_exists_in_shares = True
                share_inputs.append(
                    UseCaseShareInput(
                        team=share.team.key,
                        role=role if share.team.key == team else share.role.key,
                        isOwner=share.is_owner,
                    )
                )
            if not team_exists_in_shares:
                share_inputs.append(UseCaseShareInput(team=team, role=role, isOwner=is_owner))

        return self._gql_client.share_use_case(
            id_or_key=use_case, input=UseCaseShares(shares=share_inputs)
        ).share_use_case

    def unshare(self, use_case: str, team: str) -> UseCaseData | None:
        """
        Remove use case access for a team.
        Requires use_case:share permissions on the target use case.

        Args:
            use_case: Use case key.
            team: Team key.
        """
        use_case_details = self.get(use_case)
        share_inputs = []
        if use_case_details is None:
            logger.error(f"Use case key {use_case} not found")
            return None
        else:
            shares = use_case_details.shares
            team_exists_in_shares = False
            for share in shares:
                if share.team.key == team:
                    team_exists_in_shares = True
                    pass
                else:
                    share_inputs.append(
                        UseCaseShareInput(
                            team=share.team.key,
                            role=share.role.key,
                            isOwner=share.is_owner,
                        )
                    )
            if not team_exists_in_shares:
                logger.error(f"Team {team} did not have access to use_case {use_case} in the first place")
                return use_case_details

        return self._gql_client.share_use_case(
            id_or_key=use_case, input=UseCaseShares(shares=share_inputs)
        ).share_use_case


class AsyncUseCase(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with use cases.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def create(
        self,
        key: str,
        name: str | None = None,
        description: str | None = None,
        team: str | None = None,
        default_feedback_key: str | None = None,
    ) -> UseCaseData:
        """
        Create new use case.

        Args:
            key: Use case key.
            name: Human-readable use case name which will be rendered in the UI.
                If not set, will be the same as `key`.
            description: Description of model which will be rendered in the UI.
        """
        input = UseCaseCreate(
            name=name if name else key,
            key=key,
            description=description,
            team=team,
            settings=UseCaseSettingsInput(defaultMetric=default_feedback_key),
        )
        result = await self._gql_client.create_use_case(input)
        return result.create_use_case

    async def list(self) -> Sequence[UseCaseData]:
        """
        List all use cases.
        """
        result = await self._gql_client.list_use_cases()
        return result.use_cases

    async def get(
        self,
        use_case: str | None = None,
    ) -> UseCaseData | None:
        """
        Get details for the client's use case.
        """
        result = await self._gql_client.describe_use_case(self.use_case_key(use_case))
        return result.use_case

    async def share(self, use_case: str, team: str, role: str, is_owner: bool = False) -> UseCaseData | None:
        """
        Share use case with another team.
        Requires use_case:share permissions on the target use case.

        Args:
            use_case: Use case key.
            team: Team key.
            role: Role key.
        """
        use_case_details = await self.get(use_case)
        share_inputs = []
        if use_case_details is None:
            logger.error(f"Use case key {use_case} not found")
            return None
        else:
            shares = use_case_details.shares
            team_exists_in_shares = False
            for share in shares:
                if share.team.key == team:
                    team_exists_in_shares = True
                share_inputs.append(
                    UseCaseShareInput(
                        team=share.team.key,
                        role=role if share.team.key == team else share.role.key,
                        isOwner=share.is_owner,
                    )
                )
            if not team_exists_in_shares:
                share_inputs.append(UseCaseShareInput(team=team, role=role, isOwner=is_owner))

        return (
            await self._gql_client.share_use_case(id_or_key=use_case, input=UseCaseShares(shares=share_inputs))
        ).share_use_case

    async def unshare(self, use_case: str, team: str) -> UseCaseData | None:
        """
        Remove use case access for a team.
        Requires use_case:share permissions on the target use case.

        Args:
            use_case: Use case key.
            team: Team key.
        """
        use_case_details = await self.get(use_case)
        share_inputs = []
        if use_case_details is None:
            logger.error(f"Use case key {use_case} not found")
            return None
        else:
            shares = use_case_details.shares
            team_exists_in_shares = False
            for share in shares:
                if share.team.key == team:
                    team_exists_in_shares = True
                    pass
                else:
                    share_inputs.append(
                        UseCaseShareInput(
                            team=share.team.key,
                            role=share.role.key,
                            isOwner=share.is_owner,
                        )
                    )
            if not team_exists_in_shares:
                logger.error(f"Team {team} did not have access to use_case {use_case} in the first place")
                return use_case_details

        return (
            await self._gql_client.share_use_case(id_or_key=use_case, input=UseCaseShares(shares=share_inputs))
        ).share_use_case
