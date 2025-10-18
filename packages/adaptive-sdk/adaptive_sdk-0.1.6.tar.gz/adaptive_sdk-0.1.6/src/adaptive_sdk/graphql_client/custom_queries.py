from typing import Any, Dict, List, Optional
from . import CompletionGroupBy
from .custom_fields import AbcampaignFields, CompletionConnectionFields, CompletionFields, CompletionGroupDataConnectionFields, ComputePoolFields, ContractFields, CustomRecipeFields, DatasetFields, GlobalUsageFields, GraderFields, HarmonyGroupFields, JobArtifactFields, JobConnectionFields, JobFields, JudgeFields, MetaObjectFields, MetricFields, ModelFields, PrebuiltConfigDefinitionFields, PrebuiltCriteriaFields, RemoteConfigOutputFields, RemoteEnvFields, RoleFields, SystemPromptTemplateFields, TeamFields, ToolProviderFields, UsageAggregateItemFields, UsageAggregatePerUseCaseItemFields, UseCaseFields, UserFields
from .custom_typing_fields import GraphQLField
from .input_types import AbCampaignFilter, ArtifactFilter, CursorPageInput, CustomRecipeFilterInput, DatasetCreateFromFilters, FeedbackFilterInput, GlobalUsageFilterInput, ListCompletionsFilterInput, ListJobsFilterInput, ModelFilter, OrderPair, UsageFilterInput, UsagePerUseCaseFilterInput, UseCaseFilter

class Query:
    """@private"""

    @classmethod
    def ab_campaigns(cls, filter: AbCampaignFilter) -> AbcampaignFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'AbCampaignFilter!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return AbcampaignFields(field_name='abCampaigns', arguments=cleared_arguments)

    @classmethod
    def ab_campaign(cls, id_or_key: str) -> AbcampaignFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return AbcampaignFields(field_name='abCampaign', arguments=cleared_arguments)

    @classmethod
    def contract(cls) -> ContractFields:
        return ContractFields(field_name='contract')

    @classmethod
    def custom_recipes(cls, use_case: str, filter: CustomRecipeFilterInput) -> CustomRecipeFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}, 'filter': {'type': 'CustomRecipeFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CustomRecipeFields(field_name='customRecipes', arguments=cleared_arguments)

    @classmethod
    def custom_recipe(cls, id_or_key: str, use_case: str) -> CustomRecipeFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}, 'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CustomRecipeFields(field_name='customRecipe', arguments=cleared_arguments)

    @classmethod
    def datasets(cls, use_case: str) -> DatasetFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return DatasetFields(field_name='datasets', arguments=cleared_arguments)

    @classmethod
    def dataset(cls, id_or_key: str, use_case: str) -> DatasetFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}, 'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return DatasetFields(field_name='dataset', arguments=cleared_arguments)

    @classmethod
    def preview_dataset_from_filters(cls, input: DatasetCreateFromFilters) -> GraphQLField:
        arguments: Dict[str, Dict[str, Any]] = {'input': {'type': 'DatasetCreateFromFilters!', 'value': input}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GraphQLField(field_name='previewDatasetFromFilters', arguments=cleared_arguments)

    @classmethod
    def completions(cls, filter: ListCompletionsFilterInput, page: CursorPageInput, order: List[OrderPair]) -> CompletionConnectionFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ListCompletionsFilterInput!', 'value': filter}, 'page': {'type': 'CursorPageInput!', 'value': page}, 'order': {'type': '[OrderPair!]!', 'value': order}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionConnectionFields(field_name='completions', arguments=cleared_arguments)

    @classmethod
    def completions_grouped(cls, filter: ListCompletionsFilterInput, feedback_filter: FeedbackFilterInput, group_by: CompletionGroupBy, page: CursorPageInput, order: List[OrderPair]) -> CompletionGroupDataConnectionFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ListCompletionsFilterInput!', 'value': filter}, 'feedbackFilter': {'type': 'FeedbackFilterInput!', 'value': feedback_filter}, 'groupBy': {'type': 'CompletionGroupBy!', 'value': group_by}, 'page': {'type': 'CursorPageInput!', 'value': page}, 'order': {'type': '[OrderPair!]!', 'value': order}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionGroupDataConnectionFields(field_name='completionsGrouped', arguments=cleared_arguments)

    @classmethod
    def completion(cls, use_case: str, id: Any) -> CompletionFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}, 'id': {'type': 'UUID!', 'value': id}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return CompletionFields(field_name='completion', arguments=cleared_arguments)

    @classmethod
    def completion_download_url(cls, filter: ListCompletionsFilterInput) -> GraphQLField:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ListCompletionsFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GraphQLField(field_name='completionDownloadUrl', arguments=cleared_arguments)

    @classmethod
    def completion_as_dataset_download_url(cls, filter: ListCompletionsFilterInput) -> GraphQLField:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ListCompletionsFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GraphQLField(field_name='completionAsDatasetDownloadUrl', arguments=cleared_arguments)

    @classmethod
    def model_usage(cls, filter: UsageFilterInput) -> UsageAggregateItemFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'UsageFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return UsageAggregateItemFields(field_name='modelUsage', arguments=cleared_arguments)

    @classmethod
    def model_usage_by_use_case(cls, filter: UsagePerUseCaseFilterInput) -> UsageAggregatePerUseCaseItemFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'UsagePerUseCaseFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return UsageAggregatePerUseCaseItemFields(field_name='modelUsageByUseCase', arguments=cleared_arguments)

    @classmethod
    def global_usage(cls, filter: GlobalUsageFilterInput) -> GlobalUsageFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'GlobalUsageFilterInput!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GlobalUsageFields(field_name='globalUsage', arguments=cleared_arguments)

    @classmethod
    def system_prompt_templates(cls) -> SystemPromptTemplateFields:
        return SystemPromptTemplateFields(field_name='systemPromptTemplates')

    @classmethod
    def jobs(cls, page: CursorPageInput, filter: ListJobsFilterInput, order: List[OrderPair]) -> JobConnectionFields:
        arguments: Dict[str, Dict[str, Any]] = {'page': {'type': 'CursorPageInput!', 'value': page}, 'filter': {'type': 'ListJobsFilterInput!', 'value': filter}, 'order': {'type': '[OrderPair!]!', 'value': order}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JobConnectionFields(field_name='jobs', arguments=cleared_arguments)

    @classmethod
    def job(cls, id: Any) -> JobFields:
        arguments: Dict[str, Dict[str, Any]] = {'id': {'type': 'UUID!', 'value': id}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JobFields(field_name='job', arguments=cleared_arguments)

    @classmethod
    def metrics(cls) -> MetricFields:
        return MetricFields(field_name='metrics')

    @classmethod
    def metric(cls, id_or_key: str) -> MetricFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return MetricFields(field_name='metric', arguments=cleared_arguments)

    @classmethod
    def models(cls, filter: ModelFilter) -> ModelFields:
        """List all models that were created in the app"""
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'ModelFilter!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ModelFields(field_name='models', arguments=cleared_arguments)

    @classmethod
    def model(cls, id_or_key: str) -> ModelFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ModelFields(field_name='model', arguments=cleared_arguments)

    @classmethod
    def all_harmony_groups(cls) -> HarmonyGroupFields:
        return HarmonyGroupFields(field_name='allHarmonyGroups')

    @classmethod
    def harmony_groups(cls) -> HarmonyGroupFields:
        return HarmonyGroupFields(field_name='harmonyGroups')

    @classmethod
    def compute_pools(cls) -> ComputePoolFields:
        return ComputePoolFields(field_name='computePools')

    @classmethod
    def remote_envs(cls) -> RemoteEnvFields:
        return RemoteEnvFields(field_name='remoteEnvs')

    @classmethod
    def use_cases(cls, filter: UseCaseFilter) -> UseCaseFields:
        arguments: Dict[str, Dict[str, Any]] = {'filter': {'type': 'UseCaseFilter!', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return UseCaseFields(field_name='useCases', arguments=cleared_arguments)

    @classmethod
    def use_case(cls, id_or_key: str) -> UseCaseFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return UseCaseFields(field_name='useCase', arguments=cleared_arguments)

    @classmethod
    def me(cls) -> UserFields:
        """Currently logged in user"""
        return UserFields(field_name='me')

    @classmethod
    def users(cls) -> UserFields:
        return UserFields(field_name='users')

    @classmethod
    def roles(cls) -> RoleFields:
        return RoleFields(field_name='roles')

    @classmethod
    def permissions(cls) -> GraphQLField:
        return GraphQLField(field_name='permissions')

    @classmethod
    def teams(cls) -> TeamFields:
        return TeamFields(field_name='teams')

    @classmethod
    def judge(cls, id: str, use_case: str, *, version: Optional[int]=None) -> JudgeFields:
        arguments: Dict[str, Dict[str, Any]] = {'id': {'type': 'IdOrKey!', 'value': id}, 'useCase': {'type': 'IdOrKey!', 'value': use_case}, 'version': {'type': 'Int', 'value': version}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JudgeFields(field_name='judge', arguments=cleared_arguments)

    @classmethod
    def judges(cls, use_case: str) -> JudgeFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JudgeFields(field_name='judges', arguments=cleared_arguments)

    @classmethod
    def judge_versions(cls, use_case: str, key: str) -> JudgeFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}, 'key': {'type': 'String!', 'value': key}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JudgeFields(field_name='judgeVersions', arguments=cleared_arguments)

    @classmethod
    def prebuilt_criteria(cls) -> PrebuiltCriteriaFields:
        return PrebuiltCriteriaFields(field_name='prebuiltCriteria')

    @classmethod
    def grader(cls, id: str, use_case: str) -> GraderFields:
        arguments: Dict[str, Dict[str, Any]] = {'id': {'type': 'IdOrKey!', 'value': id}, 'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GraderFields(field_name='grader', arguments=cleared_arguments)

    @classmethod
    def graders(cls, use_case: str) -> GraderFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GraderFields(field_name='graders', arguments=cleared_arguments)

    @classmethod
    def prebuilt_configs(cls) -> PrebuiltConfigDefinitionFields:
        return PrebuiltConfigDefinitionFields(field_name='prebuiltConfigs')

    @classmethod
    def test_remote_env_2(cls, url: str) -> RemoteConfigOutputFields:
        arguments: Dict[str, Dict[str, Any]] = {'url': {'type': 'String!', 'value': url}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return RemoteConfigOutputFields(field_name='testRemoteEnv2', arguments=cleared_arguments)

    @classmethod
    def validate_data_schema_for_grader(cls, grader: str, dataset: str, usecase: str) -> GraphQLField:
        arguments: Dict[str, Dict[str, Any]] = {'grader': {'type': 'IdOrKey!', 'value': grader}, 'dataset': {'type': 'IdOrKey!', 'value': dataset}, 'usecase': {'type': 'IdOrKey!', 'value': usecase}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return GraphQLField(field_name='validateDataSchemaForGrader', arguments=cleared_arguments)

    @classmethod
    def tool_provider(cls, id_or_key: str, use_case: str) -> ToolProviderFields:
        arguments: Dict[str, Dict[str, Any]] = {'idOrKey': {'type': 'IdOrKey!', 'value': id_or_key}, 'useCase': {'type': 'IdOrKey!', 'value': use_case}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return ToolProviderFields(field_name='toolProvider', arguments=cleared_arguments)

    @classmethod
    def artifacts(cls, use_case: str, *, filter: Optional[ArtifactFilter]=None) -> JobArtifactFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}, 'filter': {'type': 'ArtifactFilter', 'value': filter}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JobArtifactFields(field_name='artifacts', arguments=cleared_arguments)

    @classmethod
    def artifact(cls, use_case: str, id: Any) -> JobArtifactFields:
        arguments: Dict[str, Dict[str, Any]] = {'useCase': {'type': 'IdOrKey!', 'value': use_case}, 'id': {'type': 'UUID!', 'value': id}}
        cleared_arguments = {key: value for (key, value) in arguments.items() if value['value'] is not None}
        return JobArtifactFields(field_name='artifact', arguments=cleared_arguments)

    @classmethod
    def meta(cls) -> MetaObjectFields:
        return MetaObjectFields(field_name='meta')