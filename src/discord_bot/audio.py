"""
Minimal voice controller for YouTube/Spotify playback using yt-dlp + FFmpeg.
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

import discord
from discord.ext import commands
import yt_dlp

YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@dataclass
class Track:
    title: str
    stream_url: str
    webpage_url: str
    duration: Optional[int] = None


class GuildAudioState:
    def __init__(self):
        self.queue: asyncio.Queue[Track] = asyncio.Queue()
        self.voice: Optional[discord.VoiceClient] = None
        self.voice_channel: Optional[discord.VoiceChannel] = None
        self.text_channel: Optional[discord.abc.Messageable] = None
        self.current: Optional[Track] = None
        self.play_lock = asyncio.Lock()


class AudioController:
    """Keeps simple guild-scoped queues and playback lifecycle."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._states: Dict[int, GuildAudioState] = {}

    def _state(self, guild_id: int) -> GuildAudioState:
        if guild_id not in self._states:
            self._states[guild_id] = GuildAudioState()
        return self._states[guild_id]

    async def join(self, ctx: commands.Context) -> discord.VoiceClient:
        """Join the caller's voice channel."""
        if not ctx.guild:
            raise RuntimeError("This command can only be used in a server.")
        if not isinstance(ctx.author, discord.Member):
            raise RuntimeError("Voice channel lookup failed.")
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise RuntimeError("Join a voice channel first.")

        state = self._state(ctx.guild.id)
        voice_channel = ctx.author.voice.channel
        state.voice_channel = voice_channel
        state.text_channel = ctx.channel

        existing = state.voice or discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if existing and existing.is_connected():
            state.voice = existing
            if existing.channel != voice_channel:
                await existing.move_to(voice_channel)
            return existing

        state.voice = await voice_channel.connect()
        return state.voice

    async def leave(self, guild_id: int):
        """Disconnect and clear state."""
        state = self._state(guild_id)
        if state.voice and state.voice.is_connected():
            await state.voice.disconnect()
        state.queue = asyncio.Queue()
        state.voice = None
        state.voice_channel = None
        state.current = None

    async def enqueue(self, ctx: commands.Context, query: str) -> Track:
        """Add a track to the queue and start playback if idle."""
        if not ctx.guild:
            raise RuntimeError("This command can only be used in a server.")

        state = self._state(ctx.guild.id)
        state.text_channel = ctx.channel
        if ctx.author.voice and ctx.author.voice.channel:
            state.voice_channel = ctx.author.voice.channel

        if not state.voice or not state.voice.is_connected():
            await self.join(ctx)

        track = await self._resolve_track(query)
        await state.queue.put(track)
        await self._play_next(ctx.guild.id)
        return track

    async def skip(self, guild_id: int) -> str:
        state = self._state(guild_id)
        if state.voice and state.voice.is_playing():
            state.voice.stop()
            return "Skipped current track."
        return "Nothing is playing."

    async def stop(self, guild_id: int) -> str:
        state = self._state(guild_id)
        while not state.queue.empty():
            try:
                state.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        if state.voice and state.voice.is_playing():
            state.voice.stop()
        state.current = None
        return "Stopped playback and cleared the queue."

    async def _play_next(self, guild_id: int):
        """Pop the next track from the queue and play it."""
        state = self._state(guild_id)
        if not state.voice_channel and (not state.voice or not state.voice.is_connected()):
            return

        async with state.play_lock:
            if state.voice is None or not state.voice.is_connected():
                if state.voice_channel:
                    state.voice = await state.voice_channel.connect()
                else:
                    return

            if state.voice.is_playing() or state.queue.empty():
                return

            track = await state.queue.get()
            state.current = track

            def _after_playback(error: Exception | None):
                # Schedule next track inside the event loop.
                coro = self._handle_after(guild_id, error)
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

            audio_source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    track.stream_url,
                    before_options=FFMPEG_OPTIONS["before_options"],
                    options=FFMPEG_OPTIONS["options"],
                ),
                volume=0.8,
            )
            state.voice.play(audio_source, after=_after_playback)

    async def _handle_after(self, guild_id: int, error: Exception | None):
        state = self._state(guild_id)
        if error:
            print(f"[audio] Playback error: {error}")
        state.current = None
        if not state.queue.empty():
            await self._play_next(guild_id)

    async def _resolve_track(self, query: str) -> Track:
        """Use yt-dlp to resolve YouTube/Spotify URLs or search terms."""
        def _extract():
            with yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS) as ytdl:
                return ytdl.extract_info(query, download=False)

        info = await asyncio.to_thread(_extract)

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        title = info.get("title") or "Unknown title"
        stream_url = info.get("url") or query
        webpage_url = info.get("webpage_url") or query
        duration = info.get("duration")

        return Track(
            title=str(title),
            stream_url=str(stream_url),
            webpage_url=str(webpage_url),
            duration=duration if isinstance(duration, int) else None,
        )

    def now_playing(self, guild_id: int) -> Optional[Track]:
        state = self._state(guild_id)
        return state.current

    def queue_size(self, guild_id: int) -> int:
        state = self._state(guild_id)
        return state.queue.qsize()
