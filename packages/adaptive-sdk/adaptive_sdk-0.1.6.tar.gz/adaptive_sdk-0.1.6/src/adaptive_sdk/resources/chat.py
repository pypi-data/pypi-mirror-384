from __future__ import annotations
import json
from loguru import logger
from uuid import UUID
from typing import (
    Dict,
    List,
    AsyncGenerator,
    Generator,
    Literal,
    overload,
    TYPE_CHECKING,
)
from typing_extensions import override
from adaptive_sdk import input_types
from adaptive_sdk.error_handling import rest_error_handler
from adaptive_sdk.rest import rest_types
from adaptive_sdk.utils import convert_optional_UUID, get_full_model_path

from .base_resource import SyncAPIResource, AsyncAPIResource, UseCaseResource

if TYPE_CHECKING:
    from adaptive_sdk.client import Adaptive, AsyncAdaptive

ROUTE = "/chat/completions"


class Chat(SyncAPIResource, UseCaseResource):  # type: ignore[misc]
    @override
    def __init__(self, client: Adaptive) -> None:
        SyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    @overload
    def create(
        self,
        messages: List[input_types.ChatMessage],
        stream: Literal[False] | None = None,
        model: str | None = None,
        stop: List[str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream_include_usage: bool | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        user: str | UUID | None = None,
        ab_campaign: str | None = None,
        n: int | None = None,
        labels: Dict[str, str] | None = None,
    ) -> rest_types.ChatResponse: ...

    @overload
    def create(
        self,
        messages: List[input_types.ChatMessage],
        stream: Literal[True],
        model: str | None = None,
        stop: List[str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream_include_usage: bool | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        user: str | UUID | None = None,
        ab_campaign: str | None = None,
        n: int | None = None,
        labels: Dict[str, str] | None = None,
    ) -> Generator[rest_types.ChatResponseChunk, None, None]: ...

    def create(
        self,
        messages: List[input_types.ChatMessage],
        stream: bool | None = None,
        model: str | None = None,
        stop: List[str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream_include_usage: bool | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        user: str | UUID | None = None,
        ab_campaign: str | None = None,
        n: int | None = None,
        labels: Dict[str, str] | None = None,
    ) -> rest_types.ChatResponse | Generator[rest_types.ChatResponseChunk, None, None]:
        """
        Create a chat completion.

        Args:
            messages: Input messages, each dict with keys `role` and `content`.
            stream: If `True`, partial message deltas will be returned. If stream is over, chunk.choices will be None.
            model: Target model key for inference. If `None`, the requests will be routed to the use case's default model.
            stop: Sequences or where the API will stop generating further tokens.
            max_tokens: Maximum # of tokens allowed to generate.
            temperature: Sampling temperature.
            top_p: Threshold for top-p sampling.
            stream_include_usage: If set, an additional chunk will be streamed with the token usage statistics for
                the entire request.
            user: ID of user making request. If not `None`, will be logged as metadata for the request.
            ab_campaign: AB test key. If set, request will be guaranteed to count towards AB test results,
                no matter the configured `traffic_split`.
            n: Number of chat completions to generate for each input messages.
            labels: Key-value pairs of interaction labels.

        Examples:
        ```
        # streaming chat request
        stream_response = client.chat.create(
            model="model_key", messages=[{"role": "user", "content": "Hello from SDK"}], stream=True
        )

        print("Streaming response: ", end="", flush=True)
        for chunk in stream_response:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
        ```
        """
        # TODO: figure out what to do with possible completion_id in messages
        input_messages = [rest_types.ChatMessage(**m) for m in messages]
        input = rest_types.ChatInput(
            messages=input_messages,
            model=get_full_model_path(self.use_case_key(use_case), model),
            stream=stream,
            stop=stop,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream_options=rest_types.StreamOptions(include_usage=stream_include_usage),
            session_id=convert_optional_UUID(session_id),
            user=convert_optional_UUID(user),
            ab_campaign=ab_campaign,
            n=n,
            labels=labels,
        )
        if input.stream:
            return self._stream(input)
        r = self._rest_client.post(ROUTE, json=input.model_dump(exclude_none=True))
        rest_error_handler(r)
        return rest_types.ChatResponse.model_validate(r.json())

    def _stream(
        self, input: rest_types.ChatInput
    ) -> Generator[rest_types.ChatResponseChunk, None, None]:
        import httpx_sse

        with httpx_sse.connect_sse(
            self._rest_client, "POST", ROUTE, json=input.model_dump(exclude_none=True)
        ) as event_source:
            for sse in event_source.iter_sse():
                if sse.data == "[DONE]":
                    break
                try:
                    chunk_content = json.loads(sse.data)
                except Exception as e:
                    logger.warning(f"Error with json in chunk: {sse.data}")
                    continue
                yield rest_types.ChatResponseChunk.model_validate(chunk_content)


class AsyncChat(AsyncAPIResource, UseCaseResource):  # type: ignore[misc]
    def __init__(self, client: AsyncAdaptive) -> None:
        AsyncAPIResource.__init__(self, client)
        UseCaseResource.__init__(self, client)

    @overload
    async def create(  # type: ignore[empty-body]
        self,
        messages: List[input_types.ChatMessage],
        stream: Literal[False] | None = None,
        model: str | None = None,
        stop: List[str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream_include_usage: bool | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        user: str | UUID | None = None,
        ab_campaign: str | None = None,
        n: int | None = None,
        labels: Dict[str, str] | None = None,
    ) -> rest_types.ChatResponse: ...

    @overload  # type: ignore[no-redef, misc]
    async def create(
        self,
        messages: List[input_types.ChatMessage],
        stream: Literal[True],
        model: str | None = None,
        stop: List[str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream_include_usage: bool | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        user: str | UUID | None = None,
        ab_campaign: str | None = None,
        n: int | None = None,
        labels: Dict[str, str] | None = None,
    ) -> AsyncGenerator[rest_types.ChatResponseChunk, None]: ...

    async def create(  # type: ignore
        self,
        messages: List[input_types.ChatMessage],
        model: str | None = None,
        stream: bool | None = None,
        stop: List[str] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream_include_usage: bool | None = None,
        session_id: str | UUID | None = None,
        use_case: str | None = None,
        user: str | UUID | None = None,
        ab_campaign: str | None = None,
        n: int | None = None,
        labels: Dict[str, str] | None = None,
    ) -> rest_types.ChatResponse | AsyncGenerator[rest_types.ChatResponseChunk, None]:
        """
        Create a chat completion.

        Args:
            messages: Input messages, each dict with keys `role` and `content`.
            stream: If `True`, partial message deltas will be returned.
            model: Target model key for inference. If `None`, the requests will be routed to the use case's default model.
            stop: Sequences or where the API will stop generating further tokens.
            max_tokens: Maximum # of tokens allowed to generate.
            temperature: Sampling temperature.
            top_p: Threshold for top-p sampling.
            stream_include_usage: If set, an additional chunk will be streamed with the token usaage statistics for
                the entire request.
            user: ID of user making request. If not `None`, will be logged as metadata for the request.
            ab_campaign: AB test key. If set, request will be guaranteed to count towards AB test results,
                no matter the configured `traffic_split`.
            n: Number of chat completions to generate for each input messages.
            labels: Key-value pairs of interaction labels.

        Examples:
        ```
        # async streaming chat request
        async def async_chat_stream():
            stream_response = aclient.chat.create(
                model="model_key", messages=[{"role": "user", "content": "Hello from SDK"}], stream=True
            )

            print("Async chat streaming response: ", end="", flush=True)
            async for chunk in await stream_response:
                if chunk.choices:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
        ```
        """
        input_messages = [rest_types.ChatMessage(**m) for m in messages]
        input = rest_types.ChatInput(
            messages=input_messages,
            model=get_full_model_path(self.use_case_key(use_case), model),
            stream=stream,
            stop=stop,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream_options=rest_types.StreamOptions(include_usage=stream_include_usage),
            session_id=convert_optional_UUID(session_id),
            user=convert_optional_UUID(user),
            ab_campaign=ab_campaign,
            n=n,
            labels=labels,
        )
        if input.stream:
            return self._stream(input)
        r = await self._rest_client.post(
            ROUTE, json=input.model_dump(exclude_none=True)
        )
        rest_error_handler(r)
        return rest_types.ChatResponse.model_validate(r.json())

    async def _stream(
        self, input: rest_types.ChatInput
    ) -> AsyncGenerator[rest_types.ChatResponseChunk, None]:
        import httpx_sse

        async with httpx_sse.aconnect_sse(
            self._rest_client, "POST", ROUTE, json=input.model_dump(exclude_none=True)
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.data == "[DONE]":
                    break
                try:
                    chunk_content = json.loads(sse.data)
                except Exception as e:
                    logger.warning(f"Error with json in chunk: {sse.data}")
                    continue
                yield rest_types.ChatResponseChunk.model_validate(chunk_content)
