"""
Integration layer for external services or business logic.
Keep this module thin by delegating HTTP details to src/api/.
"""

from .api import call_api


async def get_status() -> str:
    """Example call into an external status endpoint."""
    result = await call_api("status")
    return str(result)
