"""
Lifecycle helpers to centralize Discord bot startup/shutdown and extension management.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import discord
from discord.ext import commands

from ..integrations.twitch_integration import TwitchIntegration

# Extend this list with dotted module paths for your cogs/extensions.
DEFAULT_EXTENSIONS: List[str] = []


async def on_ready(bot: commands.Bot, twitch: TwitchIntegration, extensions: Sequence[str] | None = None):
    """
    Bot startup hook: load extensions and start Twitch sidecar.
    """
    ext_list = list(extensions) if extensions is not None else DEFAULT_EXTENSIONS
    load_extensions(bot, ext_list)
    if twitch:
        await twitch.start()
    print(f"Logged in as {bot.user} (id: {bot.user.id})")  # noqa: T201


async def on_disconnect(bot: commands.Bot):
    """Handle unexpected disconnects."""
    print("Bot disconnected from Discord.")  # noqa: T201


async def graceful_shutdown(bot: commands.Bot, twitch: TwitchIntegration | None = None):
    """
    Close Twitch sessions and Discord connection cleanly.
    """
    if twitch:
        try:
            await twitch.stop()
        except Exception:
            pass
        try:
            await twitch.api.client.aclose()
        except Exception:
            pass
    await bot.close()


async def health_check(bot: commands.Bot, twitch: TwitchIntegration | None = None) -> str:
    """
    Verify Discord readiness and Twitch API reachability.
    """
    discord_ok = bot.is_ready()
    twitch_status = "Twitch check skipped"
    if twitch:
        twitch_status = await twitch.health_check()
    return f"Discord ready: {discord_ok}; {twitch_status}"


def load_extensions(bot: commands.Bot, extensions: Iterable[str]) -> Tuple[list[str], list[tuple[str, str]]]:
    """
    Load a set of extensions. Returns (loaded, failed[(name, error)]).
    """
    loaded: list[str] = []
    failed: list[tuple[str, str]] = []
    for ext in extensions:
        if ext in bot.extensions:
            continue
        try:
            bot.load_extension(ext)
            loaded.append(ext)
        except Exception as exc:
            failed.append((ext, str(exc)))
    return loaded, failed


def reload_extensions(bot: commands.Bot, extensions: Iterable[str]) -> Tuple[list[str], list[tuple[str, str]]]:
    """
    Reload a set of extensions. Returns (reloaded, failed[(name, error)]).
    """
    reloaded: list[str] = []
    failed: list[tuple[str, str]] = []
    for ext in extensions:
        try:
            if ext in bot.extensions:
                bot.reload_extension(ext)
            else:
                bot.load_extension(ext)
            reloaded.append(ext)
        except Exception as exc:
            failed.append((ext, str(exc)))
    return reloaded, failed
