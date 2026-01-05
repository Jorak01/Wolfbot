"""
Central entrypoint for all outbound API clients and helpers.
Import from here to keep the rest of the codebase decoupled from HTTP details.
"""

from .client import ApiClient, ApiConfig
from ..config import API_BASE_URL, API_KEY, API_TIMEOUT

api_client = ApiClient(
    ApiConfig(
        base_url=API_BASE_URL,
        api_key=API_KEY or None,
        timeout=API_TIMEOUT,
    )
)

from .services import fetch_status
from .registry import call_api, API_CALLS
from .tokens import get_token, all_tokens

__all__ = [
    "api_client",
    "ApiClient",
    "ApiConfig",
    "fetch_status",
    "call_api",
    "API_CALLS",
    "get_token",
    "all_tokens",
]
