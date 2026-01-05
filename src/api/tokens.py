"""
Token registry for outbound APIs.
- Fill TOKEN_ENTRIES below for a simple array-based setup.
- Optionally override/append via API_TOKENS env (e.g., "service1=tokenA;service2=tokenB")
- Optional fallback via API_KEY as "default".
"""

from typing import Dict, Mapping, Optional

from ..config import API_KEY, API_TOKENS_RAW

# Editable array-style configuration for tokens.
# Add entries like {"name": "service1", "token": "abc123"}.
TOKEN_ENTRIES = [
    # {"name": "status", "token": "replace_me"},
    # {"name": "service2", "token": "replace_me"},
]


def _parse_tokens(raw: str) -> Dict[str, str]:
    tokens: Dict[str, str] = {}
    for chunk in raw.split(";"):
        if not chunk.strip():
            continue
        if "=" in chunk:
            name, value = chunk.split("=", 1)
            tokens[name.strip()] = value.strip()
    return tokens


def _from_entries(entries) -> Dict[str, str]:
    tokens: Dict[str, str] = {}
    for entry in entries:
        name = entry.get("name", "").strip()
        token = entry.get("token", "").strip()
        if name and token:
            tokens[name] = token
    return tokens


_TOKENS: Dict[str, str] = _parse_tokens(API_TOKENS_RAW)

# Merge in array-based entries if not already provided by env.
for name, token in _from_entries(TOKEN_ENTRIES).items():
    _TOKENS.setdefault(name, token)

# Provide a default token using API_KEY if present.
if API_KEY and "default" not in _TOKENS:
    _TOKENS["default"] = API_KEY


def get_token(name: str, *, fallback_to_default: bool = True) -> Optional[str]:
    """
    Return the token for a given service name.
    Optionally fall back to the "default" token if configured.
    """
    if name in _TOKENS:
        return _TOKENS[name]
    if fallback_to_default:
        return _TOKENS.get("default")
    return None


def all_tokens() -> Mapping[str, str]:
    """Expose a read-only view of configured tokens."""
    return dict(_TOKENS)
