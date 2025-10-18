from __future__ import annotations
from typing import Sequence, Literal, List, TYPE_CHECKING

from adaptive_sdk.graphql_client import (
    DescribeAbCampaignAbCampaign,
    AbCampaignDetailData,
    AbCampaignCreateData,
    AbcampaignStatus,
    AbCampaignFilter,
    FeedbackType,
    AbcampaignCreate,
)

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive


class ABTests(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with AB Tests.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def create(
        self,
        ab_test_key: str,
        feedback_key: str,
        models: List[str],
        traffic_split: float = 1.0,
        feedback_type: Literal["metric", "preference"] = "metric",
        auto_deploy: bool = False,
        use_case: str | None = None,
    ) -> AbCampaignCreateData:
        """
        Creates a new A/B test in the client's use case.

        Args:
            ab_test_key: A unique key to identify the AB test.
            feedback_key: The feedback key against which the AB test will run.
            models: The models to include in the AB test; they must be attached to the use case.
            traffic_split: Percentage of production traffic to route to AB test.
                `traffic_split*100` % of inference requests for the use case will be sent randomly to one of the models included in the AB test.
            feedback_type: What type of feedback to run the AB test on, metric or preference.
            auto_deploy: If set to `True`, when the AB test is completed, the winning model automatically gets promoted to the use case default model.
        """
        if feedback_type not in ["metric", "preference"]:
            raise ValueError(
                "Only `metric` and `preference` feedback types are supported for AB tests."
            )
        match feedback_type:
            case "metric":
                new_feedback_type = "DIRECT"
            case "preference":
                new_feedback_type = "COMPARISON"

        feedback_type_enum = FeedbackType(new_feedback_type)
        input = AbcampaignCreate(
            key=ab_test_key,
            metric=feedback_key,
            useCase=self.use_case_key(use_case),
            modelServices=models,
            trafficSplit=traffic_split,
            autoDeploy=auto_deploy,
            feedbackType=feedback_type_enum,
        )
        return self._gql_client.create_ab_campaign(input).create_ab_campaign

    def cancel(self, key: str) -> str:
        """
        Cancel an ongoing AB test.

        Args:
            key: The AB test key.
        """
        return self._gql_client.cancel_ab_campaign(input=key).cancel_ab_campaign

    def list(
        self,
        active: bool | None = None,
        status: Literal["warmup", "in_progress", "done", "cancelled"] | None = None,
        use_case: str | None = None,
    ) -> Sequence[AbCampaignDetailData]:
        """
        List the use case AB tests.

        Args:
            active: Filter on active or inactive AB tests.
            status: Filter on one of the possible AB test status.
        """
        if status:
            status_input = AbcampaignStatus(status.upper())
            input = AbCampaignFilter(
                active=active, status=status_input, useCase=self.use_case_key(use_case)
            )
        else:
            input = AbCampaignFilter(active=active, useCase=self.use_case_key(use_case))
        return self._gql_client.list_ab_campaigns(input).ab_campaigns

    def get(self, key: str) -> DescribeAbCampaignAbCampaign | None:
        """
        Get the details of an AB test.

        Args:
            key: The AB test key.
        """
        return self._gql_client.describe_ab_campaign(input=key).ab_campaign


class AsyncABTests(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with AB Tests.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def create(
        self,
        ab_test_key: str,
        feedback_key: str,
        models: List[str],
        traffic_split: float = 1.0,
        feedback_type: Literal["metric", "preference"] = "metric",
        auto_deploy: bool = False,
        use_case: str | None = None,
    ) -> AbCampaignCreateData:
        """
        Creates a new A/B test in the client's use case.

        Args:
            ab_test_key: A unique key to identify the AB test.
            feedback_key: The feedback key against which the AB test will run.
            models: The models to include in the AB test; they must be attached to the use case.
            traffic_split: Percentage of production traffic to route to AB test.
                `traffic_split*100` % of inference requests for the use case will be sent randomly to one of the models included in the AB test.
            feedback_type: What type of feedback to run the AB test on, metric (direct) or preference (comparison).
            auto_deploy: If set to `True`, when the AB test is completed, the winning model automatically gets promoted to the use case default model.
        """
        if feedback_type not in ["metric", "preference"]:
            raise ValueError(
                "Only `metric` and `preference` feedback types are supported for AB tests."
            )
        match feedback_type:
            case "metric":
                new_feedback_type = "DIRECT"
            case "preference":
                new_feedback_type = "COMPARISON"

        feedback_type_enum = FeedbackType(new_feedback_type)
        input = AbcampaignCreate(
            key=ab_test_key,
            metric=feedback_key,
            useCase=self.use_case_key(use_case),
            modelServices=models,
            trafficSplit=traffic_split,
            autoDeploy=auto_deploy,
            feedbackType=feedback_type_enum,
        )
        result = await self._gql_client.create_ab_campaign(input)
        return result.create_ab_campaign

    async def cancel(self, key: str) -> str:
        """
        Cancel an ongoing AB test.

        Args:
            key: The AB test key.
        """
        result = await self._gql_client.cancel_ab_campaign(input=key)
        return result.cancel_ab_campaign

    async def list(
        self,
        active: bool | None = None,
        status: Literal["warmup", "in_progress", "done", "cancelled"] | None = None,
        use_case: str | None = None,
    ) -> Sequence[AbCampaignDetailData]:
        """
        List the use case AB tests.

        Args:
            active: Filter on active or inactive AB tests.
            status: Filter on one of the possible AB test status.
        """
        if status:
            status_input = AbcampaignStatus(status.upper())
            input = AbCampaignFilter(
                active=active, status=status_input, useCase=self.use_case_key(use_case)
            )
        else:
            input = AbCampaignFilter(active=active, useCase=self.use_case_key(use_case))
        result = await self._gql_client.list_ab_campaigns(input)
        return result.ab_campaigns

    async def get(self, key: str) -> DescribeAbCampaignAbCampaign | None:
        """
        Get the details of an AB test.

        Args:
            key: The AB test key.
        """
        result = await self._gql_client.describe_ab_campaign(input=key)
        return result.ab_campaign
