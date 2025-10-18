from abc import ABC, abstractmethod
import os
from enum import Enum
from typing import Optional, Dict
import httpx
from urllib.parse import urlparse

from .graphql_client import GQLClient, AsyncGQLClient
from .error_handling import graphql_multi_error_handler


def get_version():
    import importlib

    return importlib.import_module("adaptive_sdk").__version__


class Routes(Enum):
    GQL = "/api/graphql"
    REST = "/api/v1"


def _get_api_key(api_key: Optional[str] = None) -> str:
    if api_key:
        return api_key

    env_api_key = os.environ.get("ADAPTIVE_API_KEY")
    if env_api_key:
        return env_api_key

    raise ValueError("API key not found. Please provide an API KEY or set ADAPTIVE_API_KEY environment variable.")


def is_valid_url(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme) and bool(parsed_url.netloc)


class BaseSyncClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        default_headers: Dict[str, str] | None = None,
        timeout_secs: float = 90.0,
    ):
        """
        Construct a new synchronous client instance.
        """
        if not base_url:
            raise ValueError("base_url must be provided")
        else:
            if is_valid_url(base_url):
                base_url = base_url.rstrip("/")
            else:
                raise ValueError(
                    f"Provided base_url {base_url} is invalid. It should be a well-formed url like https://api-adaptive-ml.com"
                )

        self.api_key = _get_api_key(api_key)
        self.base_url = base_url
        custom_headers = (default_headers or {}).copy()
        headers = {
            **custom_headers,
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"adaptive_sdk/{get_version()}",
        }
        self._gql_client = GQLClient(base_url + Routes.GQL.value, headers=headers)
        self._gql_client.get_data = graphql_multi_error_handler(self._gql_client.get_data)  # type: ignore[method-assign]

        timeout = httpx.Timeout(timeout=timeout_secs)

        self._gql_client.http_client.timeout = timeout
        self._rest_client = httpx.Client(headers=headers, base_url=base_url + Routes.REST.value, timeout=timeout)

    def close(self) -> None:
        self._rest_client.close()
        self._gql_client.http_client.close()


class BaseAsyncClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        default_headers: Dict[str, str] | None = None,
        timeout_secs: float = 90.0,
    ):
        """
        Construct a new asynchronous client instance.
        """
        if not base_url:
            raise ValueError("base_url must be provided")
        else:
            if is_valid_url(base_url):
                base_url = base_url.rstrip("/")
            else:
                raise ValueError(
                    f"Provided base_url {base_url} is invalid. It should be a well-formed url like https://api.adaptive-ml.com"
                )

        self.api_key = _get_api_key(api_key)
        self.base_url = base_url
        custom_headers = (default_headers or {}).copy()
        headers = {
            **custom_headers,
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"adaptive_sdk/{get_version()}",
        }

        self._gql_client = AsyncGQLClient(base_url + Routes.GQL.value, headers=headers)
        self._gql_client.get_data = graphql_multi_error_handler(self._gql_client.get_data)  # type: ignore[method-assign]

        timeout = httpx.Timeout(timeout=timeout_secs)
        self._gql_client.http_client.timeout = timeout
        self._rest_client = httpx.AsyncClient(headers=headers, base_url=base_url + Routes.REST.value, timeout=timeout)

    async def close(self) -> None:
        await self._rest_client.aclose()
        await self._gql_client.http_client.aclose()


class UseCaseClient(ABC):
    @property
    @abstractmethod
    def default_use_case(self) -> str | None:
        """Get the current default use case key."""
        pass

    @abstractmethod
    def set_default_use_case(self, use_case: str) -> None:
        """Set the default use case key."""
        pass
