"""
Twitch <-> Discord integration (lightweight stub).
Provides stream state, presence helpers, and chat relay placeholders.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Optional

import discord
from discord.ext import commands

from config import (
    TWITCH_ACCESS_TOKEN,
    TWITCH_ANNOUNCE_CHANNEL_ID,
    TWITCH_BROADCASTER_ID,
    TWITCH_CHANNEL_NAME,
    TWITCH_CLIENT_ID,
    TWITCH_EVENT_LOG_CHANNEL_ID,
    TWITCH_MONITOR_INTERVAL,
)


def _now_utc() -> dt.datetime:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)


@dataclass
class StreamState:
    is_live: bool = False
    title: str = ""
    game_name: str = ""
    started_at: Optional[dt.datetime] = None
    viewer_count: int = 0
    peak_viewers: int = 0


class _ApiStub:
    """Minimal stub to satisfy lifecycle shutdown hooks."""

    def __init__(self):
        self.client = SimpleNamespace(aclose=self._noop_async)

    async def _noop_async(self):
        return None


class TwitchIntegration:
    """
    Simplified Twitch integration to keep the bot running with the new folder layout.
    Real API calls can be reintroduced as needed.
    """

    def __init__(self, bot: commands.Bot | None = None):
        self.bot = bot
        self.state = StreamState()
        self.api = _ApiStub()

    async def start(self):
        # Placeholder: could start monitor tasks here.
        await self.update_presence_status()

    async def stop(self):
        # Placeholder: stop background tasks if added.
        return

    async def check_stream_live(self, channel_id: Optional[str] = None) -> bool:
        # Stub: mark offline by default.
        self.state.is_live = False
        return self.state.is_live

    def stream_uptime(self) -> str:
        if not self.state.is_live or not self.state.started_at:
            return "Stream is offline."
        delta = _now_utc() - self.state.started_at
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"Uptime: {hours}h {minutes}m"

    def stream_game_category(self) -> str:
        return self.state.game_name or "Unknown"

    def create_stream_embed(self, live: bool = True) -> discord.Embed:
        status = "LIVE" if live else "OFFLINE"
        color = discord.Color.green() if live else discord.Color.red()
        embed = discord.Embed(
            title=f"{status}: {self.state.title or 'Stream'}",
            description=f"Playing {self.state.game_name or 'Unknown'}",
            color=color,
            timestamp=_now_utc(),
        )
        embed.add_field(name="Uptime", value=self.stream_uptime(), inline=True)
        embed.add_field(name="Viewers", value=str(self.state.viewer_count), inline=True)
        return embed

    async def stream_stats_summary(self) -> str:
        uptime = self.stream_uptime()
        return (
            f"{uptime}\n"
            f"Current viewers: {self.state.viewer_count}\n"
            f"Peak viewers: {self.state.peak_viewers}\n"
            f"Followers: N/A\n"
            f"Subscribers: N/A"
        )

    async def relay_discord_chat_to_twitch(self, author: str, message: str):
        # Placeholder for chat relay; no-op if token missing.
        if not TWITCH_ACCESS_TOKEN:
            return
        # In a full implementation, send to Twitch chat here.
        return

    async def get_follow_count(self) -> Optional[int]:
        return None

    async def get_subscriber_count(self) -> Optional[int]:
        return None

    async def health_check(self) -> str:
        if not TWITCH_ACCESS_TOKEN or not TWITCH_CLIENT_ID or not TWITCH_BROADCASTER_ID:
            return "Twitch API is not configured."
        return "Twitch + Discord integrations are reachable (stubbed)."

    async def update_presence_status(self):
        if not self.bot:
            return
        if self.state.is_live:
            activity = discord.Streaming(
                name=self.state.title or "Streaming",
                url=f"https://twitch.tv/{TWITCH_CHANNEL_NAME or 'twitch'}",
            )
        else:
            activity = discord.Game("Idle")
        await self.bot.change_presence(activity=activity)
