"""
Spotify integration for Discord bot.
Provides currently playing track info, playlist management, music search, and voice playback.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List, Dict

import discord
from discord.ext import commands

from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_REFRESH_TOKEN,
)


class LoopMode(Enum):
    """Loop modes for music playback."""
    OFF = 0
    TRACK = 1
    QUEUE = 2


@dataclass
class SpotifyTrack:
    """Represents a Spotify track."""
    name: str
    artist: str
    album: str
    duration_ms: int
    url: str
    image_url: Optional[str] = None
    preview_url: Optional[str] = None
    is_playing: bool = False
    progress_ms: int = 0


class SpotifyIntegration:
    """
    Spotify integration for Discord bot.
    Uses spotipy library for API interactions and voice playback.
    """

    def __init__(self, bot: commands.Bot | None = None):
        self.bot = bot
        self.sp = None
        self._initialize_client()
        
        # Voice playback state
        self.voice_client: Optional[discord.VoiceClient] = None
        self.current_track: Optional[Dict[str, Any]] = None
        self.queue: List[Dict[str, Any]] = []
        self.loop_mode: LoopMode = LoopMode.OFF
        self.is_paused: bool = False
        self.volume: float = 0.5

    def _initialize_client(self):
        """Initialize Spotify client if credentials are available."""
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            return

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth

            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI or "http://localhost:8888/callback",
                scope="user-read-currently-playing user-read-playback-state user-top-read user-library-read playlist-read-private",
            )

            # If we have a refresh token, use it to get an access token
            if SPOTIFY_REFRESH_TOKEN:
                try:
                    token_info = auth_manager.refresh_access_token(SPOTIFY_REFRESH_TOKEN)
                    # Create Spotify client with the refreshed token directly
                    self.sp = spotipy.Spotify(auth=token_info['access_token'])
                except Exception:
                    # Fall back to using auth_manager if refresh fails
                    self.sp = spotipy.Spotify(auth_manager=auth_manager)
            else:
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except ImportError:
            print("Warning: spotipy not installed. Install with: pip install spotipy")
        except Exception as e:
            print(f"Warning: Could not initialize Spotify client: {e}")

    async def get_current_track(self) -> Optional[SpotifyTrack]:
        """Get the currently playing track."""
        if not self.sp:
            return None

        try:
            current = self.sp.current_playback()
            if not current or not current.get("item"):
                return None

            item = current["item"]
            artists = ", ".join([artist["name"] for artist in item.get("artists", [])])
            images = item.get("album", {}).get("images", [])
            image_url = images[0]["url"] if images else None

            return SpotifyTrack(
                name=item.get("name", "Unknown"),
                artist=artists,
                album=item.get("album", {}).get("name", "Unknown"),
                duration_ms=item.get("duration_ms", 0),
                url=item.get("external_urls", {}).get("spotify", ""),
                image_url=image_url,
                preview_url=item.get("preview_url"),
                is_playing=current.get("is_playing", False),
                progress_ms=current.get("progress_ms", 0),
            )
        except Exception as e:
            print(f"Error getting current track: {e}")
            return None

    async def search_track(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for tracks on Spotify."""
        if not self.sp:
            return []

        try:
            results = self.sp.search(q=query, type="track", limit=limit)
            tracks = []
            
            if not results:
                return []
            
            for item in results.get("tracks", {}).get("items", []):
                artists = ", ".join([artist["name"] for artist in item.get("artists", [])])
                tracks.append({
                    "name": item.get("name", "Unknown"),
                    "artist": artists,
                    "album": item.get("album", {}).get("name", "Unknown"),
                    "url": item.get("external_urls", {}).get("spotify", ""),
                    "duration_ms": item.get("duration_ms", 0),
                })
            
            return tracks
        except Exception as e:
            print(f"Error searching tracks: {e}")
            return []

    async def get_top_tracks(self, time_range: str = "medium_term", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get user's top tracks.
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
        """
        if not self.sp:
            return []

        try:
            results = self.sp.current_user_top_tracks(time_range=time_range, limit=limit)
            tracks = []
            
            if not results:
                return []
            
            for item in results.get("items", []):
                artists = ", ".join([artist["name"] for artist in item.get("artists", [])])
                tracks.append({
                    "name": item.get("name", "Unknown"),
                    "artist": artists,
                    "album": item.get("album", {}).get("name", "Unknown"),
                    "url": item.get("external_urls", {}).get("spotify", ""),
                })
            
            return tracks
        except Exception as e:
            print(f"Error getting top tracks: {e}")
            return []

    async def get_top_artists(self, time_range: str = "medium_term", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get user's top artists.
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)
        """
        if not self.sp:
            return []

        try:
            results = self.sp.current_user_top_artists(time_range=time_range, limit=limit)
            artists = []
            
            if not results:
                return []
            
            for item in results.get("items", []):
                genres = ", ".join(item.get("genres", [])[:3])  # First 3 genres
                artists.append({
                    "name": item.get("name", "Unknown"),
                    "genres": genres or "N/A",
                    "url": item.get("external_urls", {}).get("spotify", ""),
                    "followers": item.get("followers", {}).get("total", 0),
                })
            
            return artists
        except Exception as e:
            print(f"Error getting top artists: {e}")
            return []

    async def get_playlists(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's playlists."""
        if not self.sp:
            return []

        try:
            results = self.sp.current_user_playlists(limit=limit)
            playlists = []
            
            if not results:
                return []
            
            for item in results.get("items", []):
                playlists.append({
                    "name": item.get("name", "Unknown"),
                    "tracks": (item.get("tracks") or {}).get("total", 0),
                    "url": (item.get("external_urls") or {}).get("spotify", ""),
                    "owner": (item.get("owner") or {}).get("display_name", "Unknown"),
                })
            
            return playlists
        except Exception as e:
            print(f"Error getting playlists: {e}")
            return []

    def create_now_playing_embed(self, track: SpotifyTrack) -> discord.Embed:
        """Create a rich embed for the currently playing track."""
        status = "▶️ Now Playing" if track.is_playing else "⏸️ Paused"
        
        embed = discord.Embed(
            title=status,
            description=f"**{track.name}**",
            color=discord.Color.green() if track.is_playing else discord.Color.orange(),
            url=track.url,
        )
        
        embed.add_field(name="Artist", value=track.artist, inline=True)
        embed.add_field(name="Album", value=track.album, inline=True)
        
        # Calculate progress
        if track.duration_ms > 0:
            duration_sec = track.duration_ms // 1000
            progress_sec = track.progress_ms // 1000
            duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
            progress_str = f"{progress_sec // 60}:{progress_sec % 60:02d}"
            embed.add_field(name="Progress", value=f"{progress_str} / {duration_str}", inline=True)
        
        if track.image_url:
            embed.set_thumbnail(url=track.image_url)
        
        embed.set_footer(text="Spotify", icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/200px-Spotify_logo_without_text.svg.png")
        
        return embed

    async def health_check(self) -> str:
        """Check if Spotify integration is working."""
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            return "Spotify API is not configured (missing credentials)."
        
        if not self.sp:
            return "Spotify client failed to initialize."
        
        try:
            # Try to get current user info
            user = self.sp.current_user()
            if user:
                return f"Spotify integration is active (logged in as: {user.get('display_name', 'Unknown')})"
        except Exception as e:
            return f"Spotify integration error: {e}"
        
        return "Spotify integration status unknown."

    # =============================================================================
    # Voice Channel & Playback Control Methods
    # =============================================================================

    async def join_voice(self, channel: discord.VoiceChannel) -> str:
        """Join a voice channel."""
        try:
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel == channel:
                    return f"Already connected to {channel.name}"
                await self.voice_client.move_to(channel)
                return f"Moved to {channel.name}"
            
            self.voice_client = await channel.connect()
            return f"Connected to {channel.name}"
        except Exception as e:
            return f"Failed to join voice channel: {e}"

    async def leave_voice(self) -> str:
        """Leave the current voice channel."""
        if not self.voice_client or not self.voice_client.is_connected():
            return "Not connected to any voice channel."
        
        await self.voice_client.disconnect()
        self.voice_client = None
        self.current_track = None
        self.queue.clear()
        self.is_paused = False
        return "Disconnected from voice channel."

    async def play_track(self, query: str, requester: str = "Unknown") -> str:
        """
        Search for a track and add it to the queue or play immediately.
        Note: Discord.py voice requires FFmpeg and can play audio files/streams.
        Spotify API provides preview URLs (30s samples) for some tracks.
        """
        if not self.voice_client or not self.voice_client.is_connected():
            return "Bot is not connected to a voice channel. Use !join first."
        
        # Search for the track
        tracks = await self.search_track(query, limit=1)
        if not tracks:
            return f"No tracks found for '{query}'"
        
        track = tracks[0]
        track["requester"] = requester
        
        # Add to queue
        self.queue.append(track)
        
        # If nothing is playing, start playback
        if not self.voice_client.is_playing() and not self.is_paused:
            await self._play_next()
            return f"Now playing: **{track['name']}** by {track['artist']}"
        else:
            return f"Added to queue: **{track['name']}** by {track['artist']} (Position: {len(self.queue)})"

    async def _play_next(self) -> None:
        """Internal method to play the next track in the queue."""
        if not self.voice_client or not self.voice_client.is_connected():
            return
        
        # Handle loop mode
        if self.loop_mode == LoopMode.TRACK and self.current_track:
            track = self.current_track
        elif self.loop_mode == LoopMode.QUEUE and self.current_track:
            self.queue.append(self.current_track)
            if not self.queue:
                self.current_track = None
                return
            track = self.queue.pop(0)
        else:
            if not self.queue:
                self.current_track = None
                return
            track = self.queue.pop(0)
        
        self.current_track = track
        
        # Note: Spotify API provides preview_url for 30-second samples
        # For full track playback, you would need to integrate with a different service
        # or use yt-dlp to search and download from YouTube
        
        # This is a placeholder - in production, you'd use yt-dlp or similar
        # to get the actual audio stream
        print(f"Would play: {track['name']} by {track['artist']}")
        print(f"Spotify URL: {track['url']}")
        
        # For now, we'll simulate playback timing
        # In a real implementation, you'd use discord.FFmpegPCMAudio or similar
        
        # Example of how you would play with FFmpeg (requires audio source):
        # audio_source = discord.FFmpegPCMAudio(audio_url)
        # self.voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(self._play_next(), self.bot.loop))

    async def pause(self) -> str:
        """Pause the current playback."""
        if not self.voice_client or not self.voice_client.is_connected():
            return "Not connected to a voice channel."
        
        if not self.voice_client.is_playing():
            return "Nothing is currently playing."
        
        if self.is_paused:
            return "Playback is already paused."
        
        self.voice_client.pause()
        self.is_paused = True
        return "⏸️ Playback paused."

    async def resume(self) -> str:
        """Resume paused playback."""
        if not self.voice_client or not self.voice_client.is_connected():
            return "Not connected to a voice channel."
        
        if not self.is_paused:
            return "Playback is not paused."
        
        self.voice_client.resume()
        self.is_paused = False
        return "▶️ Playback resumed."

    async def skip(self) -> str:
        """Skip the current track."""
        if not self.voice_client or not self.voice_client.is_connected():
            return "Not connected to a voice channel."
        
        if not self.voice_client.is_playing() and not self.is_paused:
            return "Nothing is currently playing."
        
        if self.current_track:
            skipped = f"Skipped: **{self.current_track['name']}** by {self.current_track['artist']}"
        else:
            skipped = "Skipped current track."
        
        self.voice_client.stop()
        self.is_paused = False
        await self._play_next()
        
        return skipped

    async def stop_playback(self) -> str:
        """Stop playback and clear the queue."""
        if not self.voice_client or not self.voice_client.is_connected():
            return "Not connected to a voice channel."
        
        self.voice_client.stop()
        self.queue.clear()
        self.current_track = None
        self.is_paused = False
        return "⏹️ Playback stopped and queue cleared."

    async def set_loop(self, mode: str) -> str:
        """
        Set loop mode.
        Modes: 'off', 'track', 'queue'
        """
        mode = mode.lower()
        if mode in ["off", "none", "disable"]:
            self.loop_mode = LoopMode.OFF
            return "🔁 Loop disabled."
        elif mode in ["track", "song", "one"]:
            self.loop_mode = LoopMode.TRACK
            return "🔂 Looping current track."
        elif mode in ["queue", "all"]:
            self.loop_mode = LoopMode.QUEUE
            return "🔁 Looping queue."
        else:
            return "Invalid loop mode. Use: off, track, or queue."

    async def set_volume(self, volume: int) -> str:
        """Set playback volume (0-100)."""
        if not self.voice_client or not self.voice_client.is_connected():
            return "Not connected to a voice channel."
        
        if not 0 <= volume <= 100:
            return "Volume must be between 0 and 100."
        
        self.volume = volume / 100.0
        
        # Update volume if audio is currently playing
        if self.voice_client.source and isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
            self.voice_client.source.volume = self.volume
        
        return f"🔊 Volume set to {volume}%"

    async def get_queue(self) -> str:
        """Get the current queue."""
        if not self.queue:
            if self.current_track:
                return f"Now playing: **{self.current_track['name']}** by {self.current_track['artist']}\n\nQueue is empty."
            return "Queue is empty."
        
        lines = []
        
        if self.current_track:
            status = "⏸️ Paused" if self.is_paused else "▶️ Now Playing"
            lines.append(f"{status}: **{self.current_track['name']}** by {self.current_track['artist']}")
            lines.append("")
        
        lines.append("**Queue:**")
        for idx, track in enumerate(self.queue[:10], start=1):
            duration_sec = track.get("duration_ms", 0) // 1000
            duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
            requester = track.get("requester", "Unknown")
            lines.append(f"{idx}. **{track['name']}** by {track['artist']} [{duration_str}] - Added by {requester}")
        
        if len(self.queue) > 10:
            lines.append(f"\n... and {len(self.queue) - 10} more tracks")
        
        # Add loop status
        loop_status = {
            LoopMode.OFF: "Loop: Off",
            LoopMode.TRACK: "Loop: 🔂 Track",
            LoopMode.QUEUE: "Loop: 🔁 Queue"
        }
        lines.append(f"\n{loop_status[self.loop_mode]}")
        
        return "\n".join(lines)

    async def clear_queue(self) -> str:
        """Clear the queue without stopping current playback."""
        if not self.queue:
            return "Queue is already empty."
        
        count = len(self.queue)
        self.queue.clear()
        return f"Cleared {count} track(s) from the queue."

    async def remove_from_queue(self, position: int) -> str:
        """Remove a track from the queue by position."""
        if not self.queue:
            return "Queue is empty."
        
        if position < 1 or position > len(self.queue):
            return f"Invalid position. Queue has {len(self.queue)} track(s)."
        
        removed = self.queue.pop(position - 1)
        return f"Removed from queue: **{removed['name']}** by {removed['artist']}"

    async def shuffle_queue(self) -> str:
        """Shuffle the queue."""
        if len(self.queue) < 2:
            return "Not enough tracks in queue to shuffle."
        
        import random
        random.shuffle(self.queue)
        return f"🔀 Shuffled {len(self.queue)} track(s) in the queue."

    def create_queue_embed(self) -> discord.Embed:
        """Create a rich embed for the queue display."""
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=discord.Color.blue(),
        )
        
        if self.current_track:
            status = "⏸️ Paused" if self.is_paused else "▶️ Now Playing"
            embed.add_field(
                name=status,
                value=f"**{self.current_track['name']}**\nby {self.current_track['artist']}",
                inline=False
            )
        
        if self.queue:
            queue_text = []
            for idx, track in enumerate(self.queue[:10], start=1):
                duration_sec = track.get("duration_ms", 0) // 1000
                duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                queue_text.append(f"`{idx}.` **{track['name']}** - {track['artist']} `[{duration_str}]`")
            
            if len(self.queue) > 10:
                queue_text.append(f"\n*... and {len(self.queue) - 10} more*")
            
            embed.add_field(
                name="Up Next",
                value="\n".join(queue_text),
                inline=False
            )
        else:
            embed.add_field(name="Up Next", value="*Queue is empty*", inline=False)
        
        # Footer with loop status and queue count
        loop_icons = {
            LoopMode.OFF: "➡️",
            LoopMode.TRACK: "🔂",
            LoopMode.QUEUE: "🔁"
        }
        footer_text = f"{loop_icons[self.loop_mode]} Loop: {self.loop_mode.name} | Volume: {int(self.volume * 100)}%"
        if self.queue:
            footer_text += f" | Tracks in queue: {len(self.queue)}"
        
        embed.set_footer(text=footer_text)
        
        return embed

    async def start(self):
        """Initialize the Spotify integration."""
        self._initialize_client()

    async def stop(self):
        """Clean up resources."""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
        self.voice_client = None
        self.current_track = None
        self.queue.clear()
