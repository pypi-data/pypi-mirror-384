import asyncio
from dataclasses import dataclass
from typing import Optional, cast

import httpx

from arcade_asana.constants import ASANA_API_VERSION, ASANA_BASE_URL, ASANA_MAX_CONCURRENT_REQUESTS
from arcade_asana.decorators import clean_asana_response


@dataclass
class AsanaClient:
    auth_token: str
    base_url: str = ASANA_BASE_URL
    api_version: str = ASANA_API_VERSION
    max_concurrent_requests: int = ASANA_MAX_CONCURRENT_REQUESTS
    _semaphore: asyncio.Semaphore | None = None

    def __post_init__(self) -> None:
        self._semaphore = self._semaphore or asyncio.Semaphore(self.max_concurrent_requests)

    def _build_url(self, endpoint: str, api_version: str | None = None) -> str:
        api_version = api_version or self.api_version
        return f"{self.base_url.rstrip('/')}/{api_version.strip('/')}/{endpoint.lstrip('/')}"

    def _set_request_body(self, kwargs: dict, data: dict | None, json_data: dict | None) -> dict:
        if data and json_data:
            raise ValueError("Cannot provide both data and json_data")

        if data:
            kwargs["data"] = data

        elif json_data:
            kwargs["json"] = json_data

        return kwargs

    @clean_asana_response
    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        default_headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
        }
        headers = {**default_headers, **(headers or {})}

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
        }

        if params:
            kwargs["params"] = params

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.get(**kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
        return cast(dict, response.json())

    @clean_asana_response
    async def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        files: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        default_headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
        }

        if files is None and json_data is not None:
            default_headers["Content-Type"] = "application/json"

        headers = {**default_headers, **(headers or {})}

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
        }

        if files is not None:
            kwargs["files"] = files
            if data is not None:
                kwargs["data"] = data
        else:
            kwargs = self._set_request_body(kwargs, data, json_data)

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.post(**kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
        return cast(dict, response.json())

    @clean_asana_response
    async def put(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
        api_version: str | None = None,
    ) -> dict:
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        kwargs = {
            "url": self._build_url(endpoint, api_version),
            "headers": headers,
        }

        kwargs = self._set_request_body(kwargs, data, json_data)

        async with self._semaphore, httpx.AsyncClient() as client:  # type: ignore[union-attr]
            response = await client.put(**kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
        return cast(dict, response.json())

    async def get_current_user(self) -> dict:
        response = await self.get("/users/me")
        return cast(dict, response["data"])
