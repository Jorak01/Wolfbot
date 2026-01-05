"""
Scheduling and automation helpers using asyncio tasks.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import Awaitable, Callable, Dict, Optional

import discord

Callback = Callable[[], Awaitable[None]] | Callable[[], None]

_TASKS: Dict[int, asyncio.Task] = {}
_NEXT_ID = 1


def _next_task_id() -> int:
    global _NEXT_ID
    task_id = _NEXT_ID
    _NEXT_ID += 1
    return task_id


async def _run_callback(callback: Callback):
    result = callback()
    if asyncio.iscoroutine(result):
        await result


def schedule_task(run_at: dt.datetime | float, callback: Callback) -> int:
    """
    Schedule a callback to run at a datetime or after a delay in seconds.
    Returns a task id for cancellation.
    """
    if isinstance(run_at, dt.datetime):
        delay = max(0.0, (run_at - dt.datetime.now(tz=run_at.tzinfo)).total_seconds())
    else:
        delay = float(run_at)

    async def _runner():
        try:
            await asyncio.sleep(delay)
            await _run_callback(callback)
        finally:
            _TASKS.pop(task_id, None)

    task_id = _next_task_id()
    _TASKS[task_id] = asyncio.create_task(_runner())
    return task_id


def cancel_task(task_id: int) -> bool:
    task = _TASKS.pop(task_id, None)
    if not task:
        return False
    task.cancel()
    return True


def interval_task(seconds: float, callback: Callback) -> int:
    """
    Run a callback every `seconds` until canceled.
    Returns a task id for cancellation.
    """

    async def _runner():
        try:
            while True:
                await asyncio.sleep(seconds)
                await _run_callback(callback)
        finally:
            _TASKS.pop(task_id, None)

    task_id = _next_task_id()
    _TASKS[task_id] = asyncio.create_task(_runner())
    return task_id


def daily_task_runner(callback: Callback, *, hour: int = 0, minute: int = 0, second: int = 0) -> int:
    """
    Run a callback daily at the given time (server local time).
    Returns a task id for cancellation.
    """

    async def _runner():
        try:
            while True:
                now = dt.datetime.now()
                target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
                if target <= now:
                    target = target + dt.timedelta(days=1)
                delay = (target - now).total_seconds()
                await asyncio.sleep(delay)
                await _run_callback(callback)
        finally:
            _TASKS.pop(task_id, None)

    task_id = _next_task_id()
    _TASKS[task_id] = asyncio.create_task(_runner())
    return task_id


async def temporary_message(channel: discord.abc.Messageable, content: str, duration: float):
    """
    Send a message and delete it after `duration` seconds.
    """
    message: Optional[discord.Message] = None
    try:
        message = await channel.send(content)
        await asyncio.sleep(duration)
        await message.delete()
    except Exception:
        # Swallow errors (e.g., missing permissions or already deleted)
        pass
