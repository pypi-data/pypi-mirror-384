from typing import Any, List, Optional
from pydantic import Field
from .base_model import BaseModel
from .enums import AbcampaignStatus, CompletionGroupBy, CompletionSource, DatasetKind, DatasetSource, DateBucketUnit, ExternalModelProviderName, FeedbackType, GraderTypeEnum, JobArtifactKind, JobKind, JobStatus, MetricAggregation, MetricKind, MetricScoringType, ModelKindFilter, ModelOnline, OpenAIModel, PrebuiltCriteriaKey, Protocol, SelectionTypeInput, SortDirection, TimeseriesInterval, UnitPosition

class AbCampaignFilter(BaseModel):
    """@private"""
    active: Optional[bool] = None
    status: Optional[AbcampaignStatus] = None
    use_case: Optional[str] = Field(alias='useCase', default=None)

class AbcampaignCreate(BaseModel):
    """@private"""
    key: str
    name: Optional[str] = None
    metric: str
    use_case: str = Field(alias='useCase')
    model_services: List[str] = Field(alias='modelServices')
    auto_deploy: bool = Field(alias='autoDeploy')
    traffic_split: float = Field(alias='trafficSplit')
    feedback_type: FeedbackType = Field(alias='feedbackType', default=FeedbackType.DIRECT)

class AddExternalModelInput(BaseModel):
    """@private"""
    name: str
    provider: ExternalModelProviderName
    provider_data: Optional['ModelProviderDataInput'] = Field(alias='providerData', default=None)
    description: Optional[str] = None

class AddHFModelInput(BaseModel):
    """@private"""
    model_id: str = Field(alias='modelId')
    output_model_name: str = Field(alias='outputModelName')
    output_model_key: Optional[str] = Field(alias='outputModelKey', default=None)
    hf_token: str = Field(alias='hfToken')
    compute_pool: Optional[str] = Field(alias='computePool', default=None)
    num_gpus: int = Field(alias='numGpus', default=0)

class AddModelInput(BaseModel):
    """@private"""
    path: str
    name: str
    key: Optional[str] = None

class AnthropicProviderDataInput(BaseModel):
    """@private"""
    api_key: str = Field(alias='apiKey')
    external_model_id: str = Field(alias='externalModelId')

class ApiKeyCreate(BaseModel):
    """@private"""
    user: str

class ArtifactFilter(BaseModel):
    """@private"""
    kinds: Optional[List[JobArtifactKind]] = None
    job_id: Optional[Any] = Field(alias='jobId', default=None)

class AttachModel(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    model: str
    attached: bool = True
    placement: Optional['ModelPlacementInput'] = None
    wait: bool = False
    'Wait for the model to be deployed or not'

class AzureProviderDataInput(BaseModel):
    """@private"""
    api_key: str = Field(alias='apiKey')
    external_model_id: str = Field(alias='externalModelId')
    endpoint: str

class CompletionComparisonFilterInput(BaseModel):
    """@private"""
    metric: str

class CompletionFeedbackFilterInput(BaseModel):
    """@private"""
    metric: str
    gt: Optional[float] = None
    gte: Optional[float] = None
    eq: Optional[float] = None
    neq: Optional[float] = None
    lt: Optional[float] = None
    lte: Optional[float] = None
    reasons: Optional[List[str]] = None
    user: Optional[Any] = None

class CompletionLabelValue(BaseModel):
    """@private"""
    key: str
    value: str

class CompletionsByFilters(BaseModel):
    """@private"""
    filters: 'ListCompletionsFilterInput'
    exclude: List[Any]

class CompletionsById(BaseModel):
    """@private"""
    include: List[Any]

class CreateRecipeInput(BaseModel):
    """@private"""
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[List['LabelInput']] = None

class CreateToolProviderInput(BaseModel):
    """@private"""
    key: str
    name: str
    uri: str
    protocol: Protocol

class CursorPageInput(BaseModel):
    """@private"""
    first: Optional[int] = None
    after: Optional[str] = None
    before: Optional[str] = None
    last: Optional[int] = None

class CustomConfigInput(BaseModel):
    """@private"""
    description: Optional[str] = None

class CustomRecipeFilterInput(BaseModel):
    """@private"""
    labels: Optional[List['LabelFilter']] = None

class DatasetCompletionQuery(BaseModel):
    """@private"""
    from_selection: Optional['CompletionsById'] = Field(alias='fromSelection', default=None)
    from_filters: Optional['CompletionsByFilters'] = Field(alias='fromFilters', default=None)
    from_groups: Optional['FromGroupsQuery'] = Field(alias='fromGroups', default=None)

class DatasetCreate(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    name: str
    key: Optional[str] = None
    source: Optional[DatasetSource] = None

class DatasetCreateFromFilters(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    name: str
    key: Optional[str] = None
    completion_query: 'DatasetCompletionQuery' = Field(alias='completionQuery')
    sample_config: Optional['SampleConfig'] = Field(alias='sampleConfig', default=None)
    feedback_filters: Optional['FeedbackFilterInput'] = Field(alias='feedbackFilters', default=None)
    kind: DatasetKind
    metrics: Optional[List[str]] = None

class DatasetCreateFromMultipartUpload(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    name: str
    key: Optional[str] = None
    source: Optional[DatasetSource] = None
    upload_session_id: str = Field(alias='uploadSessionId')

class EmojiInput(BaseModel):
    """@private"""
    native: str

class FeedbackAddInput(BaseModel):
    """@private"""
    value: Any
    details: Optional[str] = None
    reason: Optional[str] = None
    user_id: Optional[Any] = Field(alias='userId', default=None)

class FeedbackFilterInput(BaseModel):
    """@private"""
    labels: Optional[List['LabelFilter']] = None

class FeedbackUpdateInput(BaseModel):
    """@private"""
    value: Optional[Any] = None
    details: Optional[str] = None

class FromGroupsQuery(BaseModel):
    """@private"""
    filters: 'ListCompletionsFilterInput'
    grouping: CompletionGroupBy
    groups: List['GroupSelectionQuery']

class GlobalUsageFilterInput(BaseModel):
    """@private"""
    timerange: Optional['TimeRange'] = None
    'use none to get "all time" data'
    interval: DateBucketUnit
    timezone: Optional[str] = None

class GoogleProviderDataInput(BaseModel):
    """@private"""
    api_key: str = Field(alias='apiKey')
    external_model_id: str = Field(alias='externalModelId')

class GraderConfigInput(BaseModel):
    """@private"""
    judge: Optional['JudgeConfigInput'] = None
    prebuilt: Optional['PrebuiltConfigInput'] = None
    remote: Optional['RemoteConfigInput'] = None
    custom: Optional['CustomConfigInput'] = None

class GraderCreateInput(BaseModel):
    """@private"""
    name: str
    key: Optional[str] = None
    grader_type: GraderTypeEnum = Field(alias='graderType')
    grader_config: 'GraderConfigInput' = Field(alias='graderConfig')
    metric: Optional['MetricGetOrCreate'] = None

class GraderUpdateInput(BaseModel):
    """@private"""
    name: Optional[str] = None
    grader_type: Optional[GraderTypeEnum] = Field(alias='graderType', default=None)
    grader_config: Optional['GraderConfigInput'] = Field(alias='graderConfig', default=None)

class GroupSelection(BaseModel):
    """@private"""
    exclude: Optional[List[Any]] = None
    select_only: Optional[List[Any]] = Field(alias='selectOnly', default=None)

class GroupSelectionQuery(BaseModel):
    """@private"""
    group_id: str = Field(alias='groupId')
    selection: 'GroupSelection'

class JobArtifactFilter(BaseModel):
    """@private"""
    kinds: List[JobArtifactKind]

class JobInput(BaseModel):
    """@private"""
    recipe: str
    use_case: str = Field(alias='useCase')
    args: Any
    name: Optional[str] = None
    compute_pool: Optional[str] = Field(alias='computePool', default=None)
    num_gpus: int = Field(alias='numGpus')

class JudgeConfigInput(BaseModel):
    """@private"""
    model: str
    criteria: str
    examples: List['JudgeExampleInput']
    system_template: str = Field(alias='systemTemplate')
    user_template: str = Field(alias='userTemplate')

class JudgeCreate(BaseModel):
    """@private"""
    key: Optional[str] = None
    name: str
    criteria: str
    examples: List['JudgeExampleInput'] = Field(default_factory=lambda : [])
    model: str
    metric: Optional[str] = None

class JudgeExampleInput(BaseModel):
    """@private"""
    input: List['JudgeExampleInputTurnEntry']
    reasoning: Optional[str] = None
    output: str
    pass_: bool = Field(alias='pass')
    id: Optional[Any] = None

class JudgeExampleInputTurnEntry(BaseModel):
    """@private"""
    role: str
    content: str

class JudgeUpdate(BaseModel):
    """@private"""
    name: Optional[str] = None
    criteria: Optional[str] = None
    examples: Optional[List['JudgeExampleInput']] = None
    model: Optional[str] = None

class LabelFilter(BaseModel):
    """@private"""
    key: str
    value: Optional[List[str]] = None

class LabelInput(BaseModel):
    """@private"""
    key: str
    value: str

class ListCompletionsFilterInput(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    models: Optional[List[str]] = None
    timerange: Optional['TimeRange'] = None
    session_id: Optional[Any] = Field(alias='sessionId', default=None)
    user_id: Optional[Any] = Field(alias='userId', default=None)
    feedbacks: Optional[List['CompletionFeedbackFilterInput']] = None
    comparisons: Optional[List['CompletionComparisonFilterInput']] = None
    labels: Optional[List['LabelFilter']] = None
    prompt_hash: Optional[str] = Field(alias='promptHash', default=None)
    completion_id: Optional[Any] = Field(alias='completionId', default=None)
    source: Optional[List[CompletionSource]] = None

class ListJobsFilterInput(BaseModel):
    """@private"""
    use_case: Optional[str] = Field(alias='useCase', default=None)
    kind: Optional[List[JobKind]] = None
    status: Optional[List[JobStatus]] = None
    timerange: Optional['TimeRange'] = None
    custom_recipes: Optional[List[str]] = Field(alias='customRecipes', default=None)
    artifacts: Optional['JobArtifactFilter'] = None

class MetricCreate(BaseModel):
    """@private"""
    name: str
    key: Optional[str] = None
    kind: MetricKind
    scoring_type: MetricScoringType = Field(alias='scoringType', default=MetricScoringType.HIGHER_IS_BETTER)
    description: Optional[str] = None
    unit: Optional[str] = None

class MetricGetOrCreate(BaseModel):
    """@private"""
    existing: Optional[str] = None
    new: Optional['MetricCreate'] = None

class MetricLink(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    metric: str

class MetricTrendInput(BaseModel):
    """@private"""
    timerange: Optional['TimeRange'] = None
    aggregation: MetricAggregation = MetricAggregation.AVERAGE

class MetricUnlink(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    metric: str

class ModelComputeConfigInput(BaseModel):
    """@private"""
    tp: Optional[int] = None
    kv_cache_len: Optional[int] = Field(alias='kvCacheLen', default=None)
    max_seq_len: Optional[int] = Field(alias='maxSeqLen', default=None)

class ModelFilter(BaseModel):
    """@private"""
    in_storage: Optional[bool] = Field(alias='inStorage', default=None)
    available: Optional[bool] = None
    trainable: Optional[bool] = None
    kind: Optional[List[ModelKindFilter]] = None
    view_all: Optional[bool] = Field(alias='viewAll', default=None)
    online: Optional[List[ModelOnline]] = None

class ModelPlacementInput(BaseModel):
    """@private"""
    compute_pools: List[str] = Field(alias='computePools')
    max_ttft_ms: Optional[int] = Field(alias='maxTtftMs', default=None)

class ModelProviderDataInput(BaseModel):
    """@private"""
    azure: Optional['AzureProviderDataInput'] = None
    open_ai: Optional['OpenAIProviderDataInput'] = Field(alias='openAI', default=None)
    google: Optional['GoogleProviderDataInput'] = None
    anthropic: Optional['AnthropicProviderDataInput'] = None
    nvidia: Optional['NvidiaProviderDataInput'] = None

class ModelServiceDisconnect(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    model_service: str = Field(alias='modelService')

class ModelServiceFilter(BaseModel):
    """@private"""
    model: Optional[str] = None
    kind: Optional[List[ModelKindFilter]] = None

class NvidiaProviderDataInput(BaseModel):
    """@private"""
    external_model_id: str = Field(alias='externalModelId')
    endpoint: str

class OpenAIProviderDataInput(BaseModel):
    """@private"""
    api_key: str = Field(alias='apiKey')
    external_model_id: OpenAIModel = Field(alias='externalModelId')

class OrderPair(BaseModel):
    """@private"""
    field: str
    order: SortDirection

class PrebuiltConfigInput(BaseModel):
    """@private"""
    key: PrebuiltCriteriaKey
    model: str

class PrebuiltJudgeCreate(BaseModel):
    """@private"""
    key: Optional[str] = None
    name: str
    model: str
    prebuilt_criteria_key: PrebuiltCriteriaKey = Field(alias='prebuiltCriteriaKey')

class RemoteConfigInput(BaseModel):
    """@private"""
    url: str

class RemoteEnvCreate(BaseModel):
    """@private"""
    url: str
    key: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class ResizePartitionInput(BaseModel):
    """@private"""
    harmony_group: str = Field(alias='harmonyGroup')
    size: int

class RoleCreate(BaseModel):
    """@private"""
    key: Optional[str] = None
    name: str
    permissions: List[str]

class SampleConfig(BaseModel):
    """@private"""
    selection_type: SelectionTypeInput = Field(alias='selectionType')
    sample_size: Optional[int] = Field(alias='sampleSize', default=None)

class SystemPromptTemplateCreate(BaseModel):
    """@private"""
    name: str
    template: str

class SystemPromptTemplateUpdate(BaseModel):
    """@private"""
    system_prompt_template: Any = Field(alias='systemPromptTemplate')
    name: Optional[str] = None
    template: str
    update_model_services: bool = Field(alias='updateModelServices', default=False)

class TeamCreate(BaseModel):
    """@private"""
    key: Optional[str] = None
    name: str

class TeamMemberRemove(BaseModel):
    """@private"""
    user: str
    team: str

class TeamMemberSet(BaseModel):
    """@private"""
    user: str
    team: str
    role: str

class TimeRange(BaseModel):
    """@private"""
    from_: int | str = Field(alias='from')
    to: int | str

class TimeseriesInput(BaseModel):
    """@private"""
    interval: TimeseriesInterval
    timerange: Optional['TimeRange'] = None
    timezone: Optional[str] = None
    by_model: bool = Field(alias='byModel', default=False)
    aggregation: MetricAggregation = MetricAggregation.AVERAGE

class UnitConfigInput(BaseModel):
    """@private"""
    symbol: str
    position: UnitPosition

class UpdateCompletion(BaseModel):
    """@private"""
    id: Any
    remove_labels: Optional[List['CompletionLabelValue']] = Field(alias='removeLabels', default=None)
    'remove some label value. This operation is atomic'
    add_labels: Optional[List['CompletionLabelValue']] = Field(alias='addLabels', default=None)
    'add a label value. This operation is atomic'
    set_labels: Optional[List['CompletionLabelValue']] = Field(alias='setLabels', default=None)
    "set the completion labels to this list. If you want to only add or remove specific labels,\nit's better to use `add_labels` or `remove_labels`"
    metadata: Optional[Any] = None
    'set metadata associated with this prompt for use with external reward servers'

class UpdateModelService(BaseModel):
    """@private"""
    use_case: str = Field(alias='useCase')
    model_service: str = Field(alias='modelService')
    is_default: Optional[bool] = Field(alias='isDefault', default=None)
    attached: Optional[bool] = None
    desired_online: Optional[bool] = Field(alias='desiredOnline', default=None)
    name: Optional[str] = None
    system_prompt_template: Optional[Any] = Field(alias='systemPromptTemplate', default=None)
    placement: Optional['ModelPlacementInput'] = None
    tool_providers: Optional[List[str]] = Field(alias='toolProviders', default=None)

class UpdateRecipeInput(BaseModel):
    """@private"""
    name: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[List['LabelInput']] = None

class UpdateToolProviderInput(BaseModel):
    """@private"""
    name: Optional[str] = None
    uri: Optional[str] = None
    protocol: Optional[Protocol] = None

class UsageFilterInput(BaseModel):
    """@private"""
    model_id: Any = Field(alias='modelId')
    timerange: Optional['TimeRange'] = None
    unit: DateBucketUnit
    timezone: Optional[str] = None

class UsagePerUseCaseFilterInput(BaseModel):
    """@private"""
    model_id: Any = Field(alias='modelId')
    timerange: Optional['TimeRange'] = None

class UseCaseCreate(BaseModel):
    """@private"""
    name: str
    team: Optional[str] = None
    key: Optional[str] = None
    description: Optional[str] = None
    gradient_color: Optional[str] = Field(alias='gradientColor', default=None)
    metadata: Optional['UseCaseMetadataInput'] = None
    settings: Optional['UseCaseSettingsInput'] = None

class UseCaseFilter(BaseModel):
    """@private"""
    is_archived: Optional[bool] = Field(alias='isArchived', default=None)

class UseCaseMetadataInput(BaseModel):
    """@private"""
    emoji: Optional['EmojiInput'] = None

class UseCaseSettingsInput(BaseModel):
    """@private"""
    default_metric: Optional[str] = Field(alias='defaultMetric', default=None)

class UseCaseShareInput(BaseModel):
    """@private"""
    team: str
    role: str
    is_owner: bool = Field(alias='isOwner')

class UseCaseShares(BaseModel):
    """@private"""
    shares: List['UseCaseShareInput']

class UseCaseUpdate(BaseModel):
    """@private"""
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[List['WidgetInput']] = None
    metadata: Optional['UseCaseMetadataInput'] = None
    settings: Optional['UseCaseSettingsInput'] = None
    is_archived: Optional[bool] = Field(alias='isArchived', default=None)

class UserCreate(BaseModel):
    """@private"""
    email: str
    name: str
    teams: List['UserCreateTeamWithRole']

class UserCreateTeamWithRole(BaseModel):
    """@private"""
    team: str
    role: str

class WidgetInput(BaseModel):
    """@private"""
    title: str
    metric: str
    aggregation: MetricAggregation
    unit: 'UnitConfigInput'
AddExternalModelInput.model_rebuild()
AttachModel.model_rebuild()
CompletionsByFilters.model_rebuild()
CreateRecipeInput.model_rebuild()
CustomRecipeFilterInput.model_rebuild()
DatasetCompletionQuery.model_rebuild()
DatasetCreateFromFilters.model_rebuild()
FeedbackFilterInput.model_rebuild()
FromGroupsQuery.model_rebuild()
GlobalUsageFilterInput.model_rebuild()
GraderConfigInput.model_rebuild()
GraderCreateInput.model_rebuild()
GraderUpdateInput.model_rebuild()
GroupSelectionQuery.model_rebuild()
JudgeConfigInput.model_rebuild()
JudgeCreate.model_rebuild()
JudgeExampleInput.model_rebuild()
JudgeUpdate.model_rebuild()
ListCompletionsFilterInput.model_rebuild()
ListJobsFilterInput.model_rebuild()
MetricGetOrCreate.model_rebuild()
MetricTrendInput.model_rebuild()
ModelProviderDataInput.model_rebuild()
TimeseriesInput.model_rebuild()
UpdateCompletion.model_rebuild()
UpdateModelService.model_rebuild()
UpdateRecipeInput.model_rebuild()
UsageFilterInput.model_rebuild()
UsagePerUseCaseFilterInput.model_rebuild()
UseCaseCreate.model_rebuild()
UseCaseMetadataInput.model_rebuild()
UseCaseShares.model_rebuild()
UseCaseUpdate.model_rebuild()
UserCreate.model_rebuild()
WidgetInput.model_rebuild()