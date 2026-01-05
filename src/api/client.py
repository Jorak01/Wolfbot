from dataclasses import dataclass
from typing import Any, Mapping

import httpx


@dataclass
class ApiConfig:
    base_url: str
    api_key: str | None = None
    timeout: float = 10.0


class ApiClient:
    """Lightweight async HTTP client wrapper."""

    def __init__(self, config: ApiConfig):
        self._config = config
        self._client: httpx.AsyncClient | None = None
        if self._config.base_url:
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                headers=self._build_headers(),
                timeout=self._config.timeout,
            )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def _build_headers(
        self,
        token_override: str | None = None,
        extra: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        token = token_override or self._config.api_key
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if extra:
            headers.update(extra)
        return headers

    def _ensure_client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("API client is not configured (missing base URL)")
        return self._client

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        api_key: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        client = self._ensure_client()
        merged_headers = self._build_headers(token_override=api_key, extra=headers)
        response = await client.request(
            method, path, params=params, json=json, headers=merged_headers
        )
        response.raise_for_status()
        return response.json()

    async def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        api_key: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        return await self._request_json(
            "GET", path, params=params, api_key=api_key, headers=headers
        )

    async def post_json(
        self,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        api_key: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        return await self._request_json(
            "POST", path, json=json, api_key=api_key, headers=headers
        )

    async def aclose(self):
        if self._client:
            await self._client.aclose()
