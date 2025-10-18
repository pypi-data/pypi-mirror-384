from typing import Any, Dict, List, Optional, Union
from .base_operation import GraphQLField
from .custom_typing_fields import AbcampaignGraphQLField, AbReportGraphQLField, AbVariantReportComparisonGraphQLField, AbVariantReportGraphQLField, ActivityGraphQLField, ActivityOutputGraphQLField, ApiKeyGraphQLField, ArtifactByproductsUnion, AuthProviderGraphQLField, BatchInferenceJobStageOutputGraphQLField, BillingUsageGraphQLField, ChatMessageGraphQLField, ComparisonFeedbackGraphQLField, CompletionConnectionGraphQLField, CompletionEdgeGraphQLField, CompletionGraphQLField, CompletionGroupDataConnectionGraphQLField, CompletionGroupDataEdgeGraphQLField, CompletionGroupDataGraphQLField, CompletionGroupFeedbackStatsGraphQLField, CompletionHistoryEntryOuputGraphQLField, CompletionLabelGraphQLField, CompletionMetadataGraphQLField, ComputePoolGraphQLField, ContractGraphQLField, CustomConfigOutputGraphQLField, CustomRecipeGraphQLField, CustomRecipeJobDetailsGraphQLField, DatasetByproductsGraphQLField, DatasetGraphQLField, DatasetMetricUsageGraphQLField, DatasetValidationOutputGraphQLField, DeleteConfirmGraphQLField, DirectFeedbackGraphQLField, EmojiGraphQLField, EvalJobStageOutputGraphQLField, EvaluationByproductsGraphQLField, EvaluationResultGraphQLField, GlobalUsageGraphQLField, GpuAllocationGraphQLField, GraderConfigUnion, GraderGraphQLField, HarmonyGroupGraphQLField, InteractionOutputGraphQLField, IntervalGraphQLField, JobArtifactGraphQLField, JobConnectionGraphQLField, JobEdgeGraphQLField, JobGraphQLField, JobStageInfoOutputUnion, JobStageOutputGraphQLField, JudgeConfigOutputGraphQLField, JudgeExampleGraphQLField, JudgeGraphQLField, LabelGraphQLField, LabelKeyUsageGraphQLField, LabelUsageGraphQLField, LabelValueUsageGraphQLField, MetaObjectGraphQLField, MetricActivityGraphQLField, MetricGraphQLField, MetricWithContextGraphQLField, ModelComputeConfigOutputGraphQLField, ModelGraphQLField, ModelPlacementOutputGraphQLField, ModelServiceGraphQLField, PageInfoGraphQLField, PrebuiltConfigDefinitionGraphQLField, PrebuiltConfigOutputGraphQLField, PrebuiltCriteriaGraphQLField, ProviderListGraphQLField, RemoteConfigOutputGraphQLField, RemoteEnvGraphQLField, RemoteEnvTestOfflineGraphQLField, RemoteEnvTestOnlineGraphQLField, RoleGraphQLField, SessionGraphQLField, SettingsGraphQLField, ShareGraphQLField, SystemPromptTemplateGraphQLField, TeamGraphQLField, TeamMemberGraphQLField, TeamWithroleGraphQLField, TimeseriesGraphQLField, ToolProviderGraphQLField, TrainingJobStageOutputGraphQLField, TrendResultGraphQLField, UnitConfigGraphQLField, UsageAggregateItemGraphQLField, UsageAggregatePerUseCaseItemGraphQLField, UsageGraphQLField, UsageStatsByModelGraphQLField, UsageStatsGraphQLField, UseCaseGraphQLField, UseCaseItemGraphQLField, UseCaseMetadataGraphQLField, UserGraphQLField, WidgetGraphQLField
from .input_types import AbCampaignFilter, CursorPageInput, FeedbackFilterInput, ListCompletionsFilterInput, MetricTrendInput, ModelServiceFilter, OrderPair, TimeRange, TimeseriesInput, UseCaseFilter

class AbReportFields(GraphQLField):
    """@private"""
    p_value: 'AbReportGraphQLField' = AbReportGraphQLField('pValue')

    @classmethod
    def variants(cls) -> 'AbVariantReportFields':
        return AbVariantReportFields('variants')

    def fields(self, *subfields: Union[AbReportGraphQLField, 'AbVariantReportFields']) -> 'AbReportFields':
        """Subfields should come from the AbReportFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'AbReportFields':
        self._alias = alias
        return self

class AbVariantReportFields(GraphQLField):
    """@private"""

    @classmethod
    def variant(cls) -> 'ModelServiceFields':
        return ModelServiceFields('variant')

    @classmethod
    def interval(cls) -> 'IntervalFields':
        return IntervalFields('interval')
    mean: 'AbVariantReportGraphQLField' = AbVariantReportGraphQLField('mean')
    feedbacks: 'AbVariantReportGraphQLField' = AbVariantReportGraphQLField('feedbacks')

    @classmethod
    def comparisons(cls) -> 'AbVariantReportComparisonFields':
        return AbVariantReportComparisonFields('comparisons')

    def fields(self, *subfields: Union[AbVariantReportGraphQLField, 'AbVariantReportComparisonFields', 'IntervalFields', 'ModelServiceFields']) -> 'AbVariantReportFields':
        """Subfields should come from the AbVariantReportFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'AbVariantReportFields':
        self._alias = alias
        return self

class AbVariantReportComparisonFields(GraphQLField):
    """@private"""

    @classmethod
    def variant(cls) -> 'ModelServiceFields':
        return ModelServiceFields('variant')
    feedbacks: 'AbVariantReportComparisonGraphQLField' = AbVariantReportComparisonGraphQLField('feedbacks')
    wins: 'AbVariantReportComparisonGraphQLField' = AbVariantReportComparisonGraphQLField('wins')
    losses: 'AbVariantReportComparisonGraphQLField' = AbVariantReportComparisonGraphQLField('losses')
    ties_good: 'AbVariantReportComparisonGraphQLField' = AbVariantReportComparisonGraphQLField('tiesGood')
    ties_bad: 'AbVariantReportComparisonGraphQLField' = AbVariantReportComparisonGraphQLField('tiesBad')

    def fields(self, *subfields: Union[AbVariantReportComparisonGraphQLField, 'ModelServiceFields']) -> 'AbVariantReportComparisonFields':
        """Subfields should come from the AbVariantReportComparisonFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'AbVariantReportComparisonFields':
        self._alias = alias
        return self

class AbcampaignFields(GraphQLField):
    """@private"""
    id: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('id')
    key: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('key')
    name: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('name')

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')

    @classmethod
    def use_case(cls) -> 'UseCaseFields':
        return UseCaseFields('useCase')
    auto_deploy: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('autoDeploy')
    status: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('status')
    feedback_type: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('feedbackType')
    traffic_split: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('trafficSplit')
    begin_date: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('beginDate')
    end_date: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('endDate')
    created_at: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('createdAt')

    @classmethod
    def report(cls) -> 'AbReportFields':
        return AbReportFields('report')

    @classmethod
    def models(cls) -> 'ModelServiceFields':
        return ModelServiceFields('models')
    feedbacks: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('feedbacks')
    has_enough_feedbacks: 'AbcampaignGraphQLField' = AbcampaignGraphQLField('hasEnoughFeedbacks')

    def fields(self, *subfields: Union[AbcampaignGraphQLField, 'AbReportFields', 'MetricFields', 'ModelServiceFields', 'UseCaseFields']) -> 'AbcampaignFields':
        """Subfields should come from the AbcampaignFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'AbcampaignFields':
        self._alias = alias
        return self

class ActivityFields(GraphQLField):
    """@private"""

    @classmethod
    def interactions(cls) -> 'InteractionOutputFields':
        return InteractionOutputFields('interactions')

    @classmethod
    def feedbacks(cls) -> 'ActivityOutputFields':
        return ActivityOutputFields('feedbacks')

    def fields(self, *subfields: Union[ActivityGraphQLField, 'ActivityOutputFields', 'InteractionOutputFields']) -> 'ActivityFields':
        """Subfields should come from the ActivityFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ActivityFields':
        self._alias = alias
        return self

class ActivityOutputFields(GraphQLField):
    """@private"""
    value: 'ActivityOutputGraphQLField' = ActivityOutputGraphQLField('value')
    trend: 'ActivityOutputGraphQLField' = ActivityOutputGraphQLField('trend')

    def fields(self, *subfields: ActivityOutputGraphQLField) -> 'ActivityOutputFields':
        """Subfields should come from the ActivityOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ActivityOutputFields':
        self._alias = alias
        return self

class ApiKeyFields(GraphQLField):
    """@private"""
    key: 'ApiKeyGraphQLField' = ApiKeyGraphQLField('key')
    created_at: 'ApiKeyGraphQLField' = ApiKeyGraphQLField('createdAt')

    def fields(self, *subfields: ApiKeyGraphQLField) -> 'ApiKeyFields':
        """Subfields should come from the ApiKeyFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ApiKeyFields':
        self._alias = alias
        return self

class AuthProviderFields(GraphQLField):
    """@private"""
    name: 'AuthProviderGraphQLField' = AuthProviderGraphQLField('name')
    key: 'AuthProviderGraphQLField' = AuthProviderGraphQLField('key')
    kind: 'AuthProviderGraphQLField' = AuthProviderGraphQLField('kind')
    login_url: 'AuthProviderGraphQLField' = AuthProviderGraphQLField('loginUrl')

    def fields(self, *subfields: AuthProviderGraphQLField) -> 'AuthProviderFields':
        """Subfields should come from the AuthProviderFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'AuthProviderFields':
        self._alias = alias
        return self

class BatchInferenceJobStageOutputFields(GraphQLField):
    """@private"""
    total_num_samples: 'BatchInferenceJobStageOutputGraphQLField' = BatchInferenceJobStageOutputGraphQLField('totalNumSamples')
    processed_num_samples: 'BatchInferenceJobStageOutputGraphQLField' = BatchInferenceJobStageOutputGraphQLField('processedNumSamples')
    monitoring_link: 'BatchInferenceJobStageOutputGraphQLField' = BatchInferenceJobStageOutputGraphQLField('monitoringLink')

    def fields(self, *subfields: BatchInferenceJobStageOutputGraphQLField) -> 'BatchInferenceJobStageOutputFields':
        """Subfields should come from the BatchInferenceJobStageOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'BatchInferenceJobStageOutputFields':
        self._alias = alias
        return self

class BillingUsageFields(GraphQLField):
    """@private
Report token usage on this billing cycle: from the start of the period until now
Also indicate a projection usage at the end of the period"""
    now: 'BillingUsageGraphQLField' = BillingUsageGraphQLField('now')
    start: 'BillingUsageGraphQLField' = BillingUsageGraphQLField('start')
    end: 'BillingUsageGraphQLField' = BillingUsageGraphQLField('end')

    @classmethod
    def usage(cls) -> 'UsageStatsFields':
        return UsageStatsFields('usage')

    @classmethod
    def projection(cls) -> 'UsageStatsFields':
        """projection of token usage at the end of the billing cycle based on the current usage"""
        return UsageStatsFields('projection')

    def fields(self, *subfields: Union[BillingUsageGraphQLField, 'UsageStatsFields']) -> 'BillingUsageFields':
        """Subfields should come from the BillingUsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'BillingUsageFields':
        self._alias = alias
        return self

class ChatMessageFields(GraphQLField):
    """@private"""
    role: 'ChatMessageGraphQLField' = ChatMessageGraphQLField('role')
    content: 'ChatMessageGraphQLField' = ChatMessageGraphQLField('content')

    def fields(self, *subfields: ChatMessageGraphQLField) -> 'ChatMessageFields':
        """Subfields should come from the ChatMessageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ChatMessageFields':
        self._alias = alias
        return self

class ComparisonFeedbackFields(GraphQLField):
    """@private"""
    id: 'ComparisonFeedbackGraphQLField' = ComparisonFeedbackGraphQLField('id')
    created_at: 'ComparisonFeedbackGraphQLField' = ComparisonFeedbackGraphQLField('createdAt')

    @classmethod
    def usecase(cls) -> 'UseCaseFields':
        return UseCaseFields('usecase')

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')

    @classmethod
    def prefered_completion(cls) -> 'CompletionFields':
        return CompletionFields('preferedCompletion')

    @classmethod
    def other_completion(cls) -> 'CompletionFields':
        return CompletionFields('otherCompletion')

    def fields(self, *subfields: Union[ComparisonFeedbackGraphQLField, 'CompletionFields', 'MetricFields', 'UseCaseFields']) -> 'ComparisonFeedbackFields':
        """Subfields should come from the ComparisonFeedbackFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ComparisonFeedbackFields':
        self._alias = alias
        return self

class CompletionFields(GraphQLField):
    """@private"""
    id: 'CompletionGraphQLField' = CompletionGraphQLField('id')
    prompt_hash: 'CompletionGraphQLField' = CompletionGraphQLField('promptHash')

    @classmethod
    def chat_messages(cls) -> 'ChatMessageFields':
        return ChatMessageFields('chatMessages')

    @classmethod
    def completion(cls, *, max_length: Optional[int]=None) -> 'CompletionGraphQLField':
        arguments: Dict[str, Dict[str, Any]] = {'maxLength': {'type': 'Int', 'value': max_length}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionGraphQLField('completion', arguments=cleared_arguments)
    source: 'CompletionGraphQLField' = CompletionGraphQLField('source')

    @classmethod
    def model_service(cls) -> 'ModelServiceFields':
        return ModelServiceFields('modelService')

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')

    @classmethod
    def direct_feedbacks(cls, *, filter: Optional[FeedbackFilterInput]=None) -> 'DirectFeedbackFields':
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'FeedbackFilterInput', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return DirectFeedbackFields('directFeedbacks', arguments=cleared_arguments)

    @classmethod
    def comparison_feedbacks(cls) -> 'ComparisonFeedbackFields':
        return ComparisonFeedbackFields('comparisonFeedbacks')

    @classmethod
    def session(cls) -> 'SessionFields':
        return SessionFields('session')

    @classmethod
    def history(cls) -> 'CompletionHistoryEntryOuputFields':
        return CompletionHistoryEntryOuputFields('history')

    @classmethod
    def labels(cls, with_protected: bool) -> 'CompletionLabelFields':
        arguments: Dict[str, Dict[str, Any]] = {'withProtected': {'type': 'Boolean!', 'value': with_protected}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionLabelFields('labels', arguments=cleared_arguments)
    created_at: 'CompletionGraphQLField' = CompletionGraphQLField('createdAt')

    @classmethod
    def siblings_count(cls, filter: ListCompletionsFilterInput) -> 'CompletionGraphQLField':
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ListCompletionsFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionGraphQLField('siblingsCount', arguments=cleared_arguments)
    has_user_metadata: 'CompletionGraphQLField' = CompletionGraphQLField('hasUserMetadata')
    user_metadata: 'CompletionGraphQLField' = CompletionGraphQLField('userMetadata')

    @classmethod
    def metadata(cls) -> 'CompletionMetadataFields':
        return CompletionMetadataFields('metadata')
    can_edit: 'CompletionGraphQLField' = CompletionGraphQLField('canEdit')

    def fields(self, *subfields: Union[CompletionGraphQLField, 'ChatMessageFields', 'ComparisonFeedbackFields', 'CompletionHistoryEntryOuputFields', 'CompletionLabelFields', 'CompletionMetadataFields', 'DirectFeedbackFields', 'ModelFields', 'ModelServiceFields', 'SessionFields']) -> 'CompletionFields':
        """Subfields should come from the CompletionFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionFields':
        self._alias = alias
        return self

class CompletionConnectionFields(GraphQLField):
    """@private"""

    @classmethod
    def page_info(cls) -> 'PageInfoFields':
        """Information to aid in pagination."""
        return PageInfoFields('pageInfo')

    @classmethod
    def edges(cls) -> 'CompletionEdgeFields':
        """A list of edges."""
        return CompletionEdgeFields('edges')

    @classmethod
    def nodes(cls) -> 'CompletionFields':
        """A list of nodes."""
        return CompletionFields('nodes')
    total_count: 'CompletionConnectionGraphQLField' = CompletionConnectionGraphQLField('totalCount')

    def fields(self, *subfields: Union[CompletionConnectionGraphQLField, 'CompletionEdgeFields', 'CompletionFields', 'PageInfoFields']) -> 'CompletionConnectionFields':
        """Subfields should come from the CompletionConnectionFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionConnectionFields':
        self._alias = alias
        return self

class CompletionEdgeFields(GraphQLField):
    """@private
An edge in a connection."""

    @classmethod
    def node(cls) -> 'CompletionFields':
        """The item at the end of the edge"""
        return CompletionFields('node')
    cursor: 'CompletionEdgeGraphQLField' = CompletionEdgeGraphQLField('cursor')
    'A cursor for use in pagination'

    def fields(self, *subfields: Union[CompletionEdgeGraphQLField, 'CompletionFields']) -> 'CompletionEdgeFields':
        """Subfields should come from the CompletionEdgeFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionEdgeFields':
        self._alias = alias
        return self

class CompletionGroupDataFields(GraphQLField):
    """@private"""
    key: 'CompletionGroupDataGraphQLField' = CompletionGroupDataGraphQLField('key')
    count: 'CompletionGroupDataGraphQLField' = CompletionGroupDataGraphQLField('count')

    @classmethod
    def direct_feedbacks_stats(cls) -> 'CompletionGroupFeedbackStatsFields':
        return CompletionGroupFeedbackStatsFields('directFeedbacksStats')

    @classmethod
    def completions(cls, page: CursorPageInput, order: List[OrderPair]) -> 'CompletionConnectionFields':
        arguments: Dict[str, Dict[str, Any]] = {'page': {'type': 'CursorPageInput!', 'value': page}, 'order': {'type': '[OrderPair!]!', 'value': order}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionConnectionFields('completions', arguments=cleared_arguments)

    def fields(self, *subfields: Union[CompletionGroupDataGraphQLField, 'CompletionConnectionFields', 'CompletionGroupFeedbackStatsFields']) -> 'CompletionGroupDataFields':
        """Subfields should come from the CompletionGroupDataFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionGroupDataFields':
        self._alias = alias
        return self

class CompletionGroupDataConnectionFields(GraphQLField):
    """@private"""

    @classmethod
    def page_info(cls) -> 'PageInfoFields':
        """Information to aid in pagination."""
        return PageInfoFields('pageInfo')

    @classmethod
    def edges(cls) -> 'CompletionGroupDataEdgeFields':
        """A list of edges."""
        return CompletionGroupDataEdgeFields('edges')

    @classmethod
    def nodes(cls) -> 'CompletionGroupDataFields':
        """A list of nodes."""
        return CompletionGroupDataFields('nodes')
    group_by: 'CompletionGroupDataConnectionGraphQLField' = CompletionGroupDataConnectionGraphQLField('groupBy')
    total_count: 'CompletionGroupDataConnectionGraphQLField' = CompletionGroupDataConnectionGraphQLField('totalCount')

    def fields(self, *subfields: Union[CompletionGroupDataConnectionGraphQLField, 'CompletionGroupDataEdgeFields', 'CompletionGroupDataFields', 'PageInfoFields']) -> 'CompletionGroupDataConnectionFields':
        """Subfields should come from the CompletionGroupDataConnectionFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionGroupDataConnectionFields':
        self._alias = alias
        return self

class CompletionGroupDataEdgeFields(GraphQLField):
    """@private
An edge in a connection."""

    @classmethod
    def node(cls) -> 'CompletionGroupDataFields':
        """The item at the end of the edge"""
        return CompletionGroupDataFields('node')
    cursor: 'CompletionGroupDataEdgeGraphQLField' = CompletionGroupDataEdgeGraphQLField('cursor')
    'A cursor for use in pagination'

    def fields(self, *subfields: Union[CompletionGroupDataEdgeGraphQLField, 'CompletionGroupDataFields']) -> 'CompletionGroupDataEdgeFields':
        """Subfields should come from the CompletionGroupDataEdgeFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionGroupDataEdgeFields':
        self._alias = alias
        return self

class CompletionGroupFeedbackStatsFields(GraphQLField):
    """@private"""

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')
    feedbacks: 'CompletionGroupFeedbackStatsGraphQLField' = CompletionGroupFeedbackStatsGraphQLField('feedbacks')
    average: 'CompletionGroupFeedbackStatsGraphQLField' = CompletionGroupFeedbackStatsGraphQLField('average')
    max: 'CompletionGroupFeedbackStatsGraphQLField' = CompletionGroupFeedbackStatsGraphQLField('max')
    min: 'CompletionGroupFeedbackStatsGraphQLField' = CompletionGroupFeedbackStatsGraphQLField('min')
    stddev: 'CompletionGroupFeedbackStatsGraphQLField' = CompletionGroupFeedbackStatsGraphQLField('stddev')
    sum: 'CompletionGroupFeedbackStatsGraphQLField' = CompletionGroupFeedbackStatsGraphQLField('sum')

    def fields(self, *subfields: Union[CompletionGroupFeedbackStatsGraphQLField, 'MetricFields']) -> 'CompletionGroupFeedbackStatsFields':
        """Subfields should come from the CompletionGroupFeedbackStatsFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionGroupFeedbackStatsFields':
        self._alias = alias
        return self

class CompletionHistoryEntryOuputFields(GraphQLField):
    """@private"""
    level: 'CompletionHistoryEntryOuputGraphQLField' = CompletionHistoryEntryOuputGraphQLField('level')
    completion_id: 'CompletionHistoryEntryOuputGraphQLField' = CompletionHistoryEntryOuputGraphQLField('completionId')
    prompt: 'CompletionHistoryEntryOuputGraphQLField' = CompletionHistoryEntryOuputGraphQLField('prompt')
    completion: 'CompletionHistoryEntryOuputGraphQLField' = CompletionHistoryEntryOuputGraphQLField('completion')
    created_at: 'CompletionHistoryEntryOuputGraphQLField' = CompletionHistoryEntryOuputGraphQLField('createdAt')

    def fields(self, *subfields: CompletionHistoryEntryOuputGraphQLField) -> 'CompletionHistoryEntryOuputFields':
        """Subfields should come from the CompletionHistoryEntryOuputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionHistoryEntryOuputFields':
        self._alias = alias
        return self

class CompletionLabelFields(GraphQLField):
    """@private"""
    key: 'CompletionLabelGraphQLField' = CompletionLabelGraphQLField('key')
    value: 'CompletionLabelGraphQLField' = CompletionLabelGraphQLField('value')

    def fields(self, *subfields: CompletionLabelGraphQLField) -> 'CompletionLabelFields':
        """Subfields should come from the CompletionLabelFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionLabelFields':
        self._alias = alias
        return self

class CompletionMetadataFields(GraphQLField):
    """@private"""
    parameters: 'CompletionMetadataGraphQLField' = CompletionMetadataGraphQLField('parameters')
    timings: 'CompletionMetadataGraphQLField' = CompletionMetadataGraphQLField('timings')
    system: 'CompletionMetadataGraphQLField' = CompletionMetadataGraphQLField('system')

    @classmethod
    def usage(cls) -> 'UsageFields':
        return UsageFields('usage')

    def fields(self, *subfields: Union[CompletionMetadataGraphQLField, 'UsageFields']) -> 'CompletionMetadataFields':
        """Subfields should come from the CompletionMetadataFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CompletionMetadataFields':
        self._alias = alias
        return self

class ComputePoolFields(GraphQLField):
    """@private"""
    id: 'ComputePoolGraphQLField' = ComputePoolGraphQLField('id')
    key: 'ComputePoolGraphQLField' = ComputePoolGraphQLField('key')
    name: 'ComputePoolGraphQLField' = ComputePoolGraphQLField('name')
    created_at: 'ComputePoolGraphQLField' = ComputePoolGraphQLField('createdAt')

    @classmethod
    def all_harmony_groups(cls) -> 'HarmonyGroupFields':
        return HarmonyGroupFields('allHarmonyGroups')

    @classmethod
    def harmony_groups(cls) -> 'HarmonyGroupFields':
        return HarmonyGroupFields('harmonyGroups')
    capabilities: 'ComputePoolGraphQLField' = ComputePoolGraphQLField('capabilities')

    def fields(self, *subfields: Union[ComputePoolGraphQLField, 'HarmonyGroupFields']) -> 'ComputePoolFields':
        """Subfields should come from the ComputePoolFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ComputePoolFields':
        self._alias = alias
        return self

class ContractFields(GraphQLField):
    """@private"""
    quota: 'ContractGraphQLField' = ContractGraphQLField('quota')
    start_date: 'ContractGraphQLField' = ContractGraphQLField('startDate')
    end_date: 'ContractGraphQLField' = ContractGraphQLField('endDate')
    cycle: 'ContractGraphQLField' = ContractGraphQLField('cycle')

    @classmethod
    def usage(cls, *, now: Optional[int | str]=None) -> 'BillingUsageFields':
        """Get token usage on Adaptive models for the current billing cycle
        returns an error if 'now' is before the start date of the contract"""
        arguments: Dict[str, Dict[str, Any]] = {'now': {'type': 'InputDatetime', 'value': now}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return BillingUsageFields('usage', arguments=cleared_arguments)

    def fields(self, *subfields: Union[ContractGraphQLField, 'BillingUsageFields']) -> 'ContractFields':
        """Subfields should come from the ContractFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ContractFields':
        self._alias = alias
        return self

class CustomConfigOutputFields(GraphQLField):
    """@private"""
    description: 'CustomConfigOutputGraphQLField' = CustomConfigOutputGraphQLField('description')

    def fields(self, *subfields: CustomConfigOutputGraphQLField) -> 'CustomConfigOutputFields':
        """Subfields should come from the CustomConfigOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CustomConfigOutputFields':
        self._alias = alias
        return self

class CustomRecipeFields(GraphQLField):
    """@private"""
    id: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('id')
    key: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('key')
    name: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('name')
    editable: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('editable')
    hidden: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('hidden')
    builtin: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('builtin')
    global_: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('global')
    created_at: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('createdAt')
    content: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('content')
    input_schema: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('inputSchema')
    json_schema: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('jsonSchema')
    content_hash: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('contentHash')
    description: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('description')

    @classmethod
    def labels(cls, with_protected: bool) -> 'LabelFields':
        arguments: Dict[str, Dict[str, Any]] = {'withProtected': {'type': 'Boolean!', 'value': with_protected}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return LabelFields('labels', arguments=cleared_arguments)
    updated_at: 'CustomRecipeGraphQLField' = CustomRecipeGraphQLField('updatedAt')

    @classmethod
    def created_by(cls) -> 'UserFields':
        return UserFields('createdBy')

    def fields(self, *subfields: Union[CustomRecipeGraphQLField, 'LabelFields', 'UserFields']) -> 'CustomRecipeFields':
        """Subfields should come from the CustomRecipeFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CustomRecipeFields':
        self._alias = alias
        return self

class CustomRecipeJobDetailsFields(GraphQLField):
    """@private"""
    args: 'CustomRecipeJobDetailsGraphQLField' = CustomRecipeJobDetailsGraphQLField('args')
    recipe_hash: 'CustomRecipeJobDetailsGraphQLField' = CustomRecipeJobDetailsGraphQLField('recipeHash')

    @classmethod
    def artifacts(cls) -> 'JobArtifactFields':
        return JobArtifactFields('artifacts')

    def fields(self, *subfields: Union[CustomRecipeJobDetailsGraphQLField, 'JobArtifactFields']) -> 'CustomRecipeJobDetailsFields':
        """Subfields should come from the CustomRecipeJobDetailsFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'CustomRecipeJobDetailsFields':
        self._alias = alias
        return self

class DatasetFields(GraphQLField):
    """@private"""
    id: 'DatasetGraphQLField' = DatasetGraphQLField('id')
    key: 'DatasetGraphQLField' = DatasetGraphQLField('key')
    name: 'DatasetGraphQLField' = DatasetGraphQLField('name')
    created_at: 'DatasetGraphQLField' = DatasetGraphQLField('createdAt')
    kind: 'DatasetGraphQLField' = DatasetGraphQLField('kind')
    records: 'DatasetGraphQLField' = DatasetGraphQLField('records')

    @classmethod
    def metrics_usage(cls) -> 'DatasetMetricUsageFields':
        return DatasetMetricUsageFields('metricsUsage')
    source: 'DatasetGraphQLField' = DatasetGraphQLField('source')
    deleted: 'DatasetGraphQLField' = DatasetGraphQLField('deleted')

    def fields(self, *subfields: Union[DatasetGraphQLField, 'DatasetMetricUsageFields']) -> 'DatasetFields':
        """Subfields should come from the DatasetFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'DatasetFields':
        self._alias = alias
        return self

class DatasetByproductsFields(GraphQLField):
    """@private"""

    @classmethod
    def dataset(cls) -> 'DatasetFields':
        return DatasetFields('dataset')

    def fields(self, *subfields: Union[DatasetByproductsGraphQLField, 'DatasetFields']) -> 'DatasetByproductsFields':
        """Subfields should come from the DatasetByproductsFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'DatasetByproductsFields':
        self._alias = alias
        return self

class DatasetMetricUsageFields(GraphQLField):
    """@private"""

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')
    feedback_count: 'DatasetMetricUsageGraphQLField' = DatasetMetricUsageGraphQLField('feedbackCount')
    comparison_count: 'DatasetMetricUsageGraphQLField' = DatasetMetricUsageGraphQLField('comparisonCount')

    def fields(self, *subfields: Union[DatasetMetricUsageGraphQLField, 'MetricFields']) -> 'DatasetMetricUsageFields':
        """Subfields should come from the DatasetMetricUsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'DatasetMetricUsageFields':
        self._alias = alias
        return self

class DatasetValidationOutputFields(GraphQLField):
    """@private"""
    valid: 'DatasetValidationOutputGraphQLField' = DatasetValidationOutputGraphQLField('valid')
    message: 'DatasetValidationOutputGraphQLField' = DatasetValidationOutputGraphQLField('message')

    def fields(self, *subfields: DatasetValidationOutputGraphQLField) -> 'DatasetValidationOutputFields':
        """Subfields should come from the DatasetValidationOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'DatasetValidationOutputFields':
        self._alias = alias
        return self

class DeleteConfirmFields(GraphQLField):
    """@private"""
    success: 'DeleteConfirmGraphQLField' = DeleteConfirmGraphQLField('success')
    details: 'DeleteConfirmGraphQLField' = DeleteConfirmGraphQLField('details')

    def fields(self, *subfields: DeleteConfirmGraphQLField) -> 'DeleteConfirmFields':
        """Subfields should come from the DeleteConfirmFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'DeleteConfirmFields':
        self._alias = alias
        return self

class DirectFeedbackFields(GraphQLField):
    """@private"""
    id: 'DirectFeedbackGraphQLField' = DirectFeedbackGraphQLField('id')
    value: 'DirectFeedbackGraphQLField' = DirectFeedbackGraphQLField('value')
    user_id: 'DirectFeedbackGraphQLField' = DirectFeedbackGraphQLField('userId')

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')
    reason: 'DirectFeedbackGraphQLField' = DirectFeedbackGraphQLField('reason')
    details: 'DirectFeedbackGraphQLField' = DirectFeedbackGraphQLField('details')
    created_at: 'DirectFeedbackGraphQLField' = DirectFeedbackGraphQLField('createdAt')

    def fields(self, *subfields: Union[DirectFeedbackGraphQLField, 'MetricFields']) -> 'DirectFeedbackFields':
        """Subfields should come from the DirectFeedbackFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'DirectFeedbackFields':
        self._alias = alias
        return self

class EmojiFields(GraphQLField):
    """@private"""
    native: 'EmojiGraphQLField' = EmojiGraphQLField('native')

    def fields(self, *subfields: EmojiGraphQLField) -> 'EmojiFields':
        """Subfields should come from the EmojiFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'EmojiFields':
        self._alias = alias
        return self

class EvalJobStageOutputFields(GraphQLField):
    """@private"""
    total_num_samples: 'EvalJobStageOutputGraphQLField' = EvalJobStageOutputGraphQLField('totalNumSamples')
    processed_num_samples: 'EvalJobStageOutputGraphQLField' = EvalJobStageOutputGraphQLField('processedNumSamples')
    monitoring_link: 'EvalJobStageOutputGraphQLField' = EvalJobStageOutputGraphQLField('monitoringLink')

    def fields(self, *subfields: EvalJobStageOutputGraphQLField) -> 'EvalJobStageOutputFields':
        """Subfields should come from the EvalJobStageOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'EvalJobStageOutputFields':
        self._alias = alias
        return self

class EvaluationByproductsFields(GraphQLField):
    """@private"""

    @classmethod
    def eval_results(cls) -> 'EvaluationResultFields':
        return EvaluationResultFields('evalResults')

    def fields(self, *subfields: Union[EvaluationByproductsGraphQLField, 'EvaluationResultFields']) -> 'EvaluationByproductsFields':
        """Subfields should come from the EvaluationByproductsFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'EvaluationByproductsFields':
        self._alias = alias
        return self

class EvaluationResultFields(GraphQLField):
    """@private"""

    @classmethod
    def model_service(cls) -> 'ModelServiceFields':
        return ModelServiceFields('modelService')

    @classmethod
    def dataset(cls) -> 'DatasetFields':
        return DatasetFields('dataset')

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')
    mean: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('mean')
    min: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('min')
    max: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('max')
    stddev: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('stddev')
    sum: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('sum')
    count: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('count')
    sum_squared: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('sumSquared')
    job_id: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('jobId')
    artifact_id: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('artifactId')
    feedback_count: 'EvaluationResultGraphQLField' = EvaluationResultGraphQLField('feedbackCount')

    @classmethod
    def judge(cls) -> 'JudgeFields':
        return JudgeFields('judge')

    @classmethod
    def grader(cls) -> 'GraderFields':
        return GraderFields('grader')

    def fields(self, *subfields: Union[EvaluationResultGraphQLField, 'DatasetFields', 'GraderFields', 'JudgeFields', 'MetricFields', 'ModelServiceFields']) -> 'EvaluationResultFields':
        """Subfields should come from the EvaluationResultFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'EvaluationResultFields':
        self._alias = alias
        return self

class GlobalUsageFields(GraphQLField):
    """@private"""

    @classmethod
    def total(cls) -> 'UsageStatsFields':
        return UsageStatsFields('total')

    @classmethod
    def adaptive_models(cls) -> 'UsageStatsFields':
        return UsageStatsFields('adaptiveModels')

    @classmethod
    def external_models(cls) -> 'UsageStatsFields':
        return UsageStatsFields('externalModels')

    @classmethod
    def by_model(cls) -> 'UsageStatsByModelFields':
        return UsageStatsByModelFields('byModel')
    signature: 'GlobalUsageGraphQLField' = GlobalUsageGraphQLField('signature')

    def fields(self, *subfields: Union[GlobalUsageGraphQLField, 'UsageStatsByModelFields', 'UsageStatsFields']) -> 'GlobalUsageFields':
        """Subfields should come from the GlobalUsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'GlobalUsageFields':
        self._alias = alias
        return self

class GpuAllocationFields(GraphQLField):
    """@private"""
    name: 'GpuAllocationGraphQLField' = GpuAllocationGraphQLField('name')
    num_gpus: 'GpuAllocationGraphQLField' = GpuAllocationGraphQLField('numGpus')
    ranks: 'GpuAllocationGraphQLField' = GpuAllocationGraphQLField('ranks')
    created_at: 'GpuAllocationGraphQLField' = GpuAllocationGraphQLField('createdAt')
    user_name: 'GpuAllocationGraphQLField' = GpuAllocationGraphQLField('userName')
    job_id: 'GpuAllocationGraphQLField' = GpuAllocationGraphQLField('jobId')

    def fields(self, *subfields: GpuAllocationGraphQLField) -> 'GpuAllocationFields':
        """Subfields should come from the GpuAllocationFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'GpuAllocationFields':
        self._alias = alias
        return self

class GraderFields(GraphQLField):
    """@private"""
    id: 'GraderGraphQLField' = GraderGraphQLField('id')
    name: 'GraderGraphQLField' = GraderGraphQLField('name')
    key: 'GraderGraphQLField' = GraderGraphQLField('key')
    locked: 'GraderGraphQLField' = GraderGraphQLField('locked')
    grader_type: 'GraderGraphQLField' = GraderGraphQLField('graderType')
    grader_config: 'GraderConfigUnion' = GraderConfigUnion('graderConfig')

    @classmethod
    def use_case(cls) -> 'UseCaseFields':
        return UseCaseFields('useCase')

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')
    created_at: 'GraderGraphQLField' = GraderGraphQLField('createdAt')
    updated_at: 'GraderGraphQLField' = GraderGraphQLField('updatedAt')

    def fields(self, *subfields: Union[GraderGraphQLField, 'GraderConfigUnion', 'MetricFields', 'UseCaseFields']) -> 'GraderFields':
        """Subfields should come from the GraderFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'GraderFields':
        self._alias = alias
        return self

class HarmonyGroupFields(GraphQLField):
    """@private"""
    id: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('id')
    key: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('key')

    @classmethod
    def compute_pool(cls) -> 'ComputePoolFields':
        return ComputePoolFields('computePool')
    status: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('status')
    url: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('url')
    world_size: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('worldSize')
    gpu_total: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('gpuTotal')
    gpu_allocated: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('gpuAllocated')

    @classmethod
    def gpu_allocations(cls) -> 'GpuAllocationFields':
        return GpuAllocationFields('gpuAllocations')
    gpu_types: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('gpuTypes')
    created_at: 'HarmonyGroupGraphQLField' = HarmonyGroupGraphQLField('createdAt')

    @classmethod
    def online_models(cls) -> 'ModelFields':
        return ModelFields('onlineModels')

    def fields(self, *subfields: Union[HarmonyGroupGraphQLField, 'ComputePoolFields', 'GpuAllocationFields', 'ModelFields']) -> 'HarmonyGroupFields':
        """Subfields should come from the HarmonyGroupFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'HarmonyGroupFields':
        self._alias = alias
        return self

class InteractionOutputFields(GraphQLField):
    """@private"""
    value: 'InteractionOutputGraphQLField' = InteractionOutputGraphQLField('value')
    per_second: 'InteractionOutputGraphQLField' = InteractionOutputGraphQLField('perSecond')
    trend: 'InteractionOutputGraphQLField' = InteractionOutputGraphQLField('trend')

    def fields(self, *subfields: InteractionOutputGraphQLField) -> 'InteractionOutputFields':
        """Subfields should come from the InteractionOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'InteractionOutputFields':
        self._alias = alias
        return self

class IntervalFields(GraphQLField):
    """@private"""
    start: 'IntervalGraphQLField' = IntervalGraphQLField('start')
    middle: 'IntervalGraphQLField' = IntervalGraphQLField('middle')
    end: 'IntervalGraphQLField' = IntervalGraphQLField('end')

    def fields(self, *subfields: IntervalGraphQLField) -> 'IntervalFields':
        """Subfields should come from the IntervalFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'IntervalFields':
        self._alias = alias
        return self

class JobFields(GraphQLField):
    """@private"""
    id: 'JobGraphQLField' = JobGraphQLField('id')

    @classmethod
    def use_case(cls) -> 'UseCaseFields':
        return UseCaseFields('useCase')
    name: 'JobGraphQLField' = JobGraphQLField('name')
    status: 'JobGraphQLField' = JobGraphQLField('status')
    created_at: 'JobGraphQLField' = JobGraphQLField('createdAt')

    @classmethod
    def created_by(cls) -> 'UserFields':
        return UserFields('createdBy')
    started_at: 'JobGraphQLField' = JobGraphQLField('startedAt')
    ended_at: 'JobGraphQLField' = JobGraphQLField('endedAt')
    duration_ms: 'JobGraphQLField' = JobGraphQLField('durationMs')

    @classmethod
    def stages(cls) -> 'JobStageOutputFields':
        return JobStageOutputFields('stages')
    progress: 'JobGraphQLField' = JobGraphQLField('progress')
    error: 'JobGraphQLField' = JobGraphQLField('error')
    kind: 'JobGraphQLField' = JobGraphQLField('kind')

    @classmethod
    def recipe(cls) -> 'CustomRecipeFields':
        return CustomRecipeFields('recipe')

    @classmethod
    def details(cls) -> 'CustomRecipeJobDetailsFields':
        return CustomRecipeJobDetailsFields('details')

    def fields(self, *subfields: Union[JobGraphQLField, 'CustomRecipeFields', 'CustomRecipeJobDetailsFields', 'JobStageOutputFields', 'UseCaseFields', 'UserFields']) -> 'JobFields':
        """Subfields should come from the JobFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JobFields':
        self._alias = alias
        return self

class JobArtifactFields(GraphQLField):
    """@private"""
    id: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('id')
    job_id: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('jobId')
    name: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('name')
    kind: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('kind')
    uri: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('uri')
    metadata: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('metadata')
    created_at: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('createdAt')

    @classmethod
    def job(cls) -> 'JobFields':
        return JobFields('job')
    download_url: 'JobArtifactGraphQLField' = JobArtifactGraphQLField('downloadUrl')
    byproducts: 'ArtifactByproductsUnion' = ArtifactByproductsUnion('byproducts')

    def fields(self, *subfields: Union[JobArtifactGraphQLField, 'ArtifactByproductsUnion', 'JobFields']) -> 'JobArtifactFields':
        """Subfields should come from the JobArtifactFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JobArtifactFields':
        self._alias = alias
        return self

class JobConnectionFields(GraphQLField):
    """@private"""

    @classmethod
    def page_info(cls) -> 'PageInfoFields':
        """Information to aid in pagination."""
        return PageInfoFields('pageInfo')

    @classmethod
    def edges(cls) -> 'JobEdgeFields':
        """A list of edges."""
        return JobEdgeFields('edges')

    @classmethod
    def nodes(cls) -> 'JobFields':
        """A list of nodes."""
        return JobFields('nodes')
    total_count: 'JobConnectionGraphQLField' = JobConnectionGraphQLField('totalCount')

    def fields(self, *subfields: Union[JobConnectionGraphQLField, 'JobEdgeFields', 'JobFields', 'PageInfoFields']) -> 'JobConnectionFields':
        """Subfields should come from the JobConnectionFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JobConnectionFields':
        self._alias = alias
        return self

class JobEdgeFields(GraphQLField):
    """@private
An edge in a connection."""

    @classmethod
    def node(cls) -> 'JobFields':
        """The item at the end of the edge"""
        return JobFields('node')
    cursor: 'JobEdgeGraphQLField' = JobEdgeGraphQLField('cursor')
    'A cursor for use in pagination'

    def fields(self, *subfields: Union[JobEdgeGraphQLField, 'JobFields']) -> 'JobEdgeFields':
        """Subfields should come from the JobEdgeFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JobEdgeFields':
        self._alias = alias
        return self

class JobStageOutputFields(GraphQLField):
    """@private"""
    name: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('name')
    status: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('status')
    parent: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('parent')
    stage_id: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('stageId')
    info: 'JobStageInfoOutputUnion' = JobStageInfoOutputUnion('info')
    started_at: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('startedAt')
    ended_at: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('endedAt')
    duration_ms: 'JobStageOutputGraphQLField' = JobStageOutputGraphQLField('durationMs')

    def fields(self, *subfields: Union[JobStageOutputGraphQLField, 'JobStageInfoOutputUnion']) -> 'JobStageOutputFields':
        """Subfields should come from the JobStageOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JobStageOutputFields':
        self._alias = alias
        return self

class JudgeFields(GraphQLField):
    """@private"""
    id: 'JudgeGraphQLField' = JudgeGraphQLField('id')
    key: 'JudgeGraphQLField' = JudgeGraphQLField('key')
    version: 'JudgeGraphQLField' = JudgeGraphQLField('version')
    name: 'JudgeGraphQLField' = JudgeGraphQLField('name')
    criteria: 'JudgeGraphQLField' = JudgeGraphQLField('criteria')
    prebuilt: 'JudgeGraphQLField' = JudgeGraphQLField('prebuilt')

    @classmethod
    def examples(cls) -> 'JudgeExampleFields':
        return JudgeExampleFields('examples')
    capabilities: 'JudgeGraphQLField' = JudgeGraphQLField('capabilities')

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')
    use_case_id: 'JudgeGraphQLField' = JudgeGraphQLField('useCaseId')

    @classmethod
    def metric(cls) -> 'MetricFields':
        return MetricFields('metric')
    created_at: 'JudgeGraphQLField' = JudgeGraphQLField('createdAt')
    updated_at: 'JudgeGraphQLField' = JudgeGraphQLField('updatedAt')

    def fields(self, *subfields: Union[JudgeGraphQLField, 'JudgeExampleFields', 'MetricFields', 'ModelFields']) -> 'JudgeFields':
        """Subfields should come from the JudgeFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JudgeFields':
        self._alias = alias
        return self

class JudgeConfigOutputFields(GraphQLField):
    """@private"""
    criteria: 'JudgeConfigOutputGraphQLField' = JudgeConfigOutputGraphQLField('criteria')

    @classmethod
    def examples(cls) -> 'JudgeExampleFields':
        return JudgeExampleFields('examples')
    system_template: 'JudgeConfigOutputGraphQLField' = JudgeConfigOutputGraphQLField('systemTemplate')
    user_template: 'JudgeConfigOutputGraphQLField' = JudgeConfigOutputGraphQLField('userTemplate')

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')

    def fields(self, *subfields: Union[JudgeConfigOutputGraphQLField, 'JudgeExampleFields', 'ModelFields']) -> 'JudgeConfigOutputFields':
        """Subfields should come from the JudgeConfigOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JudgeConfigOutputFields':
        self._alias = alias
        return self

class JudgeExampleFields(GraphQLField):
    """@private"""

    @classmethod
    def input(cls) -> 'ChatMessageFields':
        return ChatMessageFields('input')
    output: 'JudgeExampleGraphQLField' = JudgeExampleGraphQLField('output')
    pass_: 'JudgeExampleGraphQLField' = JudgeExampleGraphQLField('pass')
    reasoning: 'JudgeExampleGraphQLField' = JudgeExampleGraphQLField('reasoning')

    def fields(self, *subfields: Union[JudgeExampleGraphQLField, 'ChatMessageFields']) -> 'JudgeExampleFields':
        """Subfields should come from the JudgeExampleFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'JudgeExampleFields':
        self._alias = alias
        return self

class LabelFields(GraphQLField):
    """@private"""
    key: 'LabelGraphQLField' = LabelGraphQLField('key')
    value: 'LabelGraphQLField' = LabelGraphQLField('value')

    def fields(self, *subfields: LabelGraphQLField) -> 'LabelFields':
        """Subfields should come from the LabelFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'LabelFields':
        self._alias = alias
        return self

class LabelKeyUsageFields(GraphQLField):
    """@private"""
    key: 'LabelKeyUsageGraphQLField' = LabelKeyUsageGraphQLField('key')
    count: 'LabelKeyUsageGraphQLField' = LabelKeyUsageGraphQLField('count')

    @classmethod
    def values(cls) -> 'LabelValueUsageFields':
        return LabelValueUsageFields('values')
    last_used: 'LabelKeyUsageGraphQLField' = LabelKeyUsageGraphQLField('lastUsed')

    def fields(self, *subfields: Union[LabelKeyUsageGraphQLField, 'LabelValueUsageFields']) -> 'LabelKeyUsageFields':
        """Subfields should come from the LabelKeyUsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'LabelKeyUsageFields':
        self._alias = alias
        return self

class LabelUsageFields(GraphQLField):
    """@private"""

    @classmethod
    def keys(cls) -> 'LabelKeyUsageFields':
        return LabelKeyUsageFields('keys')

    def fields(self, *subfields: Union[LabelUsageGraphQLField, 'LabelKeyUsageFields']) -> 'LabelUsageFields':
        """Subfields should come from the LabelUsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'LabelUsageFields':
        self._alias = alias
        return self

class LabelValueUsageFields(GraphQLField):
    """@private"""
    value: 'LabelValueUsageGraphQLField' = LabelValueUsageGraphQLField('value')
    count: 'LabelValueUsageGraphQLField' = LabelValueUsageGraphQLField('count')
    last_used: 'LabelValueUsageGraphQLField' = LabelValueUsageGraphQLField('lastUsed')

    def fields(self, *subfields: LabelValueUsageGraphQLField) -> 'LabelValueUsageFields':
        """Subfields should come from the LabelValueUsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'LabelValueUsageFields':
        self._alias = alias
        return self

class MetaObjectFields(GraphQLField):
    """@private"""

    @classmethod
    def auth_providers(cls) -> 'ProviderListFields':
        return ProviderListFields('authProviders')

    def fields(self, *subfields: Union[MetaObjectGraphQLField, 'ProviderListFields']) -> 'MetaObjectFields':
        """Subfields should come from the MetaObjectFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'MetaObjectFields':
        self._alias = alias
        return self

class MetricFields(GraphQLField):
    """@private"""
    id: 'MetricGraphQLField' = MetricGraphQLField('id')
    key: 'MetricGraphQLField' = MetricGraphQLField('key')
    name: 'MetricGraphQLField' = MetricGraphQLField('name')
    created_at: 'MetricGraphQLField' = MetricGraphQLField('createdAt')
    kind: 'MetricGraphQLField' = MetricGraphQLField('kind')
    description: 'MetricGraphQLField' = MetricGraphQLField('description')
    scoring_type: 'MetricGraphQLField' = MetricGraphQLField('scoringType')
    unit: 'MetricGraphQLField' = MetricGraphQLField('unit')

    @classmethod
    def use_cases(cls, filter: UseCaseFilter) -> 'UseCaseFields':
        """Return the list of UseCase which use this metric"""
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'UseCaseFilter!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return UseCaseFields('useCases', arguments=cleared_arguments)

    @classmethod
    def activity(cls, *, timerange: Optional[TimeRange]=None) -> 'MetricActivityFields':
        arguments: Dict[str, Dict[str, Any]] = {'timerange': {'type': 'TimeRange', 'value': timerange}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return MetricActivityFields('activity', arguments=cleared_arguments)
    has_direct_feedbacks: 'MetricGraphQLField' = MetricGraphQLField('hasDirectFeedbacks')
    has_comparison_feedbacks: 'MetricGraphQLField' = MetricGraphQLField('hasComparisonFeedbacks')

    def fields(self, *subfields: Union[MetricGraphQLField, 'MetricActivityFields', 'UseCaseFields']) -> 'MetricFields':
        """Subfields should come from the MetricFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'MetricFields':
        self._alias = alias
        return self

class MetricActivityFields(GraphQLField):
    """@private"""

    @classmethod
    def feedbacks(cls) -> 'ActivityOutputFields':
        return ActivityOutputFields('feedbacks')

    def fields(self, *subfields: Union[MetricActivityGraphQLField, 'ActivityOutputFields']) -> 'MetricActivityFields':
        """Subfields should come from the MetricActivityFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'MetricActivityFields':
        self._alias = alias
        return self

class MetricWithContextFields(GraphQLField):
    """@private"""
    id: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('id')
    key: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('key')
    name: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('name')
    kind: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('kind')
    scoring_type: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('scoringType')
    description: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('description')
    created_at: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('createdAt')
    unit: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('unit')

    @classmethod
    def feedback_count(cls, *, timerange: Optional[TimeRange]=None) -> 'MetricWithContextGraphQLField':
        arguments: Dict[str, Dict[str, Any]] = {'timerange': {'type': 'TimeRange', 'value': timerange}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return MetricWithContextGraphQLField('feedbackCount', arguments=cleared_arguments)

    @classmethod
    def comparison_count(cls, *, timerange: Optional[TimeRange]=None) -> 'MetricWithContextGraphQLField':
        arguments: Dict[str, Dict[str, Any]] = {'timerange': {'type': 'TimeRange', 'value': timerange}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return MetricWithContextGraphQLField('comparisonCount', arguments=cleared_arguments)

    @classmethod
    def trend(cls, input: MetricTrendInput) -> 'TrendResultFields':
        arguments: Dict[str, Dict[str, Any]] = {'input': {'type': 'MetricTrendInput!', 'value': input}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return TrendResultFields('trend', arguments=cleared_arguments)

    @classmethod
    def timeseries(cls, input: TimeseriesInput) -> 'TimeseriesFields':
        arguments: Dict[str, Dict[str, Any]] = {'input': {'type': 'TimeseriesInput!', 'value': input}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return TimeseriesFields('timeseries', arguments=cleared_arguments)
    has_comparison_feedbacks: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('hasComparisonFeedbacks')
    has_direct_feedbacks: 'MetricWithContextGraphQLField' = MetricWithContextGraphQLField('hasDirectFeedbacks')

    def fields(self, *subfields: Union[MetricWithContextGraphQLField, 'TimeseriesFields', 'TrendResultFields']) -> 'MetricWithContextFields':
        """Subfields should come from the MetricWithContextFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'MetricWithContextFields':
        self._alias = alias
        return self

class ModelFields(GraphQLField):
    """@private"""
    id: 'ModelGraphQLField' = ModelGraphQLField('id')
    name: 'ModelGraphQLField' = ModelGraphQLField('name')
    key: 'ModelGraphQLField' = ModelGraphQLField('key')
    created_at: 'ModelGraphQLField' = ModelGraphQLField('createdAt')
    online: 'ModelGraphQLField' = ModelGraphQLField('online')
    'indicates if this model is spawned in mangrove or not'
    error: 'ModelGraphQLField' = ModelGraphQLField('error')

    @classmethod
    def activity(cls, *, timerange: Optional[TimeRange]=None) -> 'ActivityFields':
        arguments: Dict[str, Dict[str, Any]] = {'timerange': {'type': 'TimeRange', 'value': timerange}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ActivityFields('activity', arguments=cleared_arguments)

    @classmethod
    def metrics(cls) -> 'MetricWithContextFields':
        return MetricWithContextFields('metrics')

    @classmethod
    def use_cases(cls, filter: UseCaseFilter, attached: bool) -> 'UseCaseFields':
        """Return the list of UseCase which use this model"""
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'UseCaseFilter!', 'value': filter}, 'attached': {'type': 'Boolean!', 'value': attached}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return UseCaseFields('useCases', arguments=cleared_arguments)

    @classmethod
    def model_services(cls, filter: UseCaseFilter, attached: bool) -> 'ModelServiceFields':
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'UseCaseFilter!', 'value': filter}, 'attached': {'type': 'Boolean!', 'value': attached}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ModelServiceFields('modelServices', arguments=cleared_arguments)
    provider_name: 'ModelGraphQLField' = ModelGraphQLField('providerName')
    is_external: 'ModelGraphQLField' = ModelGraphQLField('isExternal')
    order: 'ModelGraphQLField' = ModelGraphQLField('order')
    in_storage: 'ModelGraphQLField' = ModelGraphQLField('inStorage')
    is_adapter: 'ModelGraphQLField' = ModelGraphQLField('isAdapter')

    @classmethod
    def backbone(cls) -> 'ModelFields':
        return ModelFields('backbone')
    is_training: 'ModelGraphQLField' = ModelGraphQLField('isTraining')
    'indicates if a training is pending or running for this model'
    kind: 'ModelGraphQLField' = ModelGraphQLField('kind')
    size: 'ModelGraphQLField' = ModelGraphQLField('size')

    @classmethod
    def compute_config(cls) -> 'ModelComputeConfigOutputFields':
        return ModelComputeConfigOutputFields('computeConfig')

    def fields(self, *subfields: Union[ModelGraphQLField, 'ActivityFields', 'MetricWithContextFields', 'ModelComputeConfigOutputFields', 'ModelFields', 'ModelServiceFields', 'UseCaseFields']) -> 'ModelFields':
        """Subfields should come from the ModelFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ModelFields':
        self._alias = alias
        return self

class ModelComputeConfigOutputFields(GraphQLField):
    """@private"""
    tp: 'ModelComputeConfigOutputGraphQLField' = ModelComputeConfigOutputGraphQLField('tp')
    kv_cache_len: 'ModelComputeConfigOutputGraphQLField' = ModelComputeConfigOutputGraphQLField('kvCacheLen')
    max_seq_len: 'ModelComputeConfigOutputGraphQLField' = ModelComputeConfigOutputGraphQLField('maxSeqLen')

    def fields(self, *subfields: ModelComputeConfigOutputGraphQLField) -> 'ModelComputeConfigOutputFields':
        """Subfields should come from the ModelComputeConfigOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ModelComputeConfigOutputFields':
        self._alias = alias
        return self

class ModelPlacementOutputFields(GraphQLField):
    """@private"""
    compute_pools: 'ModelPlacementOutputGraphQLField' = ModelPlacementOutputGraphQLField('computePools')
    max_ttft_ms: 'ModelPlacementOutputGraphQLField' = ModelPlacementOutputGraphQLField('maxTtftMs')

    def fields(self, *subfields: ModelPlacementOutputGraphQLField) -> 'ModelPlacementOutputFields':
        """Subfields should come from the ModelPlacementOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ModelPlacementOutputFields':
        self._alias = alias
        return self

class ModelServiceFields(GraphQLField):
    """@private"""
    status: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('status')
    error: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('error')
    id: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('id')
    use_case_id: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('useCaseId')
    key: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('key')
    name: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('name')
    created_at: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('createdAt')

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')
    attached: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('attached')
    is_default: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('isDefault')
    desired_online: 'ModelServiceGraphQLField' = ModelServiceGraphQLField('desiredOnline')

    @classmethod
    def activity(cls, *, timerange: Optional[TimeRange]=None) -> 'ActivityFields':
        arguments: Dict[str, Dict[str, Any]] = {'timerange': {'type': 'TimeRange', 'value': timerange}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ActivityFields('activity', arguments=cleared_arguments)

    @classmethod
    def system_prompt_template(cls) -> 'SystemPromptTemplateFields':
        return SystemPromptTemplateFields('systemPromptTemplate')

    @classmethod
    def metrics(cls) -> 'MetricWithContextFields':
        return MetricWithContextFields('metrics')

    @classmethod
    def ab_campaigns(cls, filter: AbCampaignFilter) -> 'AbcampaignFields':
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'AbCampaignFilter!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return AbcampaignFields('abCampaigns', arguments=cleared_arguments)

    @classmethod
    def placement(cls) -> 'ModelPlacementOutputFields':
        return ModelPlacementOutputFields('placement')

    @classmethod
    def tool_providers(cls) -> 'ToolProviderFields':
        return ToolProviderFields('toolProviders')

    def fields(self, *subfields: Union[ModelServiceGraphQLField, 'AbcampaignFields', 'ActivityFields', 'MetricWithContextFields', 'ModelFields', 'ModelPlacementOutputFields', 'SystemPromptTemplateFields', 'ToolProviderFields']) -> 'ModelServiceFields':
        """Subfields should come from the ModelServiceFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ModelServiceFields':
        self._alias = alias
        return self

class PageInfoFields(GraphQLField):
    """@private
Information about pagination in a connection"""
    has_previous_page: 'PageInfoGraphQLField' = PageInfoGraphQLField('hasPreviousPage')
    'When paginating backwards, are there more items?'
    has_next_page: 'PageInfoGraphQLField' = PageInfoGraphQLField('hasNextPage')
    'When paginating forwards, are there more items?'
    start_cursor: 'PageInfoGraphQLField' = PageInfoGraphQLField('startCursor')
    'When paginating backwards, the cursor to continue.'
    end_cursor: 'PageInfoGraphQLField' = PageInfoGraphQLField('endCursor')
    'When paginating forwards, the cursor to continue.'

    def fields(self, *subfields: PageInfoGraphQLField) -> 'PageInfoFields':
        """Subfields should come from the PageInfoFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'PageInfoFields':
        self._alias = alias
        return self

class PrebuiltConfigDefinitionFields(GraphQLField):
    """@private"""
    key: 'PrebuiltConfigDefinitionGraphQLField' = PrebuiltConfigDefinitionGraphQLField('key')
    name: 'PrebuiltConfigDefinitionGraphQLField' = PrebuiltConfigDefinitionGraphQLField('name')
    feedback_key: 'PrebuiltConfigDefinitionGraphQLField' = PrebuiltConfigDefinitionGraphQLField('feedbackKey')
    description: 'PrebuiltConfigDefinitionGraphQLField' = PrebuiltConfigDefinitionGraphQLField('description')

    def fields(self, *subfields: PrebuiltConfigDefinitionGraphQLField) -> 'PrebuiltConfigDefinitionFields':
        """Subfields should come from the PrebuiltConfigDefinitionFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'PrebuiltConfigDefinitionFields':
        self._alias = alias
        return self

class PrebuiltConfigOutputFields(GraphQLField):
    """@private"""

    @classmethod
    def criteria(cls) -> 'PrebuiltConfigDefinitionFields':
        return PrebuiltConfigDefinitionFields('criteria')

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')

    def fields(self, *subfields: Union[PrebuiltConfigOutputGraphQLField, 'ModelFields', 'PrebuiltConfigDefinitionFields']) -> 'PrebuiltConfigOutputFields':
        """Subfields should come from the PrebuiltConfigOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'PrebuiltConfigOutputFields':
        self._alias = alias
        return self

class PrebuiltCriteriaFields(GraphQLField):
    """@private"""
    key: 'PrebuiltCriteriaGraphQLField' = PrebuiltCriteriaGraphQLField('key')
    name: 'PrebuiltCriteriaGraphQLField' = PrebuiltCriteriaGraphQLField('name')

    @classmethod
    def feedback(cls) -> 'MetricFields':
        return MetricFields('feedback')
    description: 'PrebuiltCriteriaGraphQLField' = PrebuiltCriteriaGraphQLField('description')

    def fields(self, *subfields: Union[PrebuiltCriteriaGraphQLField, 'MetricFields']) -> 'PrebuiltCriteriaFields':
        """Subfields should come from the PrebuiltCriteriaFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'PrebuiltCriteriaFields':
        self._alias = alias
        return self

class ProviderListFields(GraphQLField):
    """@private"""

    @classmethod
    def providers(cls) -> 'AuthProviderFields':
        return AuthProviderFields('providers')

    def fields(self, *subfields: Union[ProviderListGraphQLField, 'AuthProviderFields']) -> 'ProviderListFields':
        """Subfields should come from the ProviderListFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ProviderListFields':
        self._alias = alias
        return self

class RemoteConfigOutputFields(GraphQLField):
    """@private"""
    url: 'RemoteConfigOutputGraphQLField' = RemoteConfigOutputGraphQLField('url')
    version: 'RemoteConfigOutputGraphQLField' = RemoteConfigOutputGraphQLField('version')
    description: 'RemoteConfigOutputGraphQLField' = RemoteConfigOutputGraphQLField('description')

    def fields(self, *subfields: RemoteConfigOutputGraphQLField) -> 'RemoteConfigOutputFields':
        """Subfields should come from the RemoteConfigOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'RemoteConfigOutputFields':
        self._alias = alias
        return self

class RemoteEnvFields(GraphQLField):
    """@private"""
    id: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('id')
    key: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('key')
    name: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('name')
    url: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('url')
    description: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('description')
    created_at: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('createdAt')
    version: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('version')
    status: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('status')
    metadata_schema: 'RemoteEnvGraphQLField' = RemoteEnvGraphQLField('metadataSchema')

    def fields(self, *subfields: RemoteEnvGraphQLField) -> 'RemoteEnvFields':
        """Subfields should come from the RemoteEnvFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'RemoteEnvFields':
        self._alias = alias
        return self

class RemoteEnvTestOfflineFields(GraphQLField):
    """@private"""
    error: 'RemoteEnvTestOfflineGraphQLField' = RemoteEnvTestOfflineGraphQLField('error')

    def fields(self, *subfields: RemoteEnvTestOfflineGraphQLField) -> 'RemoteEnvTestOfflineFields':
        """Subfields should come from the RemoteEnvTestOfflineFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'RemoteEnvTestOfflineFields':
        self._alias = alias
        return self

class RemoteEnvTestOnlineFields(GraphQLField):
    """@private"""
    name: 'RemoteEnvTestOnlineGraphQLField' = RemoteEnvTestOnlineGraphQLField('name')
    version: 'RemoteEnvTestOnlineGraphQLField' = RemoteEnvTestOnlineGraphQLField('version')
    description: 'RemoteEnvTestOnlineGraphQLField' = RemoteEnvTestOnlineGraphQLField('description')

    def fields(self, *subfields: RemoteEnvTestOnlineGraphQLField) -> 'RemoteEnvTestOnlineFields':
        """Subfields should come from the RemoteEnvTestOnlineFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'RemoteEnvTestOnlineFields':
        self._alias = alias
        return self

class RoleFields(GraphQLField):
    """@private"""
    id: 'RoleGraphQLField' = RoleGraphQLField('id')
    key: 'RoleGraphQLField' = RoleGraphQLField('key')
    name: 'RoleGraphQLField' = RoleGraphQLField('name')
    created_at: 'RoleGraphQLField' = RoleGraphQLField('createdAt')
    permissions: 'RoleGraphQLField' = RoleGraphQLField('permissions')

    def fields(self, *subfields: RoleGraphQLField) -> 'RoleFields':
        """Subfields should come from the RoleFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'RoleFields':
        self._alias = alias
        return self

class SessionFields(GraphQLField):
    """@private"""
    id: 'SessionGraphQLField' = SessionGraphQLField('id')

    @classmethod
    def turns(cls) -> 'CompletionFields':
        return CompletionFields('turns')

    def fields(self, *subfields: Union[SessionGraphQLField, 'CompletionFields']) -> 'SessionFields':
        """Subfields should come from the SessionFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'SessionFields':
        self._alias = alias
        return self

class SettingsFields(GraphQLField):
    """@private"""

    @classmethod
    def default_metric(cls) -> 'MetricWithContextFields':
        return MetricWithContextFields('defaultMetric')

    def fields(self, *subfields: Union[SettingsGraphQLField, 'MetricWithContextFields']) -> 'SettingsFields':
        """Subfields should come from the SettingsFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'SettingsFields':
        self._alias = alias
        return self

class ShareFields(GraphQLField):
    """@private"""

    @classmethod
    def team(cls) -> 'TeamFields':
        return TeamFields('team')

    @classmethod
    def role(cls) -> 'RoleFields':
        return RoleFields('role')
    is_owner: 'ShareGraphQLField' = ShareGraphQLField('isOwner')

    def fields(self, *subfields: Union[ShareGraphQLField, 'RoleFields', 'TeamFields']) -> 'ShareFields':
        """Subfields should come from the ShareFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ShareFields':
        self._alias = alias
        return self

class SystemPromptTemplateFields(GraphQLField):
    """@private"""
    id: 'SystemPromptTemplateGraphQLField' = SystemPromptTemplateGraphQLField('id')
    name: 'SystemPromptTemplateGraphQLField' = SystemPromptTemplateGraphQLField('name')
    template: 'SystemPromptTemplateGraphQLField' = SystemPromptTemplateGraphQLField('template')
    arguments: 'SystemPromptTemplateGraphQLField' = SystemPromptTemplateGraphQLField('arguments')
    created_at: 'SystemPromptTemplateGraphQLField' = SystemPromptTemplateGraphQLField('createdAt')
    created_by: 'SystemPromptTemplateGraphQLField' = SystemPromptTemplateGraphQLField('createdBy')

    def fields(self, *subfields: SystemPromptTemplateGraphQLField) -> 'SystemPromptTemplateFields':
        """Subfields should come from the SystemPromptTemplateFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'SystemPromptTemplateFields':
        self._alias = alias
        return self

class TeamFields(GraphQLField):
    """@private"""
    id: 'TeamGraphQLField' = TeamGraphQLField('id')
    key: 'TeamGraphQLField' = TeamGraphQLField('key')
    name: 'TeamGraphQLField' = TeamGraphQLField('name')
    created_at: 'TeamGraphQLField' = TeamGraphQLField('createdAt')

    def fields(self, *subfields: TeamGraphQLField) -> 'TeamFields':
        """Subfields should come from the TeamFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'TeamFields':
        self._alias = alias
        return self

class TeamMemberFields(GraphQLField):
    """@private"""

    @classmethod
    def user(cls) -> 'UserFields':
        return UserFields('user')

    @classmethod
    def team(cls) -> 'TeamFields':
        return TeamFields('team')

    @classmethod
    def role(cls) -> 'RoleFields':
        return RoleFields('role')

    def fields(self, *subfields: Union[TeamMemberGraphQLField, 'RoleFields', 'TeamFields', 'UserFields']) -> 'TeamMemberFields':
        """Subfields should come from the TeamMemberFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'TeamMemberFields':
        self._alias = alias
        return self

class TeamWithroleFields(GraphQLField):
    """@private"""

    @classmethod
    def team(cls) -> 'TeamFields':
        return TeamFields('team')

    @classmethod
    def role(cls) -> 'RoleFields':
        return RoleFields('role')

    def fields(self, *subfields: Union[TeamWithroleGraphQLField, 'RoleFields', 'TeamFields']) -> 'TeamWithroleFields':
        """Subfields should come from the TeamWithroleFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'TeamWithroleFields':
        self._alias = alias
        return self

class TimeseriesFields(GraphQLField):
    """@private"""

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')
    time_buckets: 'TimeseriesGraphQLField' = TimeseriesGraphQLField('timeBuckets')
    count: 'TimeseriesGraphQLField' = TimeseriesGraphQLField('count')
    values: 'TimeseriesGraphQLField' = TimeseriesGraphQLField('values')
    aggregation: 'TimeseriesGraphQLField' = TimeseriesGraphQLField('aggregation')

    def fields(self, *subfields: Union[TimeseriesGraphQLField, 'ModelFields']) -> 'TimeseriesFields':
        """Subfields should come from the TimeseriesFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'TimeseriesFields':
        self._alias = alias
        return self

class ToolProviderFields(GraphQLField):
    """@private"""
    id: 'ToolProviderGraphQLField' = ToolProviderGraphQLField('id')
    key: 'ToolProviderGraphQLField' = ToolProviderGraphQLField('key')
    name: 'ToolProviderGraphQLField' = ToolProviderGraphQLField('name')
    created_at: 'ToolProviderGraphQLField' = ToolProviderGraphQLField('createdAt')
    uri: 'ToolProviderGraphQLField' = ToolProviderGraphQLField('uri')
    protocol: 'ToolProviderGraphQLField' = ToolProviderGraphQLField('protocol')

    def fields(self, *subfields: ToolProviderGraphQLField) -> 'ToolProviderFields':
        """Subfields should come from the ToolProviderFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'ToolProviderFields':
        self._alias = alias
        return self

class TrainingJobStageOutputFields(GraphQLField):
    """@private"""
    monitoring_link: 'TrainingJobStageOutputGraphQLField' = TrainingJobStageOutputGraphQLField('monitoringLink')
    total_num_samples: 'TrainingJobStageOutputGraphQLField' = TrainingJobStageOutputGraphQLField('totalNumSamples')
    processed_num_samples: 'TrainingJobStageOutputGraphQLField' = TrainingJobStageOutputGraphQLField('processedNumSamples')
    checkpoints: 'TrainingJobStageOutputGraphQLField' = TrainingJobStageOutputGraphQLField('checkpoints')

    def fields(self, *subfields: TrainingJobStageOutputGraphQLField) -> 'TrainingJobStageOutputFields':
        """Subfields should come from the TrainingJobStageOutputFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'TrainingJobStageOutputFields':
        self._alias = alias
        return self

class TrendResultFields(GraphQLField):
    """@private"""
    trend: 'TrendResultGraphQLField' = TrendResultGraphQLField('trend')
    previous: 'TrendResultGraphQLField' = TrendResultGraphQLField('previous')
    current: 'TrendResultGraphQLField' = TrendResultGraphQLField('current')

    def fields(self, *subfields: TrendResultGraphQLField) -> 'TrendResultFields':
        """Subfields should come from the TrendResultFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'TrendResultFields':
        self._alias = alias
        return self

class UnitConfigFields(GraphQLField):
    """@private"""
    symbol: 'UnitConfigGraphQLField' = UnitConfigGraphQLField('symbol')
    position: 'UnitConfigGraphQLField' = UnitConfigGraphQLField('position')

    def fields(self, *subfields: UnitConfigGraphQLField) -> 'UnitConfigFields':
        """Subfields should come from the UnitConfigFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UnitConfigFields':
        self._alias = alias
        return self

class UsageFields(GraphQLField):
    """@private"""
    completion_tokens: 'UsageGraphQLField' = UsageGraphQLField('completionTokens')
    prompt_tokens: 'UsageGraphQLField' = UsageGraphQLField('promptTokens')
    total_tokens: 'UsageGraphQLField' = UsageGraphQLField('totalTokens')

    def fields(self, *subfields: UsageGraphQLField) -> 'UsageFields':
        """Subfields should come from the UsageFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UsageFields':
        self._alias = alias
        return self

class UsageAggregateItemFields(GraphQLField):
    """@private"""
    bucket_ts: 'UsageAggregateItemGraphQLField' = UsageAggregateItemGraphQLField('bucketTs')
    prompt_tokens: 'UsageAggregateItemGraphQLField' = UsageAggregateItemGraphQLField('promptTokens')
    completion_tokens: 'UsageAggregateItemGraphQLField' = UsageAggregateItemGraphQLField('completionTokens')
    total_tokens: 'UsageAggregateItemGraphQLField' = UsageAggregateItemGraphQLField('totalTokens')
    interactions: 'UsageAggregateItemGraphQLField' = UsageAggregateItemGraphQLField('interactions')

    def fields(self, *subfields: UsageAggregateItemGraphQLField) -> 'UsageAggregateItemFields':
        """Subfields should come from the UsageAggregateItemFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UsageAggregateItemFields':
        self._alias = alias
        return self

class UsageAggregatePerUseCaseItemFields(GraphQLField):
    """@private"""

    @classmethod
    def use_case(cls) -> 'UseCaseItemFields':
        return UseCaseItemFields('useCase')

    @classmethod
    def model_service(cls) -> 'ModelServiceFields':
        return ModelServiceFields('modelService')
    prompt_tokens: 'UsageAggregatePerUseCaseItemGraphQLField' = UsageAggregatePerUseCaseItemGraphQLField('promptTokens')
    completion_tokens: 'UsageAggregatePerUseCaseItemGraphQLField' = UsageAggregatePerUseCaseItemGraphQLField('completionTokens')
    total_tokens: 'UsageAggregatePerUseCaseItemGraphQLField' = UsageAggregatePerUseCaseItemGraphQLField('totalTokens')
    interactions: 'UsageAggregatePerUseCaseItemGraphQLField' = UsageAggregatePerUseCaseItemGraphQLField('interactions')

    def fields(self, *subfields: Union[UsageAggregatePerUseCaseItemGraphQLField, 'ModelServiceFields', 'UseCaseItemFields']) -> 'UsageAggregatePerUseCaseItemFields':
        """Subfields should come from the UsageAggregatePerUseCaseItemFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UsageAggregatePerUseCaseItemFields':
        self._alias = alias
        return self

class UsageStatsFields(GraphQLField):
    """@private"""
    total_tokens: 'UsageStatsGraphQLField' = UsageStatsGraphQLField('totalTokens')
    interactions: 'UsageStatsGraphQLField' = UsageStatsGraphQLField('interactions')
    prompt_tokens: 'UsageStatsGraphQLField' = UsageStatsGraphQLField('promptTokens')
    completion_tokens: 'UsageStatsGraphQLField' = UsageStatsGraphQLField('completionTokens')

    def fields(self, *subfields: UsageStatsGraphQLField) -> 'UsageStatsFields':
        """Subfields should come from the UsageStatsFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UsageStatsFields':
        self._alias = alias
        return self

class UsageStatsByModelFields(GraphQLField):
    """@private"""

    @classmethod
    def model(cls) -> 'ModelFields':
        return ModelFields('model')
    total_tokens: 'UsageStatsByModelGraphQLField' = UsageStatsByModelGraphQLField('totalTokens')
    interactions: 'UsageStatsByModelGraphQLField' = UsageStatsByModelGraphQLField('interactions')
    prompt_tokens: 'UsageStatsByModelGraphQLField' = UsageStatsByModelGraphQLField('promptTokens')
    completion_tokens: 'UsageStatsByModelGraphQLField' = UsageStatsByModelGraphQLField('completionTokens')

    @classmethod
    def timeseries(cls) -> 'UsageAggregateItemFields':
        return UsageAggregateItemFields('timeseries')

    def fields(self, *subfields: Union[UsageStatsByModelGraphQLField, 'ModelFields', 'UsageAggregateItemFields']) -> 'UsageStatsByModelFields':
        """Subfields should come from the UsageStatsByModelFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UsageStatsByModelFields':
        self._alias = alias
        return self

class UseCaseFields(GraphQLField):
    """@private"""
    id: 'UseCaseGraphQLField' = UseCaseGraphQLField('id')
    name: 'UseCaseGraphQLField' = UseCaseGraphQLField('name')
    key: 'UseCaseGraphQLField' = UseCaseGraphQLField('key')
    description: 'UseCaseGraphQLField' = UseCaseGraphQLField('description')
    created_at: 'UseCaseGraphQLField' = UseCaseGraphQLField('createdAt')
    is_archived: 'UseCaseGraphQLField' = UseCaseGraphQLField('isArchived')

    @classmethod
    def model_services(cls, *, filter: Optional[ModelServiceFilter]=None) -> 'ModelServiceFields':
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ModelServiceFilter', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ModelServiceFields('modelServices', arguments=cleared_arguments)

    @classmethod
    def model_service(cls, id_or_key: str) -> 'ModelServiceFields':
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ModelServiceFields('modelService', arguments=cleared_arguments)

    @classmethod
    def default_model_service(cls) -> 'ModelServiceFields':
        return ModelServiceFields('defaultModelService')

    @classmethod
    def activity(cls, *, timerange: Optional[TimeRange]=None) -> 'ActivityFields':
        arguments: Dict[str, Dict[str, Any]] = {'timerange': {'type': 'TimeRange', 'value': timerange}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ActivityFields('activity', arguments=cleared_arguments)

    @classmethod
    def metrics(cls) -> 'MetricWithContextFields':
        return MetricWithContextFields('metrics')

    @classmethod
    def metric(cls, metric: str) -> 'MetricWithContextFields':
        arguments: Dict[str, Dict[str, Any]] = {'metric': {'type': 'IdOrKey!', 'value': metric}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return MetricWithContextFields('metric', arguments=cleared_arguments)

    @classmethod
    def ab_campaigns(cls, filter: AbCampaignFilter) -> 'AbcampaignFields':
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'AbCampaignFilter!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return AbcampaignFields('abCampaigns', arguments=cleared_arguments)

    @classmethod
    def widgets(cls) -> 'WidgetFields':
        return WidgetFields('widgets')

    @classmethod
    def metadata(cls) -> 'UseCaseMetadataFields':
        return UseCaseMetadataFields('metadata')
    permissions: 'UseCaseGraphQLField' = UseCaseGraphQLField('permissions')

    @classmethod
    def shares(cls) -> 'ShareFields':
        return ShareFields('shares')

    @classmethod
    def settings(cls) -> 'SettingsFields':
        return SettingsFields('settings')

    @classmethod
    def label_usage(cls) -> 'LabelUsageFields':
        return LabelUsageFields('labelUsage')

    @classmethod
    def tool_providers(cls) -> 'ToolProviderFields':
        return ToolProviderFields('toolProviders')

    def fields(self, *subfields: Union[UseCaseGraphQLField, 'AbcampaignFields', 'ActivityFields', 'LabelUsageFields', 'MetricWithContextFields', 'ModelServiceFields', 'SettingsFields', 'ShareFields', 'ToolProviderFields', 'UseCaseMetadataFields', 'WidgetFields']) -> 'UseCaseFields':
        """Subfields should come from the UseCaseFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UseCaseFields':
        self._alias = alias
        return self

class UseCaseItemFields(GraphQLField):
    """@private"""
    id: 'UseCaseItemGraphQLField' = UseCaseItemGraphQLField('id')
    key: 'UseCaseItemGraphQLField' = UseCaseItemGraphQLField('key')
    name: 'UseCaseItemGraphQLField' = UseCaseItemGraphQLField('name')
    description: 'UseCaseItemGraphQLField' = UseCaseItemGraphQLField('description')

    def fields(self, *subfields: UseCaseItemGraphQLField) -> 'UseCaseItemFields':
        """Subfields should come from the UseCaseItemFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UseCaseItemFields':
        self._alias = alias
        return self

class UseCaseMetadataFields(GraphQLField):
    """@private"""

    @classmethod
    def emoji(cls) -> 'EmojiFields':
        return EmojiFields('emoji')

    def fields(self, *subfields: Union[UseCaseMetadataGraphQLField, 'EmojiFields']) -> 'UseCaseMetadataFields':
        """Subfields should come from the UseCaseMetadataFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UseCaseMetadataFields':
        self._alias = alias
        return self

class UserFields(GraphQLField):
    """@private"""
    id: 'UserGraphQLField' = UserGraphQLField('id')
    email: 'UserGraphQLField' = UserGraphQLField('email')
    name: 'UserGraphQLField' = UserGraphQLField('name')
    created_at: 'UserGraphQLField' = UserGraphQLField('createdAt')
    deleted: 'UserGraphQLField' = UserGraphQLField('deleted')
    deleted_at: 'UserGraphQLField' = UserGraphQLField('deletedAt')

    @classmethod
    def teams(cls) -> 'TeamWithroleFields':
        return TeamWithroleFields('teams')

    @classmethod
    def api_keys(cls) -> 'ApiKeyFields':
        return ApiKeyFields('apiKeys')

    def fields(self, *subfields: Union[UserGraphQLField, 'ApiKeyFields', 'TeamWithroleFields']) -> 'UserFields':
        """Subfields should come from the UserFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'UserFields':
        self._alias = alias
        return self

class WidgetFields(GraphQLField):
    """@private"""
    title: 'WidgetGraphQLField' = WidgetGraphQLField('title')
    metric: 'WidgetGraphQLField' = WidgetGraphQLField('metric')
    aggregation: 'WidgetGraphQLField' = WidgetGraphQLField('aggregation')

    @classmethod
    def unit(cls) -> 'UnitConfigFields':
        return UnitConfigFields('unit')

    def fields(self, *subfields: Union[WidgetGraphQLField, 'UnitConfigFields']) -> 'WidgetFields':
        """Subfields should come from the WidgetFields class"""
        self._subfields.extend(subfields)
        return self

    def alias(self, alias: str) -> 'WidgetFields':
        self._alias = alias
        return self