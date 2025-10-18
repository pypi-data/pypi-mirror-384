from __future__ import annotations
from typing import get_args, Callable, Literal, Sequence, TYPE_CHECKING

from adaptive_sdk.graphql_client import (
    OpenAIModel,
    OpenAIProviderDataInput,
    GoogleProviderDataInput,
    AzureProviderDataInput,
    ModelProviderDataInput,
    AddExternalModelInput,
    ExternalModelProviderName,
    AttachModel,
    UpdateModelService,
    ModelData,
    JobData,
    ModelServiceData,
    ListModelsModels,
    AddHFModelInput,
    ModelFilter,
    ModelPlacementInput,
    ModelComputeConfigInput,
)
from adaptive_sdk import input_types

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive

provider_config = {
    "open_ai": {
        "provider_data": lambda api_key, model_id: ModelProviderDataInput(
            openAI=OpenAIProviderDataInput(
                apiKey=api_key, externalModelId=OpenAIModel(model_id)
            )
        ),
    },
    "google": {
        "provider_data": lambda api_key, model_id: ModelProviderDataInput(
            google=GoogleProviderDataInput(apiKey=api_key, externalModelId=model_id)
        ),
    },
    "azure": {
        "provider_data": lambda api_key, model_id, endpoint: ModelProviderDataInput(
            azure=AzureProviderDataInput(
                apiKey=api_key, externalModelId=model_id, endpoint=endpoint
            )
        )
    },
}

SupportedHFModels = Literal[
    "deepseek-ai/deepseek-coder-1.3b-base",
    "deepseek-ai/deepseek-coder-6.7b-base",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "tiiuae/falcon-7b",
    "tiiuae/falcon-7b-instruct",
    "tiiuae/falcon-40b",
    "tiiuae/falcon-180B",
    "BAAI/bge-multilingual-gemma2",
    "Locutusque/TinyMistral-248M",
    "mistralai/Mistral-Small-24B-Instruct-2501",
    "baffo32/decapoda-research-llama-7B-hf",
    "princeton-nlp/Sheared-LLaMA-1.3B",
    "meta-llama/Llama-3.1-8B",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "nvidia/Llama3-ChatQA-1.5-70B",
    "Qwen/Qwen2.5-0.5B",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-Coder-7B",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "Qwen/Qwen2.5-Math-7B",
    "Qwen/Qwen2.5-Math-7B-Instruct",
    "Qwen/Qwen2.5-Coder-14B-Instruct",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/QwQ-32B",
    "google/gemma-3-1b-it",
    "google/gemma-3-4b-it",
    "google/gemma-3-12b-it",
    "google/gemma-3-27b-it",
    "Qwen/Qwen3-0.6B",
    "Qwen/Qwen3-1.7B",
    "Qwen/Qwen3-4B",
    "Qwen/Qwen3-8B",
    "Qwen/Qwen3-14B",
    "Qwen/Qwen3-32B",
    "01-ai/Yi-34B",
    "HuggingFaceH4/zephyr-7b-beta",
]


def is_supported_model(model_id: str):
    supported_models = get_args(SupportedHFModels)
    if model_id not in supported_models:
        supported_models_str = "\n".join(supported_models)
        raise ValueError(
            f"Model {model_id} is not supported.\n\nChoose from:\n{supported_models_str}"
        )


class Models(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with models.
    """

    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    def add_hf_model(
        self,
        hf_model_id: SupportedHFModels,
        output_model_name: str,
        output_model_key: str,
        hf_token: str,
        compute_pool: str | None = None,
    ) -> JobData:
        """
        Add model from the HuggingFace Model hub to Adaptive model registry.
        It will take several minutes for the model to be downloaded and converted to Adaptive format.

        Args:
            hf_model_id: The ID of the selected model repo on HuggingFace Model Hub.
            output_model_key: The key that will identify the new model in Adaptive.
            hf_token: Your HuggingFace Token, needed to validate access to gated/restricted model.
        """
        is_supported_model(hf_model_id)
        input = AddHFModelInput(
            modelId=hf_model_id,
            outputModelName=output_model_name,
            outputModelKey=output_model_key,
            hfToken=hf_token,
            computePool=compute_pool,
        )
        return self._gql_client.add_hf_model(input).import_hf_model

    def add_external(
        self,
        name: str,
        external_model_id: str,
        api_key: str,
        provider: Literal["open_ai", "google", "azure"],
        endpoint: str | None = None,
    ) -> ModelData:
        """
        Add proprietary external model to Adaptive model registry.

        Args:
            name: Adaptive name for the new model.
            external_model_id: Should match the model id publicly shared by the model provider.
            api_key: API Key for authentication against external model provider.
            provider: External proprietary model provider.
        """

        provider_data_fn: Callable[..., ModelProviderDataInput] = provider_config[provider]["provider_data"]  # type: ignore[index]
        match provider:
            case "open_ai":
                provider_data = provider_data_fn(api_key, external_model_id)
            case "google":
                provider_data = provider_data_fn(api_key, external_model_id)
            case "azure":
                if not endpoint:
                    raise ValueError(
                        "`endpoint` is required to connect Azure external model."
                    )
                provider_data = provider_data_fn(api_key, external_model_id, endpoint)
            case _:
                raise ValueError(f"Provider {provider} is not supported")

        provider_enum = ExternalModelProviderName(provider.upper())
        input = AddExternalModelInput(
            name=name, provider=provider_enum, providerData=provider_data
        )
        return self._gql_client.add_external_model(input).add_external_model

    def list(
        self, filter: input_types.ModelFilter | None = None
    ) -> Sequence[ListModelsModels]:
        """
        List all models in Adaptive model registry.
        """
        input = ModelFilter.model_validate(filter or {})
        return self._gql_client.list_models(input).models

    def get(self, model) -> ModelData | None:
        """
        Get the details for a model.

        Args:
            model: Model key.
        """
        return self._gql_client.describe_model(input=model).model

    def attach(
        self,
        model: str,
        wait: bool = False,
        make_default: bool = False,
        use_case: str | None = None,
        placement: input_types.ModelPlacementInput | None = None,
    ) -> ModelServiceData:
        """
        Attach a model to the client's use case.

        Args:
            model: Model key.
            wait: If the model is not deployed already, attaching it to the use case will automatically deploy it.
                If `True`, this call blocks until model is `Online`.
            make_default: Make the model the use case's default on attachment.
        """
        input = AttachModel(
            model=model,
            useCase=self.use_case_key(use_case),
            attached=True,
            wait=wait,
            placement=(
                ModelPlacementInput.model_validate(placement) if placement else None
            ),
        )
        result = self._gql_client.attach_model_to_use_case(input).attach_model
        if make_default:
            result = self.update(model=model, is_default=make_default)  # type: ignore[assignment]
        return result

    def detach(
        self,
        model: str,
        use_case: str | None = None,
    ) -> ModelServiceData:
        """
        Detach model from client's use case.

        Args:
            model: Model key.
        """
        return self.update(model=model, attached=False, use_case=use_case)

    def update_compute_config(
        self,
        model: str,
        compute_config: input_types.ModelComputeConfigInput,
    ) -> ModelData:
        """
        Update compute config of model.
        """
        return self._gql_client.update_model_compute_config(
            id_or_key=model,
            input=ModelComputeConfigInput.model_validate(compute_config),
        ).update_model_compute_config

    def update(
        self,
        model: str,
        is_default: bool | None = None,
        attached: bool | None = None,
        desired_online: bool | None = None,
        use_case: str | None = None,
        placement: input_types.ModelPlacementInput | None = None,
    ) -> ModelServiceData:
        """
        Update config of model attached to client's use case.

        Args:
            model: Model key.
            is_default: Change the selection of the model as default for the use case.
                `True` to promote to default, `False` to demote from default. If `None`, no changes are applied.
            attached: Whether model should be attached or detached to/from use case. If `None`, no changes are applied.
            desired_online: Turn model inference on or off for the client use case.
                This does not influence the global status of the model, it is use case-bounded.
                If `None`, no changes are applied.

        """
        input = UpdateModelService(
            useCase=self.use_case_key(use_case),
            modelService=model,
            isDefault=is_default,
            attached=attached,
            desiredOnline=desired_online,
            placement=(
                ModelPlacementInput.model_validate(placement) if placement else None
            ),
        )
        return self._gql_client.update_model(input).update_model_service

    def deploy(self, model: str, wait: bool = False) -> str:
        """
        Deploy a model, loading it to memory and making it ready for inference.

        Args:
            model: Model key.
            wait: If `True`, call block until model is in `Online` state.
        """
        return self._gql_client.deploy_model(id_or_key=model, wait=wait).deploy_model

    def terminate(self, model: str, force: bool = False) -> str:
        """
        Terminate model, removing it from memory and making it unavailable to all use cases.

        Args:
            model: Model key.
            force: If model is attached to several use cases, `force` must equal `True` in order
                for the model to be terminated.
        """
        return self._gql_client.terminate_model(
            id_or_key=model, force=force
        ).terminate_model


class AsyncModels(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    """
    Resource to interact with models.
    """

    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    async def add_hf_model(
        self,
        hf_model_id: SupportedHFModels,
        output_model_name: str,
        output_model_key: str,
        hf_token: str,
        compute_pool: str | None = None,
    ) -> JobData:
        """
        Add model from the HuggingFace Model hub to Adaptive model registry.
        It will take several minutes for the model to be downloaded and converted to Adaptive format.

        Args:
            hf_model_id: The ID of the selected model repo on HuggingFace Model Hub.
            output_model_key: The key that will identify the new model in Adaptive.
            hf_token: Your HuggingFace Token, needed to validate access to gated/restricted model.
        """
        is_supported_model(hf_model_id)
        input = AddHFModelInput(
            modelId=hf_model_id,
            outputModelName=output_model_name,
            outputModelKey=output_model_key,
            hfToken=hf_token,
            computePool=compute_pool,
        )
        result = await self._gql_client.add_hf_model(input)
        return result.import_hf_model

    async def add_external(
        self,
        name: str,
        external_model_id: str,
        api_key: str,
        provider: Literal["open_ai", "google", "azure"],
        endpoint: str | None = None,
    ) -> ModelData:
        """
        Add proprietary external model to Adaptive model registry.

        Args:
            name: Adaptive name for the new model.
            external_model_id: Should match the model id publicly shared by the model provider.
            api_key: API Key for authentication against external model provider.
            provider: External proprietary model provider.
        """
        provider_data_fn: Callable[..., ModelProviderDataInput] = provider_config[provider]["provider_data"]  # type: ignore[index]
        match provider:
            case "open_ai":
                provider_data = provider_data_fn(api_key, external_model_id)
            case "google":
                provider_data = provider_data_fn(api_key, external_model_id)
            case "azure":
                if not endpoint:
                    raise ValueError(
                        "`endpoint` is required to connect Azure external model."
                    )
                provider_data = provider_data_fn(api_key, external_model_id, endpoint)
            case _:
                raise ValueError(f"Provider {provider} is not supported")

        provider_enum = ExternalModelProviderName(provider.upper())
        input = AddExternalModelInput(
            name=name, provider=provider_enum, providerData=provider_data
        )
        result = await self._gql_client.add_external_model(input)
        return result.add_external_model

    async def list(
        self, filter: input_types.ModelFilter | None = None
    ) -> Sequence[ListModelsModels]:
        """
        List all models in Adaptive model registry.
        """
        input = ModelFilter.model_validate(filter or {})
        return (await self._gql_client.list_models(input)).models

    async def get(self, model) -> ModelData | None:
        """
        Get the details for a model.

        Args:
            model: Model key.
        """
        return (await self._gql_client.describe_model(input=model)).model

    async def attach(
        self,
        model: str,
        wait: bool = True,
        make_default: bool = False,
        use_case: str | None = None,
        placement: input_types.ModelPlacementInput | None = None,
    ) -> ModelServiceData:
        """
        Attach a model to the client's use case.

        Args:
            model: Model key.
            wait: If the model is not deployed already, attaching it to the use case will automatically deploy it.
                If `True`, this call blocks until model is `Online`.
            make_default: Make the model the use case's default on attachment.
        """
        input = AttachModel(
            model=model,
            useCase=self.use_case_key(use_case),
            attached=True,
            wait=wait,
            placement=(
                ModelPlacementInput.model_validate(placement) if placement else None
            ),
        )
        result = await self._gql_client.attach_model_to_use_case(input)
        result = result.attach_model
        if make_default:
            result = await self.update(model=model, is_default=make_default)  # type: ignore[assignment]
        return result

    async def detach(
        self,
        model: str,
        use_case: str | None = None,
    ) -> ModelServiceData:
        """
        Detach model from client's use case.

        Args:
            model: Model key.
        """
        return await self.update(model=model, attached=False, use_case=use_case)

    async def update_compute_config(
        self,
        model: str,
        compute_config: input_types.ModelComputeConfigInput,
    ) -> ModelData:
        """
        Update compute config of model.
        """
        return (
            await self._gql_client.update_model_compute_config(
                id_or_key=model,
                input=ModelComputeConfigInput.model_validate(compute_config),
            )
        ).update_model_compute_config

    async def update(
        self,
        model: str,
        is_default: bool | None = None,
        attached: bool | None = None,
        desired_online: bool | None = None,
        use_case: str | None = None,
        placement: input_types.ModelPlacementInput | None = None,
    ) -> ModelServiceData:
        """
        Update config of model attached to client's use case.

        Args:
            model: Model key.
            is_default: Change the selection of the model as default for the use case.
                `True` to promote to default, `False` to demote from default. If `None`, no changes are applied.
            attached: Whether model should be attached or detached to/from use case. If `None`, no changes are applied.
            desired_online: Turn model inference on or off for the client use case.
                This does not influence the global status of the model, it is use case-bounded.
                If `None`, no changes are applied.

        """
        input = UpdateModelService(
            useCase=self.use_case_key(use_case),
            modelService=model,
            isDefault=is_default,
            attached=attached,
            desiredOnline=desired_online,
            placement=(
                ModelPlacementInput.model_validate(placement) if placement else None
            ),
        )
        result = await self._gql_client.update_model(input)
        return result.update_model_service

    async def deploy(self, model: str, wait: bool = False) -> str:
        """
        Deploy a model, loading it to memory and making it ready for inference.

        Args:
            model: Model key.
            wait: If `True`, call block until model is in `Online` state.
        """
        return (
            await self._gql_client.deploy_model(id_or_key=model, wait=wait)
        ).deploy_model

    async def terminate(self, model: str, force: bool = False) -> str:
        """
        Terminate model, removing it from memory and making it unavailable to all use cases.

        Args:
            model: Model key.
            force: If model is attached to several use cases, `force` must equal `True` in order
                for the model to be terminated.
        """
        return (
            await self._gql_client.terminate_model(id_or_key=model, force=force)
        ).terminate_model
