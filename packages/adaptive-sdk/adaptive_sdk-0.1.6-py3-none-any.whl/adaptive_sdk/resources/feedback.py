from __future__ import annotations
from typing import Literal, Sequence, List, Dict, TYPE_CHECKING
from uuid import UUID
from typing_extensions import override
from adaptive_sdk import input_types
from adaptive_sdk.error_handling import rest_error_handler
from adaptive_sdk.graphql_client import (
    MetricData,
    MetricDataAdmin,
    MetricCreate,
    MetricKind,
    MetricScoringType,
    MetricWithContextData,
    MetricLink,
    MetricUnlink,
)
from adaptive_sdk.rest import rest_types
from adaptive_sdk.utils import (
    convert_optional_UUID,
    validate_comparison_completion,
)
from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive

FEEDBACK_ROUTE = "/feedback"
PREFERENCE_ROUTE = "/comparison"
OUTCOME_ROUTE = "/outcome"


class Feedback(SyncAPIResource, UseCaseResource):  # type: ignore
    """
    Resource to interact with and log feedback.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def register_key(
        self,
        key: str,
        kind: Literal["scalar", "bool"] = "scalar",
        scoring_type: Literal[
            "higher_is_better", "lower_is_better"
        ] = "higher_is_better",
        name: str | None = None,
        description: str | None = None,
    ) -> MetricData:
        """
        Register a new feedback key. Feedback can be logged against this key once it is created.

        Args:
            key: Feedback key.
            kind: Feedback kind.
                If `"bool"`, you can log values `0`, `1`, `True` or `False` only.
                If `"scalar"`, you can log any integer or float value.
            scoring_type: Indication of what good means for this feeback key; a higher numeric value (or `True`)
                , or a lower numeric value (or `False`).
            name Human-readable feedback name that will render in the UI. If `None`, will be the same as `key`.
            description: Description of intended purpose or nuances of feedback. Will render in the UI.
        """
        input = MetricCreate(
            name=name if name else key,
            key=key,
            kind=MetricKind(kind.upper()),
            scoringType=MetricScoringType(scoring_type.upper()),
            description=description,
        )
        return self._gql_client.create_metric(input).create_metric

    def list_keys(self) -> Sequence[MetricDataAdmin]:
        """
        List all feedback keys.
        """
        return self._gql_client.list_metrics().metrics

    def get_key(self, feedback_key: str) -> MetricData | None:
        """
        Get the details of a feedback key.

        Args:
            feedback_key: The feedback key.
        return self._gql_client.describe_metric(input=feedback_key).metric
        """
        return self._gql_client.describe_metric(input=feedback_key).metric

    def link(
        self,
        feedback_key: str,
        use_case: str | None = None,
    ) -> MetricWithContextData:
        """
        Link a feedback key to the client's use case.
        Once a feedback key is linked to a use case, its statistics and associations with interactions will render in the UI.

        Args:
            feedback_key: The feedback key to be linked.
        """
        input = MetricLink(useCase=self.use_case_key(use_case), metric=feedback_key)
        return self._gql_client.link_metric(input).link_metric

    def unlink(
        self,
        feedback_key: str,
        use_case: str | None = None,
    ) -> str:
        """
        Unlink a feedback key from the client's use case.

        Args:
            feedback_key: The feedback key to be unlinked.
        """
        input = MetricUnlink(useCase=self.use_case_key(use_case), metric=feedback_key)
        return self._gql_client.unlink_metric(input).unlink_metric

    def log_metric(
        self,
        value: bool | float | int,
        completion_id: str | UUID,
        feedback_key: str,
        user: str | UUID | None = None,
        details: str | None = None,
    ) -> rest_types.FeedbackOutput:
        """
        Log metric feedback for a single completion, which can be a float, int or bool depending on the kind of `feedback_key` it is logged against.

        Args:
            value: The feedback values.
            completion_id: The completion_id to attach the feedback to.
            feedback_key: The feedback key to log against.
            user: ID of user submitting feedback. If not `None`, will be logged as metadata for the request.
            details: Textual details for the feedback. Can be used to provide further context on the feedback `value`.
        """
        input = rest_types.AddFeedbackRequest(
            value=value,
            completion_id=convert_optional_UUID(completion_id),
            metric=feedback_key,
            user_id=convert_optional_UUID(user),
            details=details,
        )
        r = self._rest_client.post(
            FEEDBACK_ROUTE, json=input.model_dump(exclude_none=True)
        )
        rest_error_handler(r)
        return rest_types.FeedbackOutput.model_validate(r.json())

    def log_preference(
        self,
        feedback_key: str,
        preferred_completion: str | UUID | input_types.ComparisonCompletion,
        other_completion: str | UUID | input_types.ComparisonCompletion,
        user: str | UUID | None = None,
        messages: List[Dict[str, str]] | None = None,
        tied: Literal["good", "bad"] | None = None,
        use_case: str | None = None,
    ) -> rest_types.ComparisonOutput:
        """
        Log preference feedback between 2 completions.

        Args:
            feedback_key: The feedback key to log against.
            preferred_completion: Can be a completion_id or a dict with keys `model` and `text`,
                corresponding the a valid model key and its attributed completion.
            other_completion: Can be a completion_id or a dict with keys `model` and `text`,
                corresponding the a valid model key and its attributed completion.
            user: ID of user submitting feedback.
            messages: Input chat messages, each dict with keys `role` and `content`.
                Ignored if `preferred_` and `other_completion` are completion_ids.
            tied: Indicator if both completions tied as equally bad or equally good.
        """

        clean_preffered_completion = validate_comparison_completion(
            preferred_completion
        )
        clean_other_completion = validate_comparison_completion(other_completion)
        input_messages = [rest_types.ChatMessage(**m) for m in messages] if messages else None  # type: ignore

        input = rest_types.AddComparisonRequest(
            metric=feedback_key,
            preferred_completion=clean_preffered_completion,
            other_completion=clean_other_completion,
            user_id=convert_optional_UUID(user),
            messages=input_messages,
            tied=rest_types.ComparisonTie(tied) if tied else None,
            use_case=self.use_case_key(use_case),
        )
        r = self._rest_client.post(
            PREFERENCE_ROUTE, json=input.model_dump(exclude_none=True)
        )
        rest_error_handler(r)
        return rest_types.ComparisonOutput.model_validate(r.json())


class AsyncFeedback(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with and log feedback.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def register_key(
        self,
        key: str,
        kind: Literal["scalar", "bool"],
        scoring_type: Literal[
            "higher_is_better", "lower_is_better"
        ] = "higher_is_better",
        name: str | None = None,
        description: str | None = None,
    ) -> MetricData:
        """
        Register a new feedback key. Feedback can be logged against this key once it is created.

        Args:
            key: Feedback key.
            kind: Feedback kind.
                If `"bool"`, you can log values `0`, `1`, `True` or `False` only.
                If `"scalar"`, you can log any integer or float value.
            scoring_type: Indication of what good means for this feeback key; a higher numeric value (or `True`)
                , or a lower numeric value (or `False`).
            name: Human-readable feedback name that will render in the UI. If `None`, will be the same as `key`.
            description: Description of intended purpose or nuances of feedback. Will render in the UI.
        """
        input = MetricCreate(
            name=name if name else key,
            key=key,
            kind=MetricKind(kind.upper()),
            scoringType=MetricScoringType(scoring_type.upper()),
            description=description,
        )
        return (await self._gql_client.create_metric(input)).create_metric

    async def list_keys(self) -> Sequence[MetricDataAdmin]:
        """
        List all feedback keys.
        """
        return (await self._gql_client.list_metrics()).metrics

    async def get_key(self, feedback_key: str) -> MetricData | None:
        """
        Get the details of a feedback key.

        Args:
            feedback_key: The feedback key.
        """
        return (await self._gql_client.describe_metric(input=feedback_key)).metric

    async def link(
        self,
        feedback_key: str,
        use_case: str | None = None,
    ) -> MetricWithContextData:
        """
        Link a feedback key to the client's use case.
        Once a feedback key is linked to a use case, its statistics and associations with interactions will render in the UI.

        Args:
            feedback_key: The feedback key to be linked.
        """
        input = MetricLink(useCase=self.use_case_key(use_case), metric=feedback_key)
        result = await self._gql_client.link_metric(input)
        return result.link_metric

    async def unlink(
        self,
        feedback_key: str,
        use_case: str | None = None,
    ) -> str:
        """
        Unlink a feedback key from the client's use case.

        Args:
            feedback_key: The feedback key to be unlinked.
        """
        input = MetricUnlink(useCase=self.use_case_key(use_case), metric=feedback_key)
        result = await self._gql_client.unlink_metric(input)
        return result.unlink_metric

    async def log_metric(
        self,
        value: bool | float | int,
        completion_id: str | UUID,
        feedback_key: str,
        user_id: str | UUID | None = None,
        details: str | None = None,
    ) -> rest_types.FeedbackOutput:
        """
        Log metric feedback for a single completion, which can be a float, int or bool depending on the kind of `feedback_key` it is logged against.

        Args:
            value: The feedback values.
            completion_id: The completion_id to attach the feedback to.
            feedback_key: The feedback key to log against.
            user: ID of user submitting feedback. If not `None`, will be logged as metadata for the request.
            details: Textual details for the feedback. Can be used to provide further context on the feedback `value`.
        """
        input = rest_types.AddFeedbackRequest(
            value=value,
            completion_id=convert_optional_UUID(completion_id),
            metric=feedback_key,
            user_id=convert_optional_UUID(user_id),
            details=details,
        )
        r = await self._rest_client.post(
            FEEDBACK_ROUTE, json=input.model_dump(exclude_none=True)
        )
        rest_error_handler(r)
        return rest_types.FeedbackOutput.model_validate(r.json())

    async def log_preference(
        self,
        feedback_key: str,
        preferred_completion: str | UUID | input_types.ComparisonCompletion,
        other_completion: str | UUID | input_types.ComparisonCompletion,
        user_id: str | UUID | None = None,
        messages: List[Dict[str, str]] | None = None,
        tied: Literal["good", "bad"] | None = None,
        use_case: str | None = None,
    ) -> rest_types.ComparisonOutput:
        """
        Log preference feedback between 2 completions.

        Args:
            feedback_key: The feedback key to log against.
            preferred_completion: Can be a completion_id or a dict with keys `model` and `text`,
                corresponding the a valid model key and its attributed completion.
            other_completion: Can be a completion_id or a dict with keys `model` and `text`,
                corresponding the a valid model key and its attributed completion.
            user: ID of user submitting feedback.
            messages: Input chat messages, each dict with keys `role` and `content`.
                Ignored if `preferred_` and `other_completion` are completion_ids.
            tied: Indicator if both completions tied as equally bad or equally good.

        """
        clean_preffered_completion = validate_comparison_completion(
            preferred_completion
        )
        clean_other_completion = validate_comparison_completion(other_completion)
        input_messages = [rest_types.ChatMessage(**m) for m in messages] if messages else None  # type: ignore

        input = rest_types.AddComparisonRequest(
            metric=feedback_key,
            preferred_completion=clean_preffered_completion,
            other_completion=clean_other_completion,
            user_id=convert_optional_UUID(user_id),
            messages=input_messages,
            tied=rest_types.ComparisonTie(tied) if tied else None,
            use_case=self.use_case_key(use_case),
        )
        r = await self._rest_client.post(
            PREFERENCE_ROUTE, json=input.model_dump(exclude_none=True)
        )
        rest_error_handler(r)
        return rest_types.ComparisonOutput.model_validate(r.json())
