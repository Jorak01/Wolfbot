"""
Compatibility shim for legacy imports.
Now redirects to api_manager.
"""
from __future__ import annotations

from api_manager import api_manager


__all__ = ["TOKEN_ENTRIES", "all_tokens", "get_token"]

# Backward compatibility - redirect to api_manager
def get_token(name: str, *, fallback_to_default: bool = True) -> str | None:
    """
    Return the token for a given service name.
    Now delegates to api_manager.
    """
    fallback = api_manager.get_token("generic") if fallback_to_default else None
    return api_manager.get_token(name, fallback=fallback)


def all_tokens() -> dict[str, str]:
    """Expose a read-only view of configured tokens."""
    return {
        name: config.auth_token or ""
        for name, config in api_manager.get_all_configs().items()
        if config.auth_token
    }


# Legacy support - empty entries list
TOKEN_ENTRIES = []
