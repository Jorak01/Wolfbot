import pytest

from src import integration


@pytest.mark.asyncio
async def test_get_status_returns_string():
    result = await integration.get_status()
    assert isinstance(result, str)
