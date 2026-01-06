"""
Integration layer for external services or business logic.
"""

from typing import Any, Dict, List

try:
    from src.config import SEARCH_MAX_RESULTS
except ImportError:
    from config import SEARCH_MAX_RESULTS


async def call_api(endpoint: str, **kwargs) -> Any:
    """
    Placeholder API call function.
    Implement actual API calls based on your needs.
    """
    # Placeholder implementation
    if endpoint == "status":
        return "OK"
    elif endpoint == "search":
        return []
    elif endpoint == "generate_image":
        return {"url": "", "revised_prompt": kwargs.get("prompt", "")}
    return {}


async def get_status() -> str:
    """Example call into an external status endpoint."""
    result = await call_api("status")
    return str(result)


async def search_web(query: str, *, max_results: int = SEARCH_MAX_RESULTS) -> List[Dict[str, str]]:
    """
    Run a lightweight search and return a normalized list of results.
    Each entry has title, url, and snippet keys.
    """
    results = await call_api("search", query=query, max_results=max_results)
    # call_api returns either a list of dicts or a string error; normalize to list
    if isinstance(results, str):
        return [{"title": "Search error", "url": "", "snippet": results}]
    return list(results)


async def generate_art(prompt: str) -> Dict[str, Any]:
    """
    Generate AI art via the API layer.
    Returns a dict with url and prompt keys, or an error string in 'error'.
    """
    raw = await call_api("generate_image", prompt=prompt)
    if isinstance(raw, str):
        return {"error": raw}
    return {
        "url": raw.get("url", ""),
        "prompt": raw.get("revised_prompt", prompt),
    }
