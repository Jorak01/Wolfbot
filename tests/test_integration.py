import re

import pytest

import src
from src import integration


@pytest.mark.asyncio
async def test_get_status_returns_string():
    result = await integration.get_status()
    assert isinstance(result, str)


def test_package_version_format():
    assert isinstance(src.__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", src.__version__) is not None
