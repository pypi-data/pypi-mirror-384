from __future__ import annotations
from copy import deepcopy
import humps
from typing import Dict, List, Literal, TYPE_CHECKING
from uuid import UUID

from adaptive_sdk import input_types
from adaptive_sdk.error_handling import rest_error_handler
from adaptive_sdk.graphql_client import (
    CompletionGroupBy,
    CursorPageInput,
    ListCompletionsFilterInput,
    OrderPair,
    ListInteractionsCompletions,
    ListGroupedInteractionsCompletionsGrouped,
    CompletionData,
)
from adaptive_sdk.graphql_client.base_model import UNSET
from adaptive_sdk.rest import rest_types
from adaptive_sdk.utils import convert_optional_UUID
from typing_extensions import override

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive

ROUTE = "/interactions"


def _prepare_add_interactions_inputs(
    messages: list[input_types.ChatMessage],
    feedbacks: list[input_types.InteractionFeedbackDict] | None,
):
    input_messages = (
        [rest_types.ChatMessage(role=m["role"], content=m["content"]) for m in messages]
    )
    input_feedbacks = (
        [
            rest_types.InteractionFeedback(
                metric=i["feedback_key"],
                value=i["value"],
                details=i.get("details"),
            )
            for i in feedbacks
        ]
        if feedbacks
        else None
    )
    return input_messages, input_feedbacks


class Interactions(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with interactions.
    """

    @override
    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def create(
        self,
        messages: List[input_types.ChatMessage],
        completion: str,
        model: str | None = None,
        feedbacks: List[input_types.InteractionFeedbackDict] | None = None,
        user: str | UUID | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        ab_campaign: str | None = None,
        labels: Dict[str, str] | None = None,
        created_at: str | None = None,
    ) -> rest_types.AddInteractionsResponse:
        """
        Create/log an interaction.

        Args:
            model: Model key.
            messages: Input chat messages, each dict should have keys `role` and `content`.
            completion: Model completion.
            feedbacks: List of feedbacks, each dict should with keys `feedback_key`, `value` and optional(`details`).
            user: ID of user making the request. If not `None`, will be logged as metadata for the interaction.
            ab_campaign: AB test key. If set, provided `feedbacks` will count towards AB test results.
            labels: Key-value pairs of interaction labels.
            created_at: Timestamp of interaction creation or ingestion.
        """

        input_messages, input_feedbacks = _prepare_add_interactions_inputs(messages, feedbacks)

        input = rest_types.AddInteractionsRequest(
            model_service=model,
            use_case=self.use_case_key(use_case),
            completion=completion,
            messages=input_messages,
            feedbacks=input_feedbacks,
            user=convert_optional_UUID(user),
            session_id=convert_optional_UUID(session_id),
            ab_campaign=ab_campaign,
            labels=labels,
            created_at=created_at,
        )
        r = self._rest_client.post(ROUTE, json=input.model_dump(exclude_none=True))
        rest_error_handler(r)
        return rest_types.AddInteractionsResponse.model_validate(r.json())

    def list(
        self,
        order: List[input_types.Order] | None = None,
        filters: input_types.ListCompletionsFilterInput | None = None,
        page: input_types.CursorPageInput | None = None,
        group_by: Literal["model", "prompt"] | None = None,
        use_case: str | None = None,
    ) -> ListInteractionsCompletions | ListGroupedInteractionsCompletionsGrouped:
        """
        List interactions in client's use case.

        Args:
            order: Ordering of results.
            filters: List filters.
            page: Paging config.
            group_by: Retrieve interactions grouped by selected dimension.

        """
        new_filters = {} if filters is None else deepcopy(filters)
        order = [] if order is None else order
        new_page = {} if page is None else page

        new_filters = humps.camelize(new_filters)
        new_order = humps.camelize(order)
        new_page = humps.camelize(new_page)

        if new_filters.get("timerange"):
            new_filters["timerange"]["from"] = new_filters["timerange"]["from_"]  # type: ignore
            del new_filters["timerange"]["from_"]  # type: ignore

        new_filters.update({"useCase": self.use_case_key(use_case)})  # type: ignore
        order_inputs = [OrderPair.model_validate(o) for o in new_order] if new_order else UNSET
        if group_by:
            return self._gql_client.list_grouped_interactions(
                filter=ListCompletionsFilterInput.model_validate(new_filters),
                group_by=CompletionGroupBy(group_by.upper()),
                page=CursorPageInput.model_validate(new_page),
                order=order_inputs,
            ).completions_grouped
        else:
            return self._gql_client.list_interactions(
                filter=ListCompletionsFilterInput.model_validate(new_filters),
                page=CursorPageInput.model_validate(new_page),
                order=order_inputs,
            ).completions

    def get(
        self,
        completion_id: str,
        use_case: str | None = None,
    ) -> CompletionData | None:
        """
        Get the details for one specific interaction.

        Args:
            completion_id: The ID of the completion.
        """
        return self._gql_client.describe_interaction(use_case=self.use_case_key(use_case), id=completion_id).completion


class AsyncInteractions(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with interactions.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def create(
        self,
        messages: List[input_types.ChatMessage],
        completion: str,
        model: str | None = None,
        feedbacks: List[input_types.InteractionFeedbackDict] | None = None,
        user: str | UUID | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        ab_campaign: str | None = None,
        labels: Dict[str, str] | None = None,
    ) -> rest_types.AddInteractionsResponse:
        """
        Create/log an interaction.

        Args:
            model: Model key.
            messages: Input chat messages, each dict should have keys `role` and `content`.
            completion: Model completion.
            feedbacks: List of feedbacks, each dict should with keys `feedback_key`, `value` and optional(`details`).
            user: ID of user making the request. If not `None`, will be logged as metadata for the interaction.
            ab_campaign: AB test key. If set, provided `feedbacks` will count towards AB test results.
            labels: Key-value pairs of interaction labels.
            created_at: Timestamp of interaction creation or ingestion.
        """
        input_messages, input_feedbacks = _prepare_add_interactions_inputs(messages, feedbacks)

        input = rest_types.AddInteractionsRequest(
            model_service=model,
            use_case=self.use_case_key(use_case),
            completion=completion,
            messages=input_messages,
            feedbacks=input_feedbacks,
            user=convert_optional_UUID(user),
            session_id=convert_optional_UUID(session_id),
            ab_campaign=ab_campaign,
            labels=labels,
        )
        r = await self._rest_client.post(ROUTE, json=input.model_dump(exclude_none=True))
        rest_error_handler(r)
        return rest_types.AddInteractionsResponse.model_validate(r.json())

    async def list(
        self,
        order: List[input_types.Order] | None = None,
        filters: input_types.ListCompletionsFilterInput | None = None,
        page: input_types.CursorPageInput | None = None,
        group_by: Literal["model", "prompt"] | None = None,
        use_case: str | None = None,
    ) -> ListInteractionsCompletions | ListGroupedInteractionsCompletionsGrouped:
        """
        List interactions in client's use case.

        Args:
            order: Ordering of results.
            filters: List filters.
            page: Paging config.
            group_by: Retrieve interactions grouped by selected dimension.

        """
        new_filters = {} if filters is None else deepcopy(filters)
        order = [] if order is None else order
        new_page = {} if page is None else page

        new_filters = humps.camelize(new_filters)
        new_order = humps.camelize(order)
        new_page = humps.camelize(new_page)

        if new_filters.get("timerange"):
            new_filters["timerange"]["from"] = new_filters["timerange"]["from_"]  # type: ignore
            del new_filters["timerange"]["from_"]  # type: ignore

        new_filters.update({"useCase": self.use_case_key(use_case)})  # type: ignore
        order_inputs = [OrderPair.model_validate(o) for o in new_order] if new_order else UNSET
        if group_by:
            result = await self._gql_client.list_grouped_interactions(
                filter=ListCompletionsFilterInput.model_validate(new_filters),
                group_by=CompletionGroupBy(group_by.upper()),
                page=CursorPageInput.model_validate(new_page),
                order=order_inputs,
            )
            return result.completions_grouped
        else:
            result = await self._gql_client.list_interactions(
                filter=ListCompletionsFilterInput.model_validate(new_filters),
                page=CursorPageInput.model_validate(new_page),
                order=order_inputs,
            )  # type: ignore[assignment]
            return result.completions  # type: ignore[attr-defined]

    async def get(
        self,
        completion_id: str,
        use_case: str | None = None,
    ) -> CompletionData | None:
        """
        Get the details for one specific interaction.

        Args:
            completion_id: The ID of the completion.
        """
        result = await self._gql_client.describe_interaction(use_case=self.use_case_key(use_case), id=completion_id)
        return result.completion
