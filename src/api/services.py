"""
High-level API operations live here.
Keep HTTP details inside ApiClient; expose simple functions for callers.
"""

from typing import Any, Mapping

from . import api_client
from .tokens import get_token


async def fetch_status() -> str:
    """
    Example status call. Replace path/handling with your real endpoint.
    """
    if not api_client.is_configured:
        return "API client not configured; using stub status."

    try:
        token = get_token("status")
        payload: Mapping[str, Any] = await api_client.get_json(
            "/status", api_key=token
        )
    except Exception as exc:
        return f"Status check failed: {exc}"

    return str(payload.get("message") or payload or "Status endpoint responded")
