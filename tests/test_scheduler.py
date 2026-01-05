import asyncio

import pytest

from src.discord_bot import scheduler


@pytest.mark.asyncio
async def test_schedule_task_runs():
    hit = {"done": False}

    def _cb():
        hit["done"] = True

    scheduler.schedule_task(0.01, _cb)
    await asyncio.sleep(0.05)
    assert hit["done"] is True


@pytest.mark.asyncio
async def test_cancel_task():
    def _cb():
        raise AssertionError("Should not run")

    task_id = scheduler.schedule_task(60, _cb)
    assert scheduler.cancel_task(task_id) is True
