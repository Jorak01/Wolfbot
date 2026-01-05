"""
Compatibility shim for legacy imports.
Use src.tokens as the single source of truth.
"""

from ..tokens import TOKEN_ENTRIES, all_tokens, get_token

__all__ = ["TOKEN_ENTRIES", "all_tokens", "get_token"]
