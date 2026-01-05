"""
Central entrypoint for all outbound API clients and helpers.
Import from here to keep the rest of the codebase decoupled from HTTP details.
"""

from openai import AsyncOpenAI

from .client import ApiClient, ApiConfig
from ..config import (
    API_BASE_URL,
    API_KEY,
    API_TIMEOUT,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_IMAGE_MODEL,
)
from tokens import get_token, all_tokens

api_client = ApiClient(
    ApiConfig(
        base_url=API_BASE_URL,
        api_key=API_KEY or None,
        timeout=API_TIMEOUT,
    )
)

openai_client: AsyncOpenAI | None = None
if OPENAI_API_KEY:
    openai_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL or None,
    )

from .services import fetch_status
from .registry import call_api, API_CALLS

__all__ = [
    "api_client",
    "ApiClient",
    "ApiConfig",
    "fetch_status",
    "call_api",
    "API_CALLS",
    "openai_client",
    "OPENAI_MODEL",
    "OPENAI_IMAGE_MODEL",
    "get_token",
    "all_tokens",
]
