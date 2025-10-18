from __future__ import annotations
from typing import TypedDict, List, Any, TypeAlias, Literal
from typing_extensions import Required, NotRequired


class ChatMessage(TypedDict, total=True):
    role: Required[Literal["system", "user", "assistant"]]
    content: Required[str]


class ComparisonCompletion(TypedDict, total=True):
    text: Required[str]
    model: Required[str]


class CompletionComparisonFilterInput(TypedDict, total=True):
    """
    Filter for completion preference feedbacks.

    Args:
        metric: Feedback key logged against.
    """

    metric: Required[str]


class CompletionFeedbackFilterInput(TypedDict, total=False):
    """
    Filter for completion metric feedbacks.

    Args:
        metric: Feedback key logged against.
        gt: >
        gte: >=
        eq: ==
        neq: !=
        lt: <
        lte: <=
        user: Feedbacks logged by `user` id.
    """

    metric: Required[str]
    gt: NotRequired[float]
    gte: NotRequired[float]
    eq: NotRequired[float]
    neq: NotRequired[float]
    lt: NotRequired[float]
    lte: NotRequired[float]
    reasons: NotRequired[List[str]]
    user: NotRequired[Any]


class CompletionLabelFilter(TypedDict, total=False):
    """
    Filter for completion labels.
    """

    key: Required[str]
    value: NotRequired[List[str]]


CompletionSource: TypeAlias = Literal["LIVE", "OFFLINE", "AUTOMATION", "DATASET"]


class CursorPageInput(TypedDict, total=False):
    """
    Paging config.

    Args:
        first: Retrieve first n items starting from the `after` cursor.
        last: Retrieve last n items starting from the `after` cursor, limited to `before` cursor.
        after: Start cursor.
        before: End cursor.
    """

    first: NotRequired[int]
    after: NotRequired[str]
    before: NotRequired[str]
    last: NotRequired[int]


class InteractionFeedbackDict(TypedDict):
    """
    Interaction feedback.

    Args:
        feedback_key: Feedback key to register feedback against.
        value: Metric feedback value.
        details: Optional feedback text details.
    """

    feedback_key: Required[str]
    value: Required[int | float | bool]
    details: NotRequired[str]


class JudgeExampleInput(TypedDict, total=False):
    """
    Example to guide an AI judge's reasoning when evaluating a completion (few-shot prompting).

    Args:
        input: Ordered list of chat messages (role/content) that form the conversation context.
        output: Assistant completion to be evaluated.
        passes: Boolean indicating whether the *output* satisfies the criteria.
        reasoning: Optional free-text with the rationale behind the decision.
    """

    input: Required[List[ChatMessage]]
    output: Required[str]
    passes: Required[bool]
    reasoning: Required[str]


class ListCompletionsFilterInput(TypedDict, total=False):
    """
    Filter for listing interactions.

    Args:
        models: Model keys.
        timerange: A timerange in timestamp format.
        user_id: User ID that created interaction.
        feedbacks: TypedDict for metric feedback filtering.
        comparisons: TypedDict for preference feedback filtering.
        labels: TypedDict for completion labels filtering.
        completion_id: Completion id.
        source: Interaction source filter.
    """

    models: NotRequired[List[str]]
    timerange: NotRequired["TimeRange"]
    session_id: NotRequired[Any]
    user_id: NotRequired[Any]
    feedbacks: NotRequired[List["CompletionFeedbackFilterInput"]]
    comparisons: NotRequired[List["CompletionComparisonFilterInput"]]
    labels: NotRequired[List["CompletionLabelFilter"]]
    prompt_hash: NotRequired[str]
    completion_id: NotRequired[Any]
    tags: NotRequired[List[str]]
    source: NotRequired[List[CompletionSource]]


class ModelComputeConfigInput(TypedDict, total=False):
    tp: NotRequired[int]
    kv_cache_len: NotRequired[int]
    max_seq_len: NotRequired[int]


class ModelFilter(TypedDict, total=False):
    in_storage: NotRequired[bool]
    available: NotRequired[bool]
    trainable: NotRequired[bool]
    kind: NotRequired[List[Literal["Embedding", "Generation"]]]
    view_all: NotRequired[bool]
    online: NotRequired[List[Literal["ONLINE", "OFFLINE", "PENDING", "ERROR"]]]


class ModelPlacementInput(TypedDict, total=False):
    compute_pools: Required[List[str]]
    max_ttft_ms: NotRequired[int]


class TimeRange(TypedDict, total=False):
    """
    A timerange filter, in Unix timestamp format (ms).

    Args:
        from_: The start timestamp.
        to: The end timestamp.
    """

    from_: Required[int | str]
    to: Required[int | str]


class Order(TypedDict, total=False):
    """
    Ordering of interaction list results.

    Args:
        field: On what field to order by.
        order: Ascending or descending; alphabetical for string fields.
    """

    field: Required[str]
    order: Required[Literal["ASC", "DESC"]]
