from abc import ABC, abstractmethod
import asyncio
from adaptive_sdk.external.requests_journal import RequestsJournal
from adaptive_sdk.external.websocket_utils import send_large_text
from fastapi import FastAPI, APIRouter, WebSocket
from fastapi.responses import JSONResponse
from typing import Callable, Any, Generic, Type, TypeVar
from dataclasses import dataclass
import threading
from pydantic import Field
import uvicorn
from loguru import logger

from adaptive_sdk.external.reward_types import (
    ValidatedRequest,
    Response,
    ServerInfo,
    ValidatedBatchedRequest,
    BatchedResponse,
    BaseModel,
)
from adaptive_sdk.external.constants import (
    SCORE_PATH,
    BATCH_SCORE_PATH,
    INFO_PATH,
    METADATA_SCHEMA_PATH,
)


class EmptyMetadata(BaseModel):
    pass


@dataclass
class Route:
    path: str
    endpoint: Callable[..., Any]
    methods: list[str]


META = TypeVar("META", bound=BaseModel)


class RewardServer(ABC, Generic[META]):
    def __init__(
        self,
        port: int,
        metadata_cls: Type[META],
        blocking: bool = True,
        verbose: bool = False,
        request_timeout_s: int = 3_600,
        requests_journal: RequestsJournal | None = None,
    ):
        self.requests_journal = requests_journal
        self.request_timeout_s = request_timeout_s
        self.metadata_cls = metadata_cls
        # need to update the functions with the correct metadata type, otherwise the bound BaseModel is used
        # (see https://github.com/fastapi/fastapi/issues/5874)
        self._score.__annotations__["request"] = ValidatedRequest[metadata_cls]  # type: ignore[valid-type]
        self.batch_score.__annotations__["requests"] = ValidatedBatchedRequest[metadata_cls]  # type: ignore[valid-type]

        self.verbose = verbose
        self.__post_init__()
        self._setup_server(port, blocking)
        self.cleanup()

    def __post_init__(self):
        pass

    def cleanup(self):
        pass

    async def _score(self, request: ValidatedRequest[META]) -> Response:
        if self.verbose:
            request_str = request.model_dump_json(indent=2)
            print(f"Received request: {request_str}")
            res = await self.score(request)
            print(
                f"Finished request : {request_str} with response: {res.model_dump_json(indent=2)}"
            )
            return res
        else:
            return await self.score(request)

    @abstractmethod
    async def score(self, request: ValidatedRequest[META]) -> Response: ...

    async def batch_score(
        self, requests: ValidatedBatchedRequest[META]
    ) -> BatchedResponse:
        tasks = []
        for request in requests.requests:
            tasks.append(self._score(request))
        responses = await asyncio.gather(*tasks)
        return BatchedResponse(responses=responses)

    def get_medata_schema(self) -> JSONResponse:
        json_schema = self.metadata_cls.model_json_schema()
        return JSONResponse(json_schema)

    @abstractmethod
    async def info(self) -> ServerInfo: ...

    def _setup_server(self, port: int, blocking: bool, log_request: bool = False):
        class ThreadServer(uvicorn.Server):
            """ "Easy to kill uvicorn server"""

            def run_in_thread(self):
                self.thread = threading.Thread(target=self.run, daemon=True)
                self.thread.start()

            def stop(self):
                self.should_exit = True
                self.thread.join()

        def get_routes() -> list[Route]:
            routes: list[Route] = []
            routes.append(Route(SCORE_PATH, self._score, methods=["POST"]))
            routes.append(Route(BATCH_SCORE_PATH, self.batch_score, methods=["POST"]))
            routes.append(Route(INFO_PATH, self.info, methods=["GET"]))
            routes.append(
                Route(METADATA_SCHEMA_PATH, self.get_medata_schema, methods=["GET"])
            )
            return routes

        async def score_task(websocket: WebSocket, msg):
            req: ValidatedRequest = ValidatedRequest[self.metadata_cls].model_validate(msg)  # type: ignore
            req_id: int = req.id  # type: ignore
            response = await self._score(req)
            response.id = req_id
            await send_large_text(websocket, response.model_dump_json(), id=req_id)
            # await websocket.send_text(response.model_dump_json())

        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            tasks = set()
            while True:
                try:
                    json = await websocket.receive_json()
                    task = asyncio.create_task(score_task(websocket, json))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)

                except Exception as e:
                    logger.error(f"{e}")
                    break

        router = APIRouter()
        routes = get_routes()

        for route in routes:
            router.add_api_route(route.path, route.endpoint, methods=route.methods)

        app = FastAPI()
        app.include_router(router)

        app.add_api_websocket_route("/ws", websocket_endpoint)

        if self.requests_journal is not None:
            self.requests_journal.add_journalling(app=app)

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            # We do not use workers here. Depending on how the app is launched
            # they are not used. Which makes it misleading.
            ws_ping_timeout=None,
        )
        self.server = ThreadServer(config=config)

        if blocking:
            self.server.run()
        else:
            self.server.run_in_thread()


class MyMetadata(BaseModel):
    scary_letter: str = Field(min_length=1, max_length=1)


class MyRewardServer(RewardServer[MyMetadata]):
    def __init__(self, port=8000, blocking=True):
        super().__init__(port, MyMetadata, blocking, requests_journal=RequestsJournal())

    async def score(self, request: ValidatedRequest[MyMetadata]) -> Response:

        last_completion = request.turns[-1].content
        num_scary_letters = last_completion.count(request.metadata.scary_letter)
        return Response(
            reward=0.0 if request.metadata.scary_letter in last_completion else 1.0,
            metadata={
                "feedback": (
                    "There were no scary letters!"
                    if num_scary_letters == 0
                    else f"There were {num_scary_letters} scary letters!"
                )
            },
        )

    async def info(self) -> ServerInfo:
        return ServerInfo(
            version="1.0", name="My sevice", description="This is a nice description"
        )


class MyNoMetadataRewardServer(RewardServer[EmptyMetadata]):
    def __init__(self, port=8000, blocking=True):
        super().__init__(
            port, EmptyMetadata, blocking, requests_journal=RequestsJournal()
        )

    async def score(self, request: ValidatedRequest[EmptyMetadata]) -> Response:

        last_completion = request.turns[-1].content
        return Response(reward=len(last_completion), metadata={})

    async def info(self) -> ServerInfo:
        return ServerInfo(
            version="1.0", name="My sevice", description="This is a nice description"
        )


if __name__ == "__main__":
    server = MyRewardServer(port=50056)
