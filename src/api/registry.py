"""
Registry mapping API call names to callables.
Add new functions in services.py (or other modules) and register them here.
"""

from typing import Any, Awaitable, Callable, Dict

from .services import fetch_status

ApiCallable = Callable[..., Awaitable[Any]]

# Simple mapping of name -> async function.
API_CALLS: Dict[str, ApiCallable] = {
    "status": fetch_status,
}


async def call_api(name: str, *args, **kwargs) -> Any:
    """Dispatch to a registered API call by name."""
    try:
        handler = API_CALLS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown API call '{name}'") from exc
    return await handler(*args, **kwargs)
