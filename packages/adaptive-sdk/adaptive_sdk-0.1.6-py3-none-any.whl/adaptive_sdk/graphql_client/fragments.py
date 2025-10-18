from typing import Annotated, Any, List, Literal, Optional, Union
from pydantic import Field
from .base_model import BaseModel
from .enums import AbcampaignStatus, CompletionSource, DatasetKind, FeedbackType, GraderTypeEnum, HarmonyStatus, JobArtifactKind, JobKind, JobStatus, JobStatusOutput, JudgeCapability, MetricKind, MetricScoringType, ModelKindFilter, ModelOnline, PrebuiltCriteriaKey, ProviderName, RemoteEnvStatus

class AbCampaignCreateData(BaseModel):
    """@public"""
    id: Any
    key: str
    status: AbcampaignStatus
    begin_date: int = Field(alias='beginDate')

class MetricData(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    kind: MetricKind
    description: str
    scoring_type: MetricScoringType = Field(alias='scoringType')
    created_at: int = Field(alias='createdAt')
    has_direct_feedbacks: bool = Field(alias='hasDirectFeedbacks')
    has_comparison_feedbacks: bool = Field(alias='hasComparisonFeedbacks')

class AbCampaignDetailData(AbCampaignCreateData):
    """@public"""
    feedback_type: FeedbackType = Field(alias='feedbackType')
    traffic_split: float = Field(alias='trafficSplit')
    end_date: Optional[int] = Field(alias='endDate')
    metric: Optional['AbCampaignDetailDataMetric']
    use_case: Optional['AbCampaignDetailDataUseCase'] = Field(alias='useCase')
    models: List['AbCampaignDetailDataModels']
    feedbacks: int
    has_enough_feedbacks: bool = Field(alias='hasEnoughFeedbacks')

class AbCampaignDetailDataMetric(MetricData):
    """@public"""
    pass

class AbCampaignDetailDataUseCase(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class AbCampaignDetailDataModels(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class AbCampaignReportData(BaseModel):
    """@public"""
    p_value: Optional[float] = Field(alias='pValue')
    variants: List['AbCampaignReportDataVariants']

class AbCampaignReportDataVariants(BaseModel):
    """@public"""
    variant: 'AbCampaignReportDataVariantsVariant'
    interval: Optional['AbCampaignReportDataVariantsInterval']
    feedbacks: int
    comparisons: Optional[List['AbCampaignReportDataVariantsComparisons']]

class AbCampaignReportDataVariantsVariant(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class AbCampaignReportDataVariantsInterval(BaseModel):
    """@public"""
    start: float
    middle: float
    end: float

class AbCampaignReportDataVariantsComparisons(BaseModel):
    """@public"""
    feedbacks: int
    wins: int
    losses: int
    ties_good: int = Field(alias='tiesGood')
    ties_bad: int = Field(alias='tiesBad')
    variant: 'AbCampaignReportDataVariantsComparisonsVariant'

class AbCampaignReportDataVariantsComparisonsVariant(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class CompletionComparisonFeedbackData(BaseModel):
    """@public"""
    id: Any
    completion: Optional[str]
    source: CompletionSource
    model: Optional['CompletionComparisonFeedbackDataModel']

class CompletionComparisonFeedbackDataModel(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class CompletionData(BaseModel):
    """@public"""
    id: Any
    chat_messages: List['CompletionDataChatMessages'] = Field(alias='chatMessages')
    completion: Optional[str]
    source: CompletionSource
    model: Optional['CompletionDataModel']
    direct_feedbacks: List['CompletionDataDirectFeedbacks'] = Field(alias='directFeedbacks')
    comparison_feedbacks: List['CompletionDataComparisonFeedbacks'] = Field(alias='comparisonFeedbacks')
    labels: List['CompletionDataLabels']
    metadata: 'CompletionDataMetadata'
    created_at: int = Field(alias='createdAt')

class CompletionDataChatMessages(BaseModel):
    """@public"""
    role: str
    content: str

class CompletionDataModel(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class CompletionDataDirectFeedbacks(BaseModel):
    """@public"""
    id: Any
    value: float
    metric: Optional['CompletionDataDirectFeedbacksMetric']
    reason: Optional[str]
    details: Optional[str]
    created_at: int = Field(alias='createdAt')

class CompletionDataDirectFeedbacksMetric(MetricData):
    """@public"""
    pass

class CompletionDataComparisonFeedbacks(BaseModel):
    """@public"""
    id: Any
    created_at: int = Field(alias='createdAt')
    usecase: Optional['CompletionDataComparisonFeedbacksUsecase']
    metric: Optional['CompletionDataComparisonFeedbacksMetric']
    prefered_completion: Optional['CompletionDataComparisonFeedbacksPreferedCompletion'] = Field(alias='preferedCompletion')
    other_completion: Optional['CompletionDataComparisonFeedbacksOtherCompletion'] = Field(alias='otherCompletion')

class CompletionDataComparisonFeedbacksUsecase(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class CompletionDataComparisonFeedbacksMetric(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class CompletionDataComparisonFeedbacksPreferedCompletion(CompletionComparisonFeedbackData):
    """@public"""
    pass

class CompletionDataComparisonFeedbacksOtherCompletion(CompletionComparisonFeedbackData):
    """@public"""
    pass

class CompletionDataLabels(BaseModel):
    """@public"""
    key: str
    value: str

class CompletionDataMetadata(BaseModel):
    """@public"""
    parameters: Optional[Any]
    timings: Optional[Any]
    usage: Optional['CompletionDataMetadataUsage']
    system: Optional[Any]

class CompletionDataMetadataUsage(BaseModel):
    """@public"""
    completion_tokens: int = Field(alias='completionTokens')
    prompt_tokens: int = Field(alias='promptTokens')
    total_tokens: int = Field(alias='totalTokens')

class CustomRecipeData(BaseModel):
    """@public"""
    id: Any
    key: Optional[str]
    name: str
    content: str
    content_hash: str = Field(alias='contentHash')
    editable: bool
    global_: bool = Field(alias='global')
    builtin: bool
    input_schema: Any = Field(alias='inputSchema')
    json_schema: Any = Field(alias='jsonSchema')
    description: str
    labels: List['CustomRecipeDataLabels']
    created_at: int = Field(alias='createdAt')
    updated_at: Optional[int] = Field(alias='updatedAt')
    created_by: Optional['CustomRecipeDataCreatedBy'] = Field(alias='createdBy')

class CustomRecipeDataLabels(BaseModel):
    """@public"""
    key: str
    value: str

class CustomRecipeDataCreatedBy(BaseModel):
    """@public"""
    id: Any
    name: str
    email: str

class DatasetData(BaseModel):
    """@public"""
    id: Any
    key: Optional[str]
    name: str
    created_at: Any = Field(alias='createdAt')
    kind: DatasetKind
    records: Optional[int]
    metrics_usage: List['DatasetDataMetricsUsage'] = Field(alias='metricsUsage')

class DatasetDataMetricsUsage(BaseModel):
    """@public"""
    feedback_count: int = Field(alias='feedbackCount')
    comparison_count: int = Field(alias='comparisonCount')
    metric: 'DatasetDataMetricsUsageMetric'

class DatasetDataMetricsUsageMetric(MetricData):
    """@public"""
    pass

class ModelData(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    online: ModelOnline
    is_external: bool = Field(alias='isExternal')
    provider_name: ProviderName = Field(alias='providerName')
    is_adapter: bool = Field(alias='isAdapter')
    is_training: bool = Field(alias='isTraining')
    created_at: int = Field(alias='createdAt')
    kind: ModelKindFilter
    size: Optional[str]
    compute_config: Optional['ModelDataComputeConfig'] = Field(alias='computeConfig')

class ModelDataComputeConfig(BaseModel):
    """@public"""
    tp: int
    kv_cache_len: int = Field(alias='kvCacheLen')
    max_seq_len: int = Field(alias='maxSeqLen')

class GraderData(BaseModel):
    """@public"""
    id: Any
    name: str
    key: str
    locked: bool
    grader_type: GraderTypeEnum = Field(alias='graderType')
    grader_config: Union['GraderDataGraderConfigJudgeConfigOutput', 'GraderDataGraderConfigPrebuiltConfigOutput', 'GraderDataGraderConfigRemoteConfigOutput', 'GraderDataGraderConfigCustomConfigOutput'] = Field(alias='graderConfig', discriminator='typename__')
    use_case: 'GraderDataUseCase' = Field(alias='useCase')
    metric: 'GraderDataMetric'
    created_at: int = Field(alias='createdAt')
    updated_at: int = Field(alias='updatedAt')

class GraderDataGraderConfigJudgeConfigOutput(BaseModel):
    """@public"""
    typename__: Literal['JudgeConfigOutput'] = Field(alias='__typename')
    judge_criteria: str = Field(alias='judgeCriteria')
    examples: List['GraderDataGraderConfigJudgeConfigOutputExamples']
    model: 'GraderDataGraderConfigJudgeConfigOutputModel'

class GraderDataGraderConfigJudgeConfigOutputExamples(BaseModel):
    """@public"""
    input: List['GraderDataGraderConfigJudgeConfigOutputExamplesInput']
    output: str
    pass_: bool = Field(alias='pass')
    reasoning: Optional[str]

class GraderDataGraderConfigJudgeConfigOutputExamplesInput(BaseModel):
    """@public"""
    role: str
    content: str

class GraderDataGraderConfigJudgeConfigOutputModel(ModelData):
    """@public"""
    pass

class GraderDataGraderConfigPrebuiltConfigOutput(BaseModel):
    """@public"""
    typename__: Literal['PrebuiltConfigOutput'] = Field(alias='__typename')
    prebuilt_criteria: 'GraderDataGraderConfigPrebuiltConfigOutputPrebuiltCriteria' = Field(alias='prebuiltCriteria')
    model: 'GraderDataGraderConfigPrebuiltConfigOutputModel'

class GraderDataGraderConfigPrebuiltConfigOutputPrebuiltCriteria(BaseModel):
    """@public"""
    key: PrebuiltCriteriaKey
    name: str
    feedback_key: str = Field(alias='feedbackKey')
    description: str

class GraderDataGraderConfigPrebuiltConfigOutputModel(ModelData):
    """@public"""
    pass

class GraderDataGraderConfigRemoteConfigOutput(BaseModel):
    """@public"""
    typename__: Literal['RemoteConfigOutput'] = Field(alias='__typename')
    url: str
    version: str
    description: str

class GraderDataGraderConfigCustomConfigOutput(BaseModel):
    """@public"""
    typename__: Literal['CustomConfigOutput'] = Field(alias='__typename')
    grader_description: Optional[str] = Field(alias='graderDescription')

class GraderDataUseCase(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class GraderDataMetric(MetricData):
    """@public"""
    pass

class HarmonyGroupData(BaseModel):
    """@public"""
    id: Any
    key: str
    compute_pool: Optional['HarmonyGroupDataComputePool'] = Field(alias='computePool')
    status: HarmonyStatus
    url: str
    world_size: int = Field(alias='worldSize')
    gpu_types: str = Field(alias='gpuTypes')
    created_at: int = Field(alias='createdAt')
    online_models: List['HarmonyGroupDataOnlineModels'] = Field(alias='onlineModels')

class HarmonyGroupDataComputePool(BaseModel):
    """@public"""
    key: str
    name: str

class HarmonyGroupDataOnlineModels(ModelData):
    """@public"""
    pass

class JobData(BaseModel):
    """@public"""
    id: Any
    name: str
    status: JobStatus
    created_at: int = Field(alias='createdAt')
    created_by: Optional['JobDataCreatedBy'] = Field(alias='createdBy')
    started_at: Optional[int] = Field(alias='startedAt')
    ended_at: Optional[int] = Field(alias='endedAt')
    duration_ms: Optional[int] = Field(alias='durationMs')
    progress: float
    error: Optional[str]
    kind: JobKind
    stages: List['JobDataStages']
    use_case: Optional['JobDataUseCase'] = Field(alias='useCase')
    recipe: Optional['JobDataRecipe']
    details: Optional['JobDataDetails']

class JobDataCreatedBy(BaseModel):
    """@public"""
    id: Any
    name: str

class JobDataStages(BaseModel):
    """@public"""
    name: str
    status: JobStatusOutput
    info: Optional[Annotated[Union['JobDataStagesInfoTrainingJobStageOutput', 'JobDataStagesInfoEvalJobStageOutput', 'JobDataStagesInfoBatchInferenceJobStageOutput'], Field(discriminator='typename__')]]

class JobDataStagesInfoTrainingJobStageOutput(BaseModel):
    """@public"""
    typename__: Literal['TrainingJobStageOutput'] = Field(alias='__typename')
    monitoring_link: Optional[str] = Field(alias='monitoringLink')
    total_num_samples: Optional[int] = Field(alias='totalNumSamples')
    processed_num_samples: Optional[int] = Field(alias='processedNumSamples')
    checkpoints: List[str]

class JobDataStagesInfoEvalJobStageOutput(BaseModel):
    """@public"""
    typename__: Literal['EvalJobStageOutput'] = Field(alias='__typename')
    total_num_samples: Optional[int] = Field(alias='totalNumSamples')
    processed_num_samples: Optional[int] = Field(alias='processedNumSamples')

class JobDataStagesInfoBatchInferenceJobStageOutput(BaseModel):
    """@public"""
    typename__: Literal['BatchInferenceJobStageOutput'] = Field(alias='__typename')
    total_num_samples: Optional[int] = Field(alias='totalNumSamples')
    processed_num_samples: Optional[int] = Field(alias='processedNumSamples')

class JobDataUseCase(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class JobDataRecipe(CustomRecipeData):
    """@public"""
    pass

class JobDataDetails(BaseModel):
    """@public"""
    args: Any
    recipe_hash: str = Field(alias='recipeHash')
    artifacts: List['JobDataDetailsArtifacts']

class JobDataDetailsArtifacts(BaseModel):
    """@public"""
    id: Any
    name: str
    kind: JobArtifactKind
    uri: Optional[str]
    metadata: Any
    created_at: int = Field(alias='createdAt')

class JobStageOutputData(BaseModel):
    """@public"""
    name: str
    status: JobStatusOutput
    parent: Optional[str]
    stage_id: int = Field(alias='stageId')
    info: Optional[Annotated[Union['JobStageOutputDataInfoTrainingJobStageOutput', 'JobStageOutputDataInfoEvalJobStageOutput', 'JobStageOutputDataInfoBatchInferenceJobStageOutput'], Field(discriminator='typename__')]]
    started_at: Optional[int] = Field(alias='startedAt')
    ended_at: Optional[int] = Field(alias='endedAt')

class JobStageOutputDataInfoTrainingJobStageOutput(BaseModel):
    """@public"""
    typename__: Literal['TrainingJobStageOutput'] = Field(alias='__typename')
    monitoring_link: Optional[str] = Field(alias='monitoringLink')
    total_num_samples: Optional[int] = Field(alias='totalNumSamples')
    processed_num_samples: Optional[int] = Field(alias='processedNumSamples')
    checkpoints: List[str]

class JobStageOutputDataInfoEvalJobStageOutput(BaseModel):
    """@public"""
    typename__: Literal['EvalJobStageOutput'] = Field(alias='__typename')
    total_num_samples: Optional[int] = Field(alias='totalNumSamples')
    processed_num_samples: Optional[int] = Field(alias='processedNumSamples')
    monitoring_link: Optional[str] = Field(alias='monitoringLink')

class JobStageOutputDataInfoBatchInferenceJobStageOutput(BaseModel):
    """@public"""
    typename__: Literal['BatchInferenceJobStageOutput'] = Field(alias='__typename')
    total_num_samples: Optional[int] = Field(alias='totalNumSamples')
    processed_num_samples: Optional[int] = Field(alias='processedNumSamples')
    monitoring_link: Optional[str] = Field(alias='monitoringLink')

class JudgeData(BaseModel):
    """@public"""
    id: str
    key: str
    version: int
    name: str
    criteria: Optional[str]
    prebuilt: Optional[str]
    examples: Optional[List['JudgeDataExamples']]
    capabilities: List[JudgeCapability]
    model: 'JudgeDataModel'
    use_case_id: Any = Field(alias='useCaseId')
    metric: 'JudgeDataMetric'
    created_at: int = Field(alias='createdAt')
    updated_at: int = Field(alias='updatedAt')

class JudgeDataExamples(BaseModel):
    """@public"""
    input: List['JudgeDataExamplesInput']
    output: str
    pass_: bool = Field(alias='pass')
    reasoning: Optional[str]

class JudgeDataExamplesInput(BaseModel):
    """@public"""
    role: str
    content: str

class JudgeDataModel(ModelData):
    """@public"""
    pass

class JudgeDataMetric(MetricData):
    """@public"""
    pass

class MetricDataAdmin(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    kind: MetricKind
    description: str
    scoring_type: MetricScoringType = Field(alias='scoringType')
    use_cases: List['MetricDataAdminUseCases'] = Field(alias='useCases')
    created_at: int = Field(alias='createdAt')
    has_direct_feedbacks: bool = Field(alias='hasDirectFeedbacks')
    has_comparison_feedbacks: bool = Field(alias='hasComparisonFeedbacks')

class MetricDataAdminUseCases(BaseModel):
    """@public"""
    id: Any
    name: str
    key: str
    description: str

class MetricWithContextData(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    kind: MetricKind
    description: str
    scoring_type: MetricScoringType = Field(alias='scoringType')
    created_at: Any = Field(alias='createdAt')

class ModelDataAdmin(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    online: ModelOnline
    use_cases: List['ModelDataAdminUseCases'] = Field(alias='useCases')
    is_external: bool = Field(alias='isExternal')
    provider_name: ProviderName = Field(alias='providerName')
    is_adapter: bool = Field(alias='isAdapter')
    is_training: bool = Field(alias='isTraining')
    created_at: int = Field(alias='createdAt')
    kind: ModelKindFilter
    size: Optional[str]

class ModelDataAdminUseCases(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str

class ModelServiceData(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    model: 'ModelServiceDataModel'
    attached: bool
    is_default: bool = Field(alias='isDefault')
    desired_online: bool = Field(alias='desiredOnline')
    created_at: int = Field(alias='createdAt')

class ModelServiceDataModel(ModelData):
    """@public"""
    backbone: Optional['ModelServiceDataModelBackbone']

class ModelServiceDataModelBackbone(ModelData):
    """@public"""
    pass

class RemoteEnvData(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    url: str
    description: str
    created_at: int = Field(alias='createdAt')
    version: str
    status: RemoteEnvStatus
    metadata_schema: Optional[Any] = Field(alias='metadataSchema')

class UseCaseData(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    description: str
    created_at: int = Field(alias='createdAt')
    metrics: List['UseCaseDataMetrics']
    model_services: List['UseCaseDataModelServices'] = Field(alias='modelServices')
    permissions: List[str]
    shares: List['UseCaseDataShares']

class UseCaseDataMetrics(MetricWithContextData):
    """@public"""
    pass

class UseCaseDataModelServices(ModelServiceData):
    """@public"""
    pass

class UseCaseDataShares(BaseModel):
    """@public"""
    team: 'UseCaseDataSharesTeam'
    role: 'UseCaseDataSharesRole'
    is_owner: bool = Field(alias='isOwner')

class UseCaseDataSharesTeam(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')

class UseCaseDataSharesRole(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
    permissions: List[str]

class UserData(BaseModel):
    """@public"""
    id: Any
    email: str
    name: str
    created_at: int = Field(alias='createdAt')
    teams: List['UserDataTeams']

class UserDataTeams(BaseModel):
    """@public"""
    team: 'UserDataTeamsTeam'
    role: 'UserDataTeamsRole'

class UserDataTeamsTeam(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')

class UserDataTeamsRole(BaseModel):
    """@public"""
    id: Any
    key: str
    name: str
    created_at: int = Field(alias='createdAt')
    permissions: List[str]
AbCampaignCreateData.model_rebuild()
MetricData.model_rebuild()
AbCampaignDetailData.model_rebuild()
AbCampaignReportData.model_rebuild()
CompletionComparisonFeedbackData.model_rebuild()
CompletionData.model_rebuild()
CustomRecipeData.model_rebuild()
DatasetData.model_rebuild()
ModelData.model_rebuild()
GraderData.model_rebuild()
HarmonyGroupData.model_rebuild()
JobData.model_rebuild()
JobStageOutputData.model_rebuild()
JudgeData.model_rebuild()
MetricDataAdmin.model_rebuild()
MetricWithContextData.model_rebuild()
ModelDataAdmin.model_rebuild()
ModelServiceData.model_rebuild()
RemoteEnvData.model_rebuild()
UseCaseData.model_rebuild()
UserData.model_rebuild()