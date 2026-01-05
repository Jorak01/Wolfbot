"""
Compatibility shim for legacy imports.
Now redirects to api_manager.
"""

from api_manager import api_manager

# Backward compatibility functions
def get_token(name: str, fallback_to_default: bool = True):
    """Get token from api_manager."""
    fallback = api_manager.get_token("generic") if fallback_to_default else None
    return api_manager.get_token(name, fallback=fallback)

def all_tokens():
    """Get all tokens from api_manager."""
    return {
        name: config.auth_token or ""
        for name, config in api_manager.get_all_configs().items()
        if config.auth_token
    }

TOKEN_ENTRIES = []  # Legacy support

__all__ = ["TOKEN_ENTRIES", "all_tokens", "get_token"]
