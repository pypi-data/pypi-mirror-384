from typing import Any, Dict, List, Optional, Tuple, Union
from graphql import DocumentNode, NamedTypeNode, NameNode, OperationDefinitionNode, OperationType, SelectionNode, SelectionSetNode, VariableDefinitionNode, VariableNode, print_ast
from .add_external_model import AddExternalModel
from .add_hf_model import AddHFModel
from .add_model import AddModel
from .add_remote_env import AddRemoteEnv
from .attach_model_to_use_case import AttachModelToUseCase
from .base_client_open_telemetry import BaseClientOpenTelemetry
from .base_model import UNSET, UnsetType, Upload
from .base_operation import GraphQLField
from .cancel_ab_campaign import CancelABCampaign
from .cancel_job import CancelJob
from .create_ab_campaign import CreateAbCampaign
from .create_custom_recipe import CreateCustomRecipe
from .create_grader import CreateGrader
from .create_job import CreateJob
from .create_judge import CreateJudge
from .create_metric import CreateMetric
from .create_prebuilt_judge import CreatePrebuiltJudge
from .create_role import CreateRole
from .create_team import CreateTeam
from .create_use_case import CreateUseCase
from .create_user import CreateUser
from .delete_custom_recipe import DeleteCustomRecipe
from .delete_dataset import DeleteDataset
from .delete_grader import DeleteGrader
from .delete_judge import DeleteJudge
from .delete_user import DeleteUser
from .deploy_model import DeployModel
from .describe_ab_campaign import DescribeAbCampaign
from .describe_dataset import DescribeDataset
from .describe_interaction import DescribeInteraction
from .describe_job import DescribeJob
from .describe_metric import DescribeMetric
from .describe_metric_admin import DescribeMetricAdmin
from .describe_model import DescribeModel
from .describe_model_admin import DescribeModelAdmin
from .describe_use_case import DescribeUseCase
from .enums import CompletionGroupBy
from .get_custom_recipe import GetCustomRecipe
from .get_grader import GetGrader
from .get_judge import GetJudge
from .input_types import AbcampaignCreate, AbCampaignFilter, AddExternalModelInput, AddHFModelInput, AddModelInput, AttachModel, CreateRecipeInput, CursorPageInput, CustomRecipeFilterInput, DatasetCreate, GraderCreateInput, GraderUpdateInput, JobInput, JudgeCreate, JudgeUpdate, ListCompletionsFilterInput, ListJobsFilterInput, MetricCreate, MetricLink, MetricUnlink, ModelComputeConfigInput, ModelFilter, ModelPlacementInput, OrderPair, PrebuiltJudgeCreate, RemoteEnvCreate, RoleCreate, TeamCreate, TeamMemberRemove, TeamMemberSet, UpdateModelService, UpdateRecipeInput, UseCaseCreate, UseCaseShares, UserCreate
from .link_metric import LinkMetric
from .list_ab_campaigns import ListAbCampaigns
from .list_compute_pools import ListComputePools
from .list_custom_recipes import ListCustomRecipes
from .list_datasets import ListDatasets
from .list_graders import ListGraders
from .list_grouped_interactions import ListGroupedInteractions
from .list_harmony_groups import ListHarmonyGroups
from .list_interactions import ListInteractions
from .list_jobs import ListJobs
from .list_judge_versions import ListJudgeVersions
from .list_judges import ListJudges
from .list_metrics import ListMetrics
from .list_models import ListModels
from .list_permissions import ListPermissions
from .list_remote_envs import ListRemoteEnvs
from .list_roles import ListRoles
from .list_teams import ListTeams
from .list_use_cases import ListUseCases
from .list_users import ListUsers
from .load_dataset import LoadDataset
from .lock_grader import LockGrader
from .me import Me
from .remove_remote_env import RemoveRemoteEnv
from .remove_team_member import RemoveTeamMember
from .share_use_case import ShareUseCase
from .terminate_model import TerminateModel
from .test_remote_env import TestRemoteEnv
from .unlink_metric import UnlinkMetric
from .update_custom_recipe import UpdateCustomRecipe
from .update_grader import UpdateGrader
from .update_judge import UpdateJudge
from .update_model import UpdateModel
from .update_model_compute_config import UpdateModelComputeConfig
from .update_user import UpdateUser

def gql(q: str) -> str:
    return q

class GQLClient(BaseClientOpenTelemetry):
    """@private"""

    def create_metric(self, input: MetricCreate, **kwargs: Any) -> CreateMetric:
        query = gql('\n            mutation CreateMetric($input: MetricCreate!) {\n              createMetric(input: $input) {\n                ...MetricData\n              }\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateMetric', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateMetric.model_validate(data)

    def link_metric(self, input: MetricLink, **kwargs: Any) -> LinkMetric:
        query = gql('\n            mutation LinkMetric($input: MetricLink!) {\n              linkMetric(input: $input) {\n                ...MetricWithContextData\n              }\n            }\n\n            fragment MetricWithContextData on MetricWithContext {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='LinkMetric', variables=variables, **kwargs)
        data = self.get_data(response)
        return LinkMetric.model_validate(data)

    def unlink_metric(self, input: MetricUnlink, **kwargs: Any) -> UnlinkMetric:
        query = gql('\n            mutation UnlinkMetric($input: MetricUnlink!) {\n              unlinkMetric(input: $input)\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='UnlinkMetric', variables=variables, **kwargs)
        data = self.get_data(response)
        return UnlinkMetric.model_validate(data)

    def attach_model_to_use_case(self, input: AttachModel, **kwargs: Any) -> AttachModelToUseCase:
        query = gql('\n            mutation AttachModelToUseCase($input: AttachModel!) {\n              attachModel(input: $input) {\n                ...ModelServiceData\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n\n            fragment ModelServiceData on ModelService {\n              id\n              key\n              name\n              model {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n              attached\n              isDefault\n              desiredOnline\n              createdAt\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='AttachModelToUseCase', variables=variables, **kwargs)
        data = self.get_data(response)
        return AttachModelToUseCase.model_validate(data)

    def add_external_model(self, input: AddExternalModelInput, **kwargs: Any) -> AddExternalModel:
        query = gql('\n            mutation AddExternalModel($input: AddExternalModelInput!) {\n              addExternalModel(input: $input) {\n                ...ModelData\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='AddExternalModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return AddExternalModel.model_validate(data)

    def add_model(self, input: AddModelInput, **kwargs: Any) -> AddModel:
        query = gql('\n            mutation AddModel($input: AddModelInput!) {\n              addModel(input: $input) {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='AddModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return AddModel.model_validate(data)

    def update_model(self, input: UpdateModelService, **kwargs: Any) -> UpdateModel:
        query = gql('\n            mutation UpdateModel($input: UpdateModelService!) {\n              updateModelService(input: $input) {\n                ...ModelServiceData\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n\n            fragment ModelServiceData on ModelService {\n              id\n              key\n              name\n              model {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n              attached\n              isDefault\n              desiredOnline\n              createdAt\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='UpdateModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return UpdateModel.model_validate(data)

    def deploy_model(self, id_or_key: str, wait: bool, placement: Union[Optional[ModelPlacementInput], UnsetType]=UNSET, **kwargs: Any) -> DeployModel:
        query = gql('\n            mutation DeployModel($idOrKey: IdOrKey!, $wait: Boolean!, $placement: ModelPlacementInput) {\n              deployModel(idOrKey: $idOrKey, wait: $wait, placement: $placement)\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key, 'wait': wait, 'placement': placement}
        response = self.execute(query=query, operation_name='DeployModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return DeployModel.model_validate(data)

    def terminate_model(self, id_or_key: str, force: bool, **kwargs: Any) -> TerminateModel:
        query = gql('\n            mutation TerminateModel($idOrKey: IdOrKey!, $force: Boolean!) {\n              terminateModel(idOrKey: $idOrKey, force: $force)\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key, 'force': force}
        response = self.execute(query=query, operation_name='TerminateModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return TerminateModel.model_validate(data)

    def create_use_case(self, input: UseCaseCreate, **kwargs: Any) -> CreateUseCase:
        query = gql('\n            mutation CreateUseCase($input: UseCaseCreate!) {\n              createUseCase(input: $input) {\n                ...UseCaseData\n              }\n            }\n\n            fragment MetricWithContextData on MetricWithContext {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n\n            fragment ModelServiceData on ModelService {\n              id\n              key\n              name\n              model {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n              attached\n              isDefault\n              desiredOnline\n              createdAt\n            }\n\n            fragment UseCaseData on UseCase {\n              id\n              key\n              name\n              description\n              createdAt\n              metrics {\n                ...MetricWithContextData\n              }\n              modelServices {\n                ...ModelServiceData\n              }\n              permissions\n              shares {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n                isOwner\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateUseCase', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateUseCase.model_validate(data)

    def share_use_case(self, id_or_key: str, input: UseCaseShares, **kwargs: Any) -> ShareUseCase:
        query = gql('\n            mutation ShareUseCase($idOrKey: IdOrKey!, $input: UseCaseShares!) {\n              shareUseCase(idOrKey: $idOrKey, input: $input) {\n                ...UseCaseData\n              }\n            }\n\n            fragment MetricWithContextData on MetricWithContext {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n\n            fragment ModelServiceData on ModelService {\n              id\n              key\n              name\n              model {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n              attached\n              isDefault\n              desiredOnline\n              createdAt\n            }\n\n            fragment UseCaseData on UseCase {\n              id\n              key\n              name\n              description\n              createdAt\n              metrics {\n                ...MetricWithContextData\n              }\n              modelServices {\n                ...ModelServiceData\n              }\n              permissions\n              shares {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n                isOwner\n              }\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key, 'input': input}
        response = self.execute(query=query, operation_name='ShareUseCase', variables=variables, **kwargs)
        data = self.get_data(response)
        return ShareUseCase.model_validate(data)

    def create_ab_campaign(self, input: AbcampaignCreate, **kwargs: Any) -> CreateAbCampaign:
        query = gql('\n            mutation CreateAbCampaign($input: AbcampaignCreate!) {\n              createAbCampaign(input: $input) {\n                ...AbCampaignCreateData\n              }\n            }\n\n            fragment AbCampaignCreateData on Abcampaign {\n              id\n              key\n              status\n              beginDate\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateAbCampaign', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateAbCampaign.model_validate(data)

    def cancel_ab_campaign(self, input: str, **kwargs: Any) -> CancelABCampaign:
        query = gql('\n            mutation CancelABCampaign($input: IdOrKey!) {\n              cancelAbCampaign(input: $input)\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CancelABCampaign', variables=variables, **kwargs)
        data = self.get_data(response)
        return CancelABCampaign.model_validate(data)

    def load_dataset(self, input: DatasetCreate, file: Upload, **kwargs: Any) -> LoadDataset:
        query = gql('\n            mutation LoadDataset($input: DatasetCreate!, $file: Upload!) {\n              createDataset(input: $input, file: $file) {\n                ...DatasetData\n              }\n            }\n\n            fragment DatasetData on Dataset {\n              id\n              key\n              name\n              createdAt\n              kind\n              records\n              metricsUsage {\n                feedbackCount\n                comparisonCount\n                metric {\n                  ...MetricData\n                }\n              }\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input, 'file': file}
        response = self.execute(query=query, operation_name='LoadDataset', variables=variables, **kwargs)
        data = self.get_data(response)
        return LoadDataset.model_validate(data)

    def delete_dataset(self, id_or_key: str, use_case: str, **kwargs: Any) -> DeleteDataset:
        query = gql('\n            mutation DeleteDataset($idOrKey: IdOrKey!, $useCase: IdOrKey!) {\n              deleteDataset(idOrKey: $idOrKey, useCase: $useCase)\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key, 'useCase': use_case}
        response = self.execute(query=query, operation_name='DeleteDataset', variables=variables, **kwargs)
        data = self.get_data(response)
        return DeleteDataset.model_validate(data)

    def add_hf_model(self, input: AddHFModelInput, **kwargs: Any) -> AddHFModel:
        query = gql('\n            mutation AddHFModel($input: AddHFModelInput!) {\n              importHfModel(input: $input) {\n                ...JobData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n\n            fragment JobData on Job {\n              id\n              name\n              status\n              createdAt\n              createdBy {\n                id\n                name\n              }\n              startedAt\n              endedAt\n              durationMs\n              progress\n              error\n              kind\n              stages {\n                name\n                status\n                info {\n                  __typename\n                  ... on TrainingJobStageOutput {\n                    monitoringLink\n                    totalNumSamples\n                    processedNumSamples\n                    checkpoints\n                  }\n                  ... on EvalJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                  ... on BatchInferenceJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              recipe {\n                ...CustomRecipeData\n              }\n              details {\n                args\n                recipeHash\n                artifacts {\n                  id\n                  name\n                  kind\n                  uri\n                  metadata\n                  createdAt\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='AddHFModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return AddHFModel.model_validate(data)

    def create_user(self, input: UserCreate, **kwargs: Any) -> CreateUser:
        query = gql('\n            mutation CreateUser($input: UserCreate!) {\n              createUser(input: $input) {\n                ...UserData\n              }\n            }\n\n            fragment UserData on User {\n              id\n              email\n              name\n              createdAt\n              teams {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateUser', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateUser.model_validate(data)

    def delete_user(self, user: str, **kwargs: Any) -> DeleteUser:
        query = gql('\n            mutation DeleteUser($user: IdOrKey!) {\n              deleteUser(user: $user) {\n                ...UserData\n              }\n            }\n\n            fragment UserData on User {\n              id\n              email\n              name\n              createdAt\n              teams {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'user': user}
        response = self.execute(query=query, operation_name='DeleteUser', variables=variables, **kwargs)
        data = self.get_data(response)
        return DeleteUser.model_validate(data)

    def update_user(self, input: TeamMemberSet, **kwargs: Any) -> UpdateUser:
        query = gql('\n            mutation UpdateUser($input: TeamMemberSet!) {\n              setTeamMember(input: $input) {\n                user {\n                  ...UserData\n                }\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n\n            fragment UserData on User {\n              id\n              email\n              name\n              createdAt\n              teams {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='UpdateUser', variables=variables, **kwargs)
        data = self.get_data(response)
        return UpdateUser.model_validate(data)

    def create_role(self, input: RoleCreate, **kwargs: Any) -> CreateRole:
        query = gql('\n            mutation CreateRole($input: RoleCreate!) {\n              createRole(input: $input) {\n                id\n                key\n                name\n                createdAt\n                permissions\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateRole', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateRole.model_validate(data)

    def create_team(self, input: TeamCreate, **kwargs: Any) -> CreateTeam:
        query = gql('\n            mutation CreateTeam($input: TeamCreate!) {\n              createTeam(input: $input) {\n                id\n                key\n                name\n                createdAt\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateTeam', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateTeam.model_validate(data)

    def update_model_compute_config(self, id_or_key: str, input: ModelComputeConfigInput, **kwargs: Any) -> UpdateModelComputeConfig:
        query = gql('\n            mutation UpdateModelComputeConfig($idOrKey: IdOrKey!, $input: ModelComputeConfigInput!) {\n              updateModelComputeConfig(idOrKey: $idOrKey, input: $input) {\n                ...ModelData\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key, 'input': input}
        response = self.execute(query=query, operation_name='UpdateModelComputeConfig', variables=variables, **kwargs)
        data = self.get_data(response)
        return UpdateModelComputeConfig.model_validate(data)

    def add_remote_env(self, input: RemoteEnvCreate, **kwargs: Any) -> AddRemoteEnv:
        query = gql('\n            mutation AddRemoteEnv($input: RemoteEnvCreate!) {\n              addRemoteEnv(input: $input) {\n                ...RemoteEnvData\n              }\n            }\n\n            fragment RemoteEnvData on RemoteEnv {\n              id\n              key\n              name\n              url\n              description\n              createdAt\n              version\n              status\n              metadataSchema\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='AddRemoteEnv', variables=variables, **kwargs)
        data = self.get_data(response)
        return AddRemoteEnv.model_validate(data)

    def remove_remote_env(self, id_or_key: str, **kwargs: Any) -> RemoveRemoteEnv:
        query = gql('\n            mutation RemoveRemoteEnv($idOrKey: IdOrKey!) {\n              removeRemoteEnv(idOrKey: $idOrKey)\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key}
        response = self.execute(query=query, operation_name='RemoveRemoteEnv', variables=variables, **kwargs)
        data = self.get_data(response)
        return RemoveRemoteEnv.model_validate(data)

    def test_remote_env(self, input: RemoteEnvCreate, **kwargs: Any) -> TestRemoteEnv:
        query = gql('\n            mutation TestRemoteEnv($input: RemoteEnvCreate!) {\n              testRemoteEnv(input: $input) {\n                __typename\n                ... on RemoteEnvTestOffline {\n                  error\n                }\n                ... on RemoteEnvTestOnline {\n                  name\n                  version\n                  description\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='TestRemoteEnv', variables=variables, **kwargs)
        data = self.get_data(response)
        return TestRemoteEnv.model_validate(data)

    def create_custom_recipe(self, use_case: str, input: CreateRecipeInput, file: Upload, **kwargs: Any) -> CreateCustomRecipe:
        query = gql('\n            mutation CreateCustomRecipe($useCase: IdOrKey!, $input: CreateRecipeInput!, $file: Upload!) {\n              createCustomRecipe(useCase: $useCase, input: $input, file: $file) {\n                ...CustomRecipeData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'input': input, 'file': file}
        response = self.execute(query=query, operation_name='CreateCustomRecipe', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateCustomRecipe.model_validate(data)

    def update_custom_recipe(self, use_case: str, id: str, input: UpdateRecipeInput, file: Union[Optional[Upload], UnsetType]=UNSET, **kwargs: Any) -> UpdateCustomRecipe:
        query = gql('\n            mutation UpdateCustomRecipe($useCase: IdOrKey!, $id: IdOrKey!, $input: UpdateRecipeInput!, $file: Upload) {\n              updateCustomRecipe(useCase: $useCase, id: $id, input: $input, file: $file) {\n                ...CustomRecipeData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'id': id, 'input': input, 'file': file}
        response = self.execute(query=query, operation_name='UpdateCustomRecipe', variables=variables, **kwargs)
        data = self.get_data(response)
        return UpdateCustomRecipe.model_validate(data)

    def delete_custom_recipe(self, use_case: str, id: str, **kwargs: Any) -> DeleteCustomRecipe:
        query = gql('\n            mutation DeleteCustomRecipe($useCase: IdOrKey!, $id: IdOrKey!) {\n              deleteCustomRecipe(useCase: $useCase, id: $id)\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'id': id}
        response = self.execute(query=query, operation_name='DeleteCustomRecipe', variables=variables, **kwargs)
        data = self.get_data(response)
        return DeleteCustomRecipe.model_validate(data)

    def create_judge(self, use_case: str, input: JudgeCreate, **kwargs: Any) -> CreateJudge:
        query = gql('\n            mutation CreateJudge($useCase: IdOrKey!, $input: JudgeCreate!) {\n              createJudge(useCase: $useCase, input: $input) {\n                ...JudgeData\n              }\n            }\n\n            fragment JudgeData on Judge {\n              id\n              key\n              version\n              name\n              criteria\n              prebuilt\n              examples {\n                input {\n                  role\n                  content\n                }\n                output\n                pass\n                reasoning\n              }\n              capabilities\n              model {\n                ...ModelData\n              }\n              useCaseId\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'input': input}
        response = self.execute(query=query, operation_name='CreateJudge', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateJudge.model_validate(data)

    def create_prebuilt_judge(self, use_case: str, input: PrebuiltJudgeCreate, **kwargs: Any) -> CreatePrebuiltJudge:
        query = gql('\n            mutation CreatePrebuiltJudge($useCase: IdOrKey!, $input: PrebuiltJudgeCreate!) {\n              createPrebuiltJudge(useCase: $useCase, input: $input) {\n                ...JudgeData\n              }\n            }\n\n            fragment JudgeData on Judge {\n              id\n              key\n              version\n              name\n              criteria\n              prebuilt\n              examples {\n                input {\n                  role\n                  content\n                }\n                output\n                pass\n                reasoning\n              }\n              capabilities\n              model {\n                ...ModelData\n              }\n              useCaseId\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'input': input}
        response = self.execute(query=query, operation_name='CreatePrebuiltJudge', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreatePrebuiltJudge.model_validate(data)

    def update_judge(self, use_case: str, key: str, input: JudgeUpdate, **kwargs: Any) -> UpdateJudge:
        query = gql('\n            mutation UpdateJudge($useCase: IdOrKey!, $key: String!, $input: JudgeUpdate!) {\n              updateJudge(useCase: $useCase, key: $key, input: $input) {\n                ...JudgeData\n              }\n            }\n\n            fragment JudgeData on Judge {\n              id\n              key\n              version\n              name\n              criteria\n              prebuilt\n              examples {\n                input {\n                  role\n                  content\n                }\n                output\n                pass\n                reasoning\n              }\n              capabilities\n              model {\n                ...ModelData\n              }\n              useCaseId\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'key': key, 'input': input}
        response = self.execute(query=query, operation_name='UpdateJudge', variables=variables, **kwargs)
        data = self.get_data(response)
        return UpdateJudge.model_validate(data)

    def delete_judge(self, use_case: str, key: str, **kwargs: Any) -> DeleteJudge:
        query = gql('\n            mutation DeleteJudge($useCase: IdOrKey!, $key: String!) {\n              deleteJudge(useCase: $useCase, key: $key) {\n                success\n                details\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'key': key}
        response = self.execute(query=query, operation_name='DeleteJudge', variables=variables, **kwargs)
        data = self.get_data(response)
        return DeleteJudge.model_validate(data)

    def create_grader(self, use_case: str, input: GraderCreateInput, **kwargs: Any) -> CreateGrader:
        query = gql('\n            mutation CreateGrader($useCase: IdOrKey!, $input: GraderCreateInput!) {\n              createGrader(useCase: $useCase, input: $input) {\n                ...GraderData\n              }\n            }\n\n            fragment GraderData on Grader {\n              id\n              name\n              key\n              locked\n              graderType\n              graderConfig {\n                __typename\n                ... on JudgeConfigOutput {\n                  judgeCriteria: criteria\n                  examples {\n                    input {\n                      role\n                      content\n                    }\n                    output\n                    pass\n                    reasoning\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on PrebuiltConfigOutput {\n                  prebuiltCriteria: criteria {\n                    key\n                    name\n                    feedbackKey\n                    description\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on RemoteConfigOutput {\n                  url\n                  version\n                  description\n                }\n                ... on CustomConfigOutput {\n                  graderDescription: description\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'input': input}
        response = self.execute(query=query, operation_name='CreateGrader', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateGrader.model_validate(data)

    def update_grader(self, use_case: str, id: str, input: GraderUpdateInput, **kwargs: Any) -> UpdateGrader:
        query = gql('\n            mutation UpdateGrader($useCase: IdOrKey!, $id: IdOrKey!, $input: GraderUpdateInput!) {\n              updateGrader(useCase: $useCase, id: $id, input: $input) {\n                ...GraderData\n              }\n            }\n\n            fragment GraderData on Grader {\n              id\n              name\n              key\n              locked\n              graderType\n              graderConfig {\n                __typename\n                ... on JudgeConfigOutput {\n                  judgeCriteria: criteria\n                  examples {\n                    input {\n                      role\n                      content\n                    }\n                    output\n                    pass\n                    reasoning\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on PrebuiltConfigOutput {\n                  prebuiltCriteria: criteria {\n                    key\n                    name\n                    feedbackKey\n                    description\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on RemoteConfigOutput {\n                  url\n                  version\n                  description\n                }\n                ... on CustomConfigOutput {\n                  graderDescription: description\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'id': id, 'input': input}
        response = self.execute(query=query, operation_name='UpdateGrader', variables=variables, **kwargs)
        data = self.get_data(response)
        return UpdateGrader.model_validate(data)

    def delete_grader(self, use_case: str, id: str, **kwargs: Any) -> DeleteGrader:
        query = gql('\n            mutation DeleteGrader($useCase: IdOrKey!, $id: IdOrKey!) {\n              deleteGrader(useCase: $useCase, id: $id) {\n                success\n                details\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'id': id}
        response = self.execute(query=query, operation_name='DeleteGrader', variables=variables, **kwargs)
        data = self.get_data(response)
        return DeleteGrader.model_validate(data)

    def lock_grader(self, use_case: str, id: str, locked: bool, **kwargs: Any) -> LockGrader:
        query = gql('\n            mutation LockGrader($useCase: IdOrKey!, $id: IdOrKey!, $locked: Boolean!) {\n              lockGrader(useCase: $useCase, id: $id, locked: $locked) {\n                ...GraderData\n              }\n            }\n\n            fragment GraderData on Grader {\n              id\n              name\n              key\n              locked\n              graderType\n              graderConfig {\n                __typename\n                ... on JudgeConfigOutput {\n                  judgeCriteria: criteria\n                  examples {\n                    input {\n                      role\n                      content\n                    }\n                    output\n                    pass\n                    reasoning\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on PrebuiltConfigOutput {\n                  prebuiltCriteria: criteria {\n                    key\n                    name\n                    feedbackKey\n                    description\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on RemoteConfigOutput {\n                  url\n                  version\n                  description\n                }\n                ... on CustomConfigOutput {\n                  graderDescription: description\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'id': id, 'locked': locked}
        response = self.execute(query=query, operation_name='LockGrader', variables=variables, **kwargs)
        data = self.get_data(response)
        return LockGrader.model_validate(data)

    def remove_team_member(self, input: TeamMemberRemove, **kwargs: Any) -> RemoveTeamMember:
        query = gql('\n            mutation RemoveTeamMember($input: TeamMemberRemove!) {\n              removeTeamMember(input: $input) {\n                ...UserData\n              }\n            }\n\n            fragment UserData on User {\n              id\n              email\n              name\n              createdAt\n              teams {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='RemoveTeamMember', variables=variables, **kwargs)
        data = self.get_data(response)
        return RemoveTeamMember.model_validate(data)

    def create_job(self, input: JobInput, **kwargs: Any) -> CreateJob:
        query = gql('\n            mutation CreateJob($input: JobInput!) {\n              createJob(input: $input) {\n                ...JobData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n\n            fragment JobData on Job {\n              id\n              name\n              status\n              createdAt\n              createdBy {\n                id\n                name\n              }\n              startedAt\n              endedAt\n              durationMs\n              progress\n              error\n              kind\n              stages {\n                name\n                status\n                info {\n                  __typename\n                  ... on TrainingJobStageOutput {\n                    monitoringLink\n                    totalNumSamples\n                    processedNumSamples\n                    checkpoints\n                  }\n                  ... on EvalJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                  ... on BatchInferenceJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              recipe {\n                ...CustomRecipeData\n              }\n              details {\n                args\n                recipeHash\n                artifacts {\n                  id\n                  name\n                  kind\n                  uri\n                  metadata\n                  createdAt\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='CreateJob', variables=variables, **kwargs)
        data = self.get_data(response)
        return CreateJob.model_validate(data)

    def cancel_job(self, job_id: Any, **kwargs: Any) -> CancelJob:
        query = gql('\n            mutation CancelJob($jobId: UUID!) {\n              cancelJob(id: $jobId) {\n                ...JobData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n\n            fragment JobData on Job {\n              id\n              name\n              status\n              createdAt\n              createdBy {\n                id\n                name\n              }\n              startedAt\n              endedAt\n              durationMs\n              progress\n              error\n              kind\n              stages {\n                name\n                status\n                info {\n                  __typename\n                  ... on TrainingJobStageOutput {\n                    monitoringLink\n                    totalNumSamples\n                    processedNumSamples\n                    checkpoints\n                  }\n                  ... on EvalJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                  ... on BatchInferenceJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              recipe {\n                ...CustomRecipeData\n              }\n              details {\n                args\n                recipeHash\n                artifacts {\n                  id\n                  name\n                  kind\n                  uri\n                  metadata\n                  createdAt\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'jobId': job_id}
        response = self.execute(query=query, operation_name='CancelJob', variables=variables, **kwargs)
        data = self.get_data(response)
        return CancelJob.model_validate(data)

    def list_datasets(self, input: str, **kwargs: Any) -> ListDatasets:
        query = gql('\n            query ListDatasets($input: IdOrKey!) {\n              datasets(useCase: $input) {\n                ...DatasetData\n              }\n            }\n\n            fragment DatasetData on Dataset {\n              id\n              key\n              name\n              createdAt\n              kind\n              records\n              metricsUsage {\n                feedbackCount\n                comparisonCount\n                metric {\n                  ...MetricData\n                }\n              }\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='ListDatasets', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListDatasets.model_validate(data)

    def describe_dataset(self, input: str, usecase: str, **kwargs: Any) -> DescribeDataset:
        query = gql('\n            query DescribeDataset($input: IdOrKey!, $usecase: IdOrKey!) {\n              dataset(idOrKey: $input, useCase: $usecase) {\n                ...DatasetData\n              }\n            }\n\n            fragment DatasetData on Dataset {\n              id\n              key\n              name\n              createdAt\n              kind\n              records\n              metricsUsage {\n                feedbackCount\n                comparisonCount\n                metric {\n                  ...MetricData\n                }\n              }\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input, 'usecase': usecase}
        response = self.execute(query=query, operation_name='DescribeDataset', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeDataset.model_validate(data)

    def describe_use_case(self, input: str, **kwargs: Any) -> DescribeUseCase:
        query = gql('\n            query DescribeUseCase($input: IdOrKey!) {\n              useCase(idOrKey: $input) {\n                ...UseCaseData\n              }\n            }\n\n            fragment MetricWithContextData on MetricWithContext {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n\n            fragment ModelServiceData on ModelService {\n              id\n              key\n              name\n              model {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n              attached\n              isDefault\n              desiredOnline\n              createdAt\n            }\n\n            fragment UseCaseData on UseCase {\n              id\n              key\n              name\n              description\n              createdAt\n              metrics {\n                ...MetricWithContextData\n              }\n              modelServices {\n                ...ModelServiceData\n              }\n              permissions\n              shares {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n                isOwner\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='DescribeUseCase', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeUseCase.model_validate(data)

    def list_use_cases(self, **kwargs: Any) -> ListUseCases:
        query = gql('\n            query ListUseCases {\n              useCases {\n                ...UseCaseData\n              }\n            }\n\n            fragment MetricWithContextData on MetricWithContext {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n\n            fragment ModelServiceData on ModelService {\n              id\n              key\n              name\n              model {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n              attached\n              isDefault\n              desiredOnline\n              createdAt\n            }\n\n            fragment UseCaseData on UseCase {\n              id\n              key\n              name\n              description\n              createdAt\n              metrics {\n                ...MetricWithContextData\n              }\n              modelServices {\n                ...ModelServiceData\n              }\n              permissions\n              shares {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n                isOwner\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListUseCases', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListUseCases.model_validate(data)

    def list_models(self, filter: ModelFilter, **kwargs: Any) -> ListModels:
        query = gql('\n            query ListModels($filter: ModelFilter! = {inStorage: null, available: null, trainable: null, kind: [Generation, Embedding], viewAll: false, online: null}) {\n              models(filter: $filter) {\n                ...ModelDataAdmin\n                backbone {\n                  ...ModelDataAdmin\n                }\n              }\n            }\n\n            fragment ModelDataAdmin on Model {\n              id\n              key\n              name\n              online\n              useCases {\n                id\n                key\n                name\n              }\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n            }\n            ')
        variables: Dict[str, object] = {'filter': filter}
        response = self.execute(query=query, operation_name='ListModels', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListModels.model_validate(data)

    def describe_model_admin(self, input: str, **kwargs: Any) -> DescribeModelAdmin:
        query = gql('\n            query DescribeModelAdmin($input: IdOrKey!) {\n              model(idOrKey: $input) {\n                ...ModelDataAdmin\n                backbone {\n                  ...ModelDataAdmin\n                }\n              }\n            }\n\n            fragment ModelDataAdmin on Model {\n              id\n              key\n              name\n              online\n              useCases {\n                id\n                key\n                name\n              }\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='DescribeModelAdmin', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeModelAdmin.model_validate(data)

    def describe_model(self, input: str, **kwargs: Any) -> DescribeModel:
        query = gql('\n            query DescribeModel($input: IdOrKey!) {\n              model(idOrKey: $input) {\n                ...ModelData\n                backbone {\n                  ...ModelData\n                }\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='DescribeModel', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeModel.model_validate(data)

    def list_metrics(self, **kwargs: Any) -> ListMetrics:
        query = gql('\n            query ListMetrics {\n              metrics {\n                ...MetricDataAdmin\n              }\n            }\n\n            fragment MetricDataAdmin on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              useCases {\n                id\n                name\n                key\n                description\n              }\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListMetrics', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListMetrics.model_validate(data)

    def describe_metric_admin(self, input: str, **kwargs: Any) -> DescribeMetricAdmin:
        query = gql('\n            query DescribeMetricAdmin($input: IdOrKey!) {\n              metric(idOrKey: $input) {\n                ...MetricDataAdmin\n              }\n            }\n\n            fragment MetricDataAdmin on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              useCases {\n                id\n                name\n                key\n                description\n              }\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='DescribeMetricAdmin', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeMetricAdmin.model_validate(data)

    def describe_metric(self, input: str, **kwargs: Any) -> DescribeMetric:
        query = gql('\n            query DescribeMetric($input: IdOrKey!) {\n              metric(idOrKey: $input) {\n                ...MetricData\n              }\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='DescribeMetric', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeMetric.model_validate(data)

    def list_ab_campaigns(self, input: AbCampaignFilter, **kwargs: Any) -> ListAbCampaigns:
        query = gql('\n            query ListAbCampaigns($input: AbCampaignFilter!) {\n              abCampaigns(filter: $input) {\n                ...AbCampaignDetailData\n              }\n            }\n\n            fragment AbCampaignCreateData on Abcampaign {\n              id\n              key\n              status\n              beginDate\n            }\n\n            fragment AbCampaignDetailData on Abcampaign {\n              ...AbCampaignCreateData\n              feedbackType\n              trafficSplit\n              endDate\n              metric {\n                ...MetricData\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              models {\n                id\n                key\n                name\n              }\n              feedbacks\n              hasEnoughFeedbacks\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='ListAbCampaigns', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListAbCampaigns.model_validate(data)

    def describe_ab_campaign(self, input: str, **kwargs: Any) -> DescribeAbCampaign:
        query = gql('\n            query DescribeAbCampaign($input: IdOrKey!) {\n              abCampaign(idOrKey: $input) {\n                ...AbCampaignDetailData\n                report {\n                  ...AbCampaignReportData\n                }\n              }\n            }\n\n            fragment AbCampaignCreateData on Abcampaign {\n              id\n              key\n              status\n              beginDate\n            }\n\n            fragment AbCampaignDetailData on Abcampaign {\n              ...AbCampaignCreateData\n              feedbackType\n              trafficSplit\n              endDate\n              metric {\n                ...MetricData\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              models {\n                id\n                key\n                name\n              }\n              feedbacks\n              hasEnoughFeedbacks\n            }\n\n            fragment AbCampaignReportData on AbReport {\n              pValue\n              variants {\n                variant {\n                  id\n                  key\n                  name\n                }\n                interval {\n                  start\n                  middle\n                  end\n                }\n                feedbacks\n                comparisons {\n                  feedbacks\n                  wins\n                  losses\n                  tiesGood\n                  tiesBad\n                  variant {\n                    id\n                    key\n                    name\n                  }\n                }\n              }\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'input': input}
        response = self.execute(query=query, operation_name='DescribeAbCampaign', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeAbCampaign.model_validate(data)

    def list_interactions(self, filter: ListCompletionsFilterInput, page: CursorPageInput, order: Union[Optional[List[OrderPair]], UnsetType]=UNSET, **kwargs: Any) -> ListInteractions:
        query = gql('\n            query ListInteractions($filter: ListCompletionsFilterInput!, $page: CursorPageInput!, $order: [OrderPair!] = [{field: "created_at", order: DESC}]) {\n              completions(filter: $filter, page: $page, order: $order) {\n                totalCount\n                pageInfo {\n                  hasNextPage\n                  endCursor\n                }\n                nodes {\n                  ...CompletionData\n                }\n              }\n            }\n\n            fragment CompletionComparisonFeedbackData on Completion {\n              id\n              completion\n              source\n              model {\n                id\n                key\n                name\n              }\n            }\n\n            fragment CompletionData on Completion {\n              id\n              chatMessages {\n                role\n                content\n              }\n              completion\n              source\n              model {\n                id\n                key\n                name\n              }\n              directFeedbacks {\n                id\n                value\n                metric {\n                  ...MetricData\n                }\n                reason\n                details\n                createdAt\n              }\n              comparisonFeedbacks {\n                id\n                createdAt\n                usecase {\n                  id\n                  key\n                  name\n                }\n                metric {\n                  id\n                  key\n                  name\n                }\n                preferedCompletion {\n                  ...CompletionComparisonFeedbackData\n                }\n                otherCompletion {\n                  ...CompletionComparisonFeedbackData\n                }\n              }\n              labels {\n                key\n                value\n              }\n              metadata {\n                parameters\n                timings\n                usage {\n                  completionTokens\n                  promptTokens\n                  totalTokens\n                }\n                system\n              }\n              createdAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'filter': filter, 'page': page, 'order': order}
        response = self.execute(query=query, operation_name='ListInteractions', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListInteractions.model_validate(data)

    def list_grouped_interactions(self, filter: ListCompletionsFilterInput, group_by: CompletionGroupBy, page: CursorPageInput, order: Union[Optional[List[OrderPair]], UnsetType]=UNSET, **kwargs: Any) -> ListGroupedInteractions:
        query = gql('\n            query ListGroupedInteractions($filter: ListCompletionsFilterInput!, $groupBy: CompletionGroupBy!, $page: CursorPageInput!, $order: [OrderPair!] = [{field: "group", order: ASC}]) {\n              completionsGrouped(\n                groupBy: $groupBy\n                filter: $filter\n                page: $page\n                order: $order\n              ) {\n                totalCount\n                groupBy\n                pageInfo {\n                  hasNextPage\n                  endCursor\n                }\n                nodes {\n                  key\n                  count\n                  directFeedbacksStats {\n                    metric {\n                      ...MetricData\n                    }\n                    feedbacks\n                    average\n                    max\n                    min\n                    stddev\n                    sum\n                  }\n                  completions(page: $page, order: [{field: "created_at", order: DESC}]) {\n                    nodes {\n                      ...CompletionData\n                    }\n                  }\n                }\n              }\n            }\n\n            fragment CompletionComparisonFeedbackData on Completion {\n              id\n              completion\n              source\n              model {\n                id\n                key\n                name\n              }\n            }\n\n            fragment CompletionData on Completion {\n              id\n              chatMessages {\n                role\n                content\n              }\n              completion\n              source\n              model {\n                id\n                key\n                name\n              }\n              directFeedbacks {\n                id\n                value\n                metric {\n                  ...MetricData\n                }\n                reason\n                details\n                createdAt\n              }\n              comparisonFeedbacks {\n                id\n                createdAt\n                usecase {\n                  id\n                  key\n                  name\n                }\n                metric {\n                  id\n                  key\n                  name\n                }\n                preferedCompletion {\n                  ...CompletionComparisonFeedbackData\n                }\n                otherCompletion {\n                  ...CompletionComparisonFeedbackData\n                }\n              }\n              labels {\n                key\n                value\n              }\n              metadata {\n                parameters\n                timings\n                usage {\n                  completionTokens\n                  promptTokens\n                  totalTokens\n                }\n                system\n              }\n              createdAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'filter': filter, 'groupBy': group_by, 'page': page, 'order': order}
        response = self.execute(query=query, operation_name='ListGroupedInteractions', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListGroupedInteractions.model_validate(data)

    def describe_interaction(self, use_case: str, id: Any, **kwargs: Any) -> DescribeInteraction:
        query = gql('\n            query DescribeInteraction($useCase: IdOrKey!, $id: UUID!) {\n              completion(useCase: $useCase, id: $id) {\n                ...CompletionData\n              }\n            }\n\n            fragment CompletionComparisonFeedbackData on Completion {\n              id\n              completion\n              source\n              model {\n                id\n                key\n                name\n              }\n            }\n\n            fragment CompletionData on Completion {\n              id\n              chatMessages {\n                role\n                content\n              }\n              completion\n              source\n              model {\n                id\n                key\n                name\n              }\n              directFeedbacks {\n                id\n                value\n                metric {\n                  ...MetricData\n                }\n                reason\n                details\n                createdAt\n              }\n              comparisonFeedbacks {\n                id\n                createdAt\n                usecase {\n                  id\n                  key\n                  name\n                }\n                metric {\n                  id\n                  key\n                  name\n                }\n                preferedCompletion {\n                  ...CompletionComparisonFeedbackData\n                }\n                otherCompletion {\n                  ...CompletionComparisonFeedbackData\n                }\n              }\n              labels {\n                key\n                value\n              }\n              metadata {\n                parameters\n                timings\n                usage {\n                  completionTokens\n                  promptTokens\n                  totalTokens\n                }\n                system\n              }\n              createdAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'id': id}
        response = self.execute(query=query, operation_name='DescribeInteraction', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeInteraction.model_validate(data)

    def list_users(self, **kwargs: Any) -> ListUsers:
        query = gql('\n            query ListUsers {\n              users {\n                ...UserData\n              }\n            }\n\n            fragment UserData on User {\n              id\n              email\n              name\n              createdAt\n              teams {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListUsers', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListUsers.model_validate(data)

    def me(self, **kwargs: Any) -> Me:
        query = gql('\n            query Me {\n              me {\n                ...UserData\n                apiKeys {\n                  key\n                  createdAt\n                }\n              }\n            }\n\n            fragment UserData on User {\n              id\n              email\n              name\n              createdAt\n              teams {\n                team {\n                  id\n                  key\n                  name\n                  createdAt\n                }\n                role {\n                  id\n                  key\n                  name\n                  createdAt\n                  permissions\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='Me', variables=variables, **kwargs)
        data = self.get_data(response)
        return Me.model_validate(data)

    def list_teams(self, **kwargs: Any) -> ListTeams:
        query = gql('\n            query ListTeams {\n              teams {\n                id\n                key\n                name\n                createdAt\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListTeams', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListTeams.model_validate(data)

    def list_roles(self, **kwargs: Any) -> ListRoles:
        query = gql('\n            query ListRoles {\n              roles {\n                id\n                key\n                name\n                createdAt\n                permissions\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListRoles', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListRoles.model_validate(data)

    def list_permissions(self, **kwargs: Any) -> ListPermissions:
        query = gql('\n            query ListPermissions {\n              permissions\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListPermissions', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListPermissions.model_validate(data)

    def list_harmony_groups(self, **kwargs: Any) -> ListHarmonyGroups:
        query = gql('\n            query ListHarmonyGroups {\n              harmonyGroups {\n                ...HarmonyGroupData\n              }\n            }\n\n            fragment HarmonyGroupData on HarmonyGroup {\n              id\n              key\n              computePool {\n                key\n                name\n              }\n              status\n              url\n              worldSize\n              gpuTypes\n              createdAt\n              onlineModels {\n                ...ModelData\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListHarmonyGroups', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListHarmonyGroups.model_validate(data)

    def list_compute_pools(self, **kwargs: Any) -> ListComputePools:
        query = gql('\n            query ListComputePools {\n              computePools {\n                id\n                key\n                name\n                createdAt\n                capabilities\n                harmonyGroups {\n                  ...HarmonyGroupData\n                }\n              }\n            }\n\n            fragment HarmonyGroupData on HarmonyGroup {\n              id\n              key\n              computePool {\n                key\n                name\n              }\n              status\n              url\n              worldSize\n              gpuTypes\n              createdAt\n              onlineModels {\n                ...ModelData\n              }\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListComputePools', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListComputePools.model_validate(data)

    def list_remote_envs(self, **kwargs: Any) -> ListRemoteEnvs:
        query = gql('\n            query ListRemoteEnvs {\n              remoteEnvs {\n                ...RemoteEnvData\n              }\n            }\n\n            fragment RemoteEnvData on RemoteEnv {\n              id\n              key\n              name\n              url\n              description\n              createdAt\n              version\n              status\n              metadataSchema\n            }\n            ')
        variables: Dict[str, object] = {}
        response = self.execute(query=query, operation_name='ListRemoteEnvs', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListRemoteEnvs.model_validate(data)

    def list_custom_recipes(self, use_case: str, filter: CustomRecipeFilterInput, **kwargs: Any) -> ListCustomRecipes:
        query = gql('\n            query ListCustomRecipes($useCase: IdOrKey!, $filter: CustomRecipeFilterInput!) {\n              customRecipes(useCase: $useCase, filter: $filter) {\n                ...CustomRecipeData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'filter': filter}
        response = self.execute(query=query, operation_name='ListCustomRecipes', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListCustomRecipes.model_validate(data)

    def get_custom_recipe(self, id_or_key: str, use_case: str, **kwargs: Any) -> GetCustomRecipe:
        query = gql('\n            query GetCustomRecipe($idOrKey: IdOrKey!, $useCase: IdOrKey!) {\n              customRecipe(idOrKey: $idOrKey, useCase: $useCase) {\n                ...CustomRecipeData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n            ')
        variables: Dict[str, object] = {'idOrKey': id_or_key, 'useCase': use_case}
        response = self.execute(query=query, operation_name='GetCustomRecipe', variables=variables, **kwargs)
        data = self.get_data(response)
        return GetCustomRecipe.model_validate(data)

    def get_judge(self, id: str, use_case: str, version: Union[Optional[int], UnsetType]=UNSET, **kwargs: Any) -> GetJudge:
        query = gql('\n            query GetJudge($id: IdOrKey!, $useCase: IdOrKey!, $version: Int) {\n              judge(id: $id, useCase: $useCase, version: $version) {\n                ...JudgeData\n              }\n            }\n\n            fragment JudgeData on Judge {\n              id\n              key\n              version\n              name\n              criteria\n              prebuilt\n              examples {\n                input {\n                  role\n                  content\n                }\n                output\n                pass\n                reasoning\n              }\n              capabilities\n              model {\n                ...ModelData\n              }\n              useCaseId\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'id': id, 'useCase': use_case, 'version': version}
        response = self.execute(query=query, operation_name='GetJudge', variables=variables, **kwargs)
        data = self.get_data(response)
        return GetJudge.model_validate(data)

    def list_judges(self, use_case: str, **kwargs: Any) -> ListJudges:
        query = gql('\n            query ListJudges($useCase: IdOrKey!) {\n              judges(useCase: $useCase) {\n                ...JudgeData\n              }\n            }\n\n            fragment JudgeData on Judge {\n              id\n              key\n              version\n              name\n              criteria\n              prebuilt\n              examples {\n                input {\n                  role\n                  content\n                }\n                output\n                pass\n                reasoning\n              }\n              capabilities\n              model {\n                ...ModelData\n              }\n              useCaseId\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case}
        response = self.execute(query=query, operation_name='ListJudges', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListJudges.model_validate(data)

    def list_judge_versions(self, use_case: str, key: str, **kwargs: Any) -> ListJudgeVersions:
        query = gql('\n            query ListJudgeVersions($useCase: IdOrKey!, $key: String!) {\n              judgeVersions(useCase: $useCase, key: $key) {\n                ...JudgeData\n              }\n            }\n\n            fragment JudgeData on Judge {\n              id\n              key\n              version\n              name\n              criteria\n              prebuilt\n              examples {\n                input {\n                  role\n                  content\n                }\n                output\n                pass\n                reasoning\n              }\n              capabilities\n              model {\n                ...ModelData\n              }\n              useCaseId\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case, 'key': key}
        response = self.execute(query=query, operation_name='ListJudgeVersions', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListJudgeVersions.model_validate(data)

    def get_grader(self, id: str, use_case: str, **kwargs: Any) -> GetGrader:
        query = gql('\n            query GetGrader($id: IdOrKey!, $useCase: IdOrKey!) {\n              grader(id: $id, useCase: $useCase) {\n                ...GraderData\n              }\n            }\n\n            fragment GraderData on Grader {\n              id\n              name\n              key\n              locked\n              graderType\n              graderConfig {\n                __typename\n                ... on JudgeConfigOutput {\n                  judgeCriteria: criteria\n                  examples {\n                    input {\n                      role\n                      content\n                    }\n                    output\n                    pass\n                    reasoning\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on PrebuiltConfigOutput {\n                  prebuiltCriteria: criteria {\n                    key\n                    name\n                    feedbackKey\n                    description\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on RemoteConfigOutput {\n                  url\n                  version\n                  description\n                }\n                ... on CustomConfigOutput {\n                  graderDescription: description\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'id': id, 'useCase': use_case}
        response = self.execute(query=query, operation_name='GetGrader', variables=variables, **kwargs)
        data = self.get_data(response)
        return GetGrader.model_validate(data)

    def list_graders(self, use_case: str, **kwargs: Any) -> ListGraders:
        query = gql('\n            query ListGraders($useCase: IdOrKey!) {\n              graders(useCase: $useCase) {\n                ...GraderData\n              }\n            }\n\n            fragment GraderData on Grader {\n              id\n              name\n              key\n              locked\n              graderType\n              graderConfig {\n                __typename\n                ... on JudgeConfigOutput {\n                  judgeCriteria: criteria\n                  examples {\n                    input {\n                      role\n                      content\n                    }\n                    output\n                    pass\n                    reasoning\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on PrebuiltConfigOutput {\n                  prebuiltCriteria: criteria {\n                    key\n                    name\n                    feedbackKey\n                    description\n                  }\n                  model {\n                    ...ModelData\n                  }\n                }\n                ... on RemoteConfigOutput {\n                  url\n                  version\n                  description\n                }\n                ... on CustomConfigOutput {\n                  graderDescription: description\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              metric {\n                ...MetricData\n              }\n              createdAt\n              updatedAt\n            }\n\n            fragment MetricData on Metric {\n              id\n              key\n              name\n              kind\n              description\n              scoringType\n              createdAt\n              hasDirectFeedbacks\n              hasComparisonFeedbacks\n            }\n\n            fragment ModelData on Model {\n              id\n              key\n              name\n              online\n              isExternal\n              providerName\n              isAdapter\n              isTraining\n              createdAt\n              kind\n              size\n              computeConfig {\n                tp\n                kvCacheLen\n                maxSeqLen\n              }\n            }\n            ')
        variables: Dict[str, object] = {'useCase': use_case}
        response = self.execute(query=query, operation_name='ListGraders', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListGraders.model_validate(data)

    def list_jobs(self, page: CursorPageInput, filter: Union[Optional[ListJobsFilterInput], UnsetType]=UNSET, order: Union[Optional[List[OrderPair]], UnsetType]=UNSET, **kwargs: Any) -> ListJobs:
        query = gql('\n            query ListJobs($page: CursorPageInput!, $filter: ListJobsFilterInput, $order: [OrderPair!]) {\n              jobs(page: $page, filter: $filter, order: $order) {\n                totalCount\n                pageInfo {\n                  hasNextPage\n                  hasPreviousPage\n                  startCursor\n                  endCursor\n                }\n                nodes {\n                  ...JobData\n                }\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n\n            fragment JobData on Job {\n              id\n              name\n              status\n              createdAt\n              createdBy {\n                id\n                name\n              }\n              startedAt\n              endedAt\n              durationMs\n              progress\n              error\n              kind\n              stages {\n                name\n                status\n                info {\n                  __typename\n                  ... on TrainingJobStageOutput {\n                    monitoringLink\n                    totalNumSamples\n                    processedNumSamples\n                    checkpoints\n                  }\n                  ... on EvalJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                  ... on BatchInferenceJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              recipe {\n                ...CustomRecipeData\n              }\n              details {\n                args\n                recipeHash\n                artifacts {\n                  id\n                  name\n                  kind\n                  uri\n                  metadata\n                  createdAt\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'page': page, 'filter': filter, 'order': order}
        response = self.execute(query=query, operation_name='ListJobs', variables=variables, **kwargs)
        data = self.get_data(response)
        return ListJobs.model_validate(data)

    def describe_job(self, id: Any, **kwargs: Any) -> DescribeJob:
        query = gql('\n            query DescribeJob($id: UUID!) {\n              job(id: $id) {\n                ...JobData\n              }\n            }\n\n            fragment CustomRecipeData on CustomRecipe {\n              id\n              key\n              name\n              content\n              contentHash\n              editable\n              global\n              builtin\n              inputSchema\n              jsonSchema\n              description\n              labels {\n                key\n                value\n              }\n              createdAt\n              updatedAt\n              createdBy {\n                id\n                name\n                email\n              }\n            }\n\n            fragment JobData on Job {\n              id\n              name\n              status\n              createdAt\n              createdBy {\n                id\n                name\n              }\n              startedAt\n              endedAt\n              durationMs\n              progress\n              error\n              kind\n              stages {\n                name\n                status\n                info {\n                  __typename\n                  ... on TrainingJobStageOutput {\n                    monitoringLink\n                    totalNumSamples\n                    processedNumSamples\n                    checkpoints\n                  }\n                  ... on EvalJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                  ... on BatchInferenceJobStageOutput {\n                    totalNumSamples\n                    processedNumSamples\n                  }\n                }\n              }\n              useCase {\n                id\n                key\n                name\n              }\n              recipe {\n                ...CustomRecipeData\n              }\n              details {\n                args\n                recipeHash\n                artifacts {\n                  id\n                  name\n                  kind\n                  uri\n                  metadata\n                  createdAt\n                }\n              }\n            }\n            ')
        variables: Dict[str, object] = {'id': id}
        response = self.execute(query=query, operation_name='DescribeJob', variables=variables, **kwargs)
        data = self.get_data(response)
        return DescribeJob.model_validate(data)

    def execute_custom_operation(self, *fields: GraphQLField, operation_type: OperationType, operation_name: str) -> Dict[str, Any]:
        selections = self._build_selection_set(fields)
        combined_variables = self._combine_variables(fields)
        variable_definitions = self._build_variable_definitions(combined_variables['types'])
        operation_ast = self._build_operation_ast(selections, operation_type, operation_name, variable_definitions)
        response = self.execute(print_ast(operation_ast), variables=combined_variables['values'], operation_name=operation_name)
        return self.get_data(response)

    def _combine_variables(self, fields: Tuple[GraphQLField, ...]) -> Dict[str, Dict[str, Any]]:
        variables_types_combined = {}
        processed_variables_combined = {}
        for field in fields:
            formatted_variables = field.get_formatted_variables()
            variables_types_combined.update({k: v['type'] for (k, v) in formatted_variables.items()})
            processed_variables_combined.update({k: v['value'] for (k, v) in formatted_variables.items()})
        return {'types': variables_types_combined, 'values': processed_variables_combined}

    def _build_variable_definitions(self, variables_types_combined: Dict[str, str]) -> List[VariableDefinitionNode]:
        return [VariableDefinitionNode(variable=VariableNode(name=NameNode(value=var_name)), type=NamedTypeNode(name=NameNode(value=var_value))) for (var_name, var_value) in variables_types_combined.items()]

    def _build_operation_ast(self, selections: List[SelectionNode], operation_type: OperationType, operation_name: str, variable_definitions: List[VariableDefinitionNode]) -> DocumentNode:
        return DocumentNode(definitions=[OperationDefinitionNode(operation=operation_type, name=NameNode(value=operation_name), variable_definitions=variable_definitions, selection_set=SelectionSetNode(selections=selections))])

    def _build_selection_set(self, fields: Tuple[GraphQLField, ...]) -> List[SelectionNode]:
        return [field.to_ast(idx) for (idx, field) in enumerate(fields)]

    def query(self, *fields: GraphQLField, operation_name: str) -> Dict[str, Any]:
        return self.execute_custom_operation(*fields, operation_type=OperationType.QUERY, operation_name=operation_name)

    def mutation(self, *fields: GraphQLField, operation_name: str) -> Dict[str, Any]:
        return self.execute_custom_operation(*fields, operation_type=OperationType.MUTATION, operation_name=operation_name)