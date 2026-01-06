import discord
from discord.ext import commands

import integration
from api_manager import require_token
from discord_bot import analytics, command_handler, lifecycle, maintenance, storage_api, utils_misc
from discord_bot.config_store import get_guild_config, set_guild_config
from discord_bot.games import coin_flip, poll_creator, rps_game, roll_dice
from discord_bot.member_roles import (
    on_member_join as handle_member_join,
    on_member_remove as handle_member_remove,
)
from discord_bot.moderation import (
    ban_user as mod_ban_user,
    kick_user as mod_kick_user,
    lock_channel as mod_lock_channel,
    mute_user as mod_mute_user,
    purge_messages,
    unban_user as mod_unban_user,
    unlock_channel as mod_unlock_channel,
    warn_user as mod_warn_user,
)
from discord_bot.notifications import notify_user, react_to_message, send_announcement
from discord_bot.scheduler import temporary_message
from discord_bot.security import is_admin, is_moderator
from integrations.spotify_integration import SpotifyIntegration
from integrations.twitch_integration import TwitchIntegration

# Optional import for check_imports
try:
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from scripts.check_imports import main as check_imports_main
except ImportError:
    check_imports_main = None

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable for prefix commands
intents.members = True  # Enable for member events

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize integrations
twitch = TwitchIntegration(bot)
spotify = SpotifyIntegration(bot)


def _get_channel_from_config(
    guild: discord.Guild | None, key: str
) -> discord.TextChannel | None:
    if not guild:
        return None
    cfg = get_guild_config(guild.id)
    channel_id = cfg.get(key)
    if isinstance(channel_id, discord.TextChannel):
        return channel_id
    if not channel_id:
        return None
    try:
        channel_id = int(channel_id)
    except (TypeError, ValueError):
        return None
    channel = guild.get_channel(channel_id)
    return channel if isinstance(channel, discord.TextChannel) else None


def _mod_check(ctx: commands.Context) -> bool:
    return isinstance(ctx.author, discord.Member) and (is_admin(ctx.author) or is_moderator(ctx.author))


@bot.event
async def on_ready():
    if check_imports_main:
        check_imports_main()
    await lifecycle.on_ready(bot, twitch)
    await spotify.start()


@bot.event
async def on_disconnect():
    await lifecycle.on_disconnect(bot)


@bot.event
async def on_command_completion(ctx: commands.Context):
    if ctx.command and ctx.author and not ctx.author.bot:
        analytics.log_command_usage(ctx.author.id, ctx.command.name)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    analytics.log_error(error)
    if isinstance(error, (commands.CommandNotFound, commands.CheckFailure, commands.CommandOnCooldown)):
        return
    await ctx.send(f"Error: {error}")


@bot.before_invoke
async def _rate_limit(ctx: commands.Context):
    if ctx.author.bot or not ctx.command:
        return
    if not command_handler.cooldown_check(ctx.author.id, ctx.command.name):
        await ctx.send("Slow down, that command is on cooldown.")
        raise commands.CheckFailure("On cooldown")


@bot.event
async def on_member_join(member: discord.Member):
    channel = _get_channel_from_config(member.guild, "welcome_channel_id")
    await handle_member_join(member, channel)


@bot.event
async def on_member_remove(member: discord.Member):
    channel = _get_channel_from_config(member.guild, "leave_channel_id")
    await handle_member_remove(member, channel)


@bot.command(name="status")
async def status(ctx: commands.Context):
    """Return the current status from the integration layer."""
    message = await integration.get_status()
    await ctx.send(message)


@bot.command(name="search")
async def search(ctx: commands.Context, *, query: str):
    """Run a quick web search."""
    results = await integration.search_web(query)
    if not results:
        await ctx.send("No results found.")
        return

    lines = []
    for idx, item in enumerate(results, start=1):
        title = item.get("title") or "Result"
        url = item.get("url") or ""
        snippet = (item.get("snippet") or "").strip()
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        line = f"{idx}. {title}"
        if url:
            line += f" - {url}"
        if snippet:
            line += f"\n   {snippet}"
        lines.append(line)
        if idx >= 5:
            break

    message = "\n".join(lines)
    await ctx.send(message[:1990] or "No results found.")


@bot.command(name="imagine", aliases=["art", "image"])
async def imagine(ctx: commands.Context, *, prompt: str):
    """Generate AI art using a ChatGPT-style prompt enhancer + image model."""
    result = await integration.generate_art(prompt)
    if result.get("error"):
        await ctx.send(result["error"])
        return

    url = result.get("url") or ""
    prompt_used = result.get("prompt") or prompt
    text = f"Prompt: {prompt_used}"
    if url:
        text += f"\n{url}"
    await ctx.send(text[:1990])


# =============================================================================
# Twitch Commands
# =============================================================================

@bot.command(name="uptime")
async def uptime(ctx: commands.Context):
    """Report Twitch stream uptime."""
    await twitch.check_stream_live()
    await ctx.send(twitch.stream_uptime())


@bot.command(name="live")
async def live(ctx: commands.Context):
    """Check if Twitch stream is live and post embed."""
    await twitch.check_stream_live()
    if not twitch.state.is_live:
        await ctx.send("Stream is offline.")
        return
    embed = twitch.create_stream_embed(live=True)
    await ctx.send(embed=embed)


@bot.command(name="twitchstats", aliases=["tstats"])
async def twitchstats(ctx: commands.Context):
    """Show Twitch stream stats summary."""
    summary = await twitch.stream_stats_summary()
    await ctx.send(summary[:1990])


@bot.command(name="tchat")
async def tchat(ctx: commands.Context, *, message: str):
    """Relay a Discord message to Twitch chat."""
    await twitch.relay_discord_chat_to_twitch(ctx.author.display_name, message)
    await ctx.send("Sent to Twitch chat.")


@bot.command(name="followers")
async def followers(ctx: commands.Context):
    """Show follower count."""
    count = await twitch.get_follow_count()
    await ctx.send(f"Followers: {count or 'N/A'}")


@bot.command(name="subs")
async def subs(ctx: commands.Context):
    """Show subscriber count."""
    count = await twitch.get_subscriber_count()
    await ctx.send(f"Subscribers: {count or 'N/A'}")


@bot.command(name="streamgame")
async def streamgame(ctx: commands.Context):
    """Report the current game/category."""
    await twitch.check_stream_live()
    await ctx.send(f"Game/category: {twitch.stream_game_category()}")


@bot.command(name="health")
async def health(ctx: commands.Context):
    """Check Twitch/Discord/Spotify integration health."""
    status = await lifecycle.health_check(bot, twitch)
    spotify_status = await spotify.health_check()
    combined = f"{status}\n{spotify_status}"
    await ctx.send(combined[:1990])


# =============================================================================
# Spotify Commands
# =============================================================================

@bot.command(name="spotify", aliases=["sp", "nowlistening"])
async def spotify_now(ctx: commands.Context):
    """Show what's currently playing on Spotify."""
    track = await spotify.get_current_track()
    if not track:
        await ctx.send("Nothing is playing on Spotify right now, or Spotify integration is not configured.")
        return
    embed = spotify.create_now_playing_embed(track)
    await ctx.send(embed=embed)


@bot.command(name="spotifysearch", aliases=["spsearch", "searchtrack"])
async def spotify_search(ctx: commands.Context, *, query: str):
    """Search for tracks on Spotify."""
    tracks = await spotify.search_track(query, limit=5)
    if not tracks:
        await ctx.send("No tracks found or Spotify integration is not configured.")
        return
    
    lines = ["**Spotify Search Results:**"]
    for idx, track in enumerate(tracks, start=1):
        duration_sec = track["duration_ms"] // 1000
        duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        lines.append(f"{idx}. **{track['name']}** by {track['artist']} [{duration_str}]\n   {track['url']}")
    
    message = "\n".join(lines)
    await ctx.send(message[:1990])


@bot.command(name="toptracks", aliases=["mytoptracks"])
async def top_tracks(ctx: commands.Context, timeframe: str = "medium"):
    """
    Show your top tracks on Spotify.
    Timeframe: short (4 weeks), medium (6 months), long (all time)
    """
    time_range_map = {
        "short": "short_term",
        "medium": "medium_term",
        "long": "long_term",
    }
    time_range = time_range_map.get(timeframe.lower(), "medium_term")
    
    tracks = await spotify.get_top_tracks(time_range=time_range, limit=10)
    if not tracks:
        await ctx.send("Could not fetch top tracks. Make sure Spotify integration is configured.")
        return
    
    timeframe_display = {"short_term": "4 weeks", "medium_term": "6 months", "long_term": "all time"}
    lines = [f"**Your Top Tracks ({timeframe_display.get(time_range, 'recent')}):**"]
    for idx, track in enumerate(tracks, start=1):
        lines.append(f"{idx}. **{track['name']}** by {track['artist']}\n   {track['url']}")
    
    message = "\n".join(lines)
    await ctx.send(message[:1990])


@bot.command(name="topartists", aliases=["mytopartists"])
async def top_artists(ctx: commands.Context, timeframe: str = "medium"):
    """
    Show your top artists on Spotify.
    Timeframe: short (4 weeks), medium (6 months), long (all time)
    """
    time_range_map = {
        "short": "short_term",
        "medium": "medium_term",
        "long": "long_term",
    }
    time_range = time_range_map.get(timeframe.lower(), "medium_term")
    
    artists = await spotify.get_top_artists(time_range=time_range, limit=10)
    if not artists:
        await ctx.send("Could not fetch top artists. Make sure Spotify integration is configured.")
        return
    
    timeframe_display = {"short_term": "4 weeks", "medium_term": "6 months", "long_term": "all time"}
    lines = [f"**Your Top Artists ({timeframe_display.get(time_range, 'recent')}):**"]
    for idx, artist in enumerate(artists, start=1):
        followers_str = f"{artist['followers']:,}" if artist['followers'] > 0 else "N/A"
        lines.append(f"{idx}. **{artist['name']}** ({artist['genres']})\n   Followers: {followers_str} | {artist['url']}")
    
    message = "\n".join(lines)
    await ctx.send(message[:1990])


@bot.command(name="playlists", aliases=["myplaylists", "spotifyplaylists"])
async def playlists(ctx: commands.Context):
    """Show your Spotify playlists."""
    playlists = await spotify.get_playlists(limit=10)
    if not playlists:
        await ctx.send("Could not fetch playlists. Make sure Spotify integration is configured.")
        return
    
    lines = ["**Your Spotify Playlists:**"]
    for idx, playlist in enumerate(playlists, start=1):
        lines.append(f"{idx}. **{playlist['name']}** by {playlist['owner']}\n   {playlist['tracks']} tracks | {playlist['url']}")
    
    message = "\n".join(lines)
    await ctx.send(message[:1990])


# =============================================================================
# Music Playback Commands (Voice Channel)
# =============================================================================

@bot.command(name="join", aliases=["connect"])
async def join_voice(ctx: commands.Context):
    """Join your current voice channel."""
    if not isinstance(ctx.author, discord.Member) or not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("You need to be in a voice channel to use this command.")
        return
    
    channel = ctx.author.voice.channel
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("You need to be in a voice channel (not a stage channel).")
        return
    
    message = await spotify.join_voice(channel)
    await ctx.send(message)


@bot.command(name="leave", aliases=["disconnect", "dc"])
async def leave_voice(ctx: commands.Context):
    """Leave the current voice channel."""
    message = await spotify.leave_voice()
    await ctx.send(message)


@bot.command(name="play", aliases=["p"])
async def play_music(ctx: commands.Context, *, query: str):
    """
    Play a song from Spotify search.
    Example: !play never gonna give you up
    """
    # Auto-join if not connected
    if not spotify.voice_client or not spotify.voice_client.is_connected():
        if isinstance(ctx.author, discord.Member) and ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            if isinstance(channel, discord.VoiceChannel):
                await spotify.join_voice(channel)
            else:
                await ctx.send("You need to be in a voice channel (not a stage channel).")
                return
        else:
            await ctx.send("You need to be in a voice channel or the bot needs to be connected to one.")
            return
    
    message = await spotify.play_track(query, requester=ctx.author.display_name)
    await ctx.send(message)


@bot.command(name="pause")
async def pause_music(ctx: commands.Context):
    """Pause the current playback."""
    message = await spotify.pause()
    await ctx.send(message)


@bot.command(name="resume", aliases=["unpause"])
async def resume_music(ctx: commands.Context):
    """Resume paused playback."""
    message = await spotify.resume()
    await ctx.send(message)


@bot.command(name="skip", aliases=["next", "s"])
async def skip_music(ctx: commands.Context):
    """Skip the current track."""
    message = await spotify.skip()
    await ctx.send(message)


@bot.command(name="stop")
async def stop_music(ctx: commands.Context):
    """Stop playback and clear the queue."""
    message = await spotify.stop_playback()
    await ctx.send(message)


@bot.command(name="loop", aliases=["repeat"])
async def loop_music(ctx: commands.Context, mode: str = "off"):
    """
    Set loop mode.
    Modes: off, track, queue
    Example: !loop track
    """
    message = await spotify.set_loop(mode)
    await ctx.send(message)


@bot.command(name="volume", aliases=["vol", "v"])
async def set_volume(ctx: commands.Context, volume: int):
    """
    Set playback volume (0-100).
    Example: !volume 50
    """
    message = await spotify.set_volume(volume)
    await ctx.send(message)


@bot.command(name="queue", aliases=["q"])
async def show_queue(ctx: commands.Context):
    """Show the current music queue."""
    embed = spotify.create_queue_embed()
    await ctx.send(embed=embed)


@bot.command(name="nowplaying", aliases=["np", "current"])
async def now_playing(ctx: commands.Context):
    """Show the currently playing track in voice."""
    if not spotify.current_track:
        await ctx.send("Nothing is currently playing.")
        return
    
    track = spotify.current_track
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**{track['name']}**",
        color=discord.Color.green(),
        url=track['url'],
    )
    
    embed.add_field(name="Artist", value=track['artist'], inline=True)
    embed.add_field(name="Album", value=track.get('album', 'Unknown'), inline=True)
    
    if track.get('duration_ms'):
        duration_sec = track['duration_ms'] // 1000
        duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        embed.add_field(name="Duration", value=duration_str, inline=True)
    
    if track.get('requester'):
        embed.add_field(name="Requested by", value=track['requester'], inline=True)
    
    embed.set_footer(text="Spotify Music Player")
    
    await ctx.send(embed=embed)


@bot.command(name="clearqueue", aliases=["cq", "clear"])
async def clear_queue(ctx: commands.Context):
    """Clear the music queue."""
    message = await spotify.clear_queue()
    await ctx.send(message)


@bot.command(name="remove", aliases=["rm"])
async def remove_from_queue(ctx: commands.Context, position: int):
    """
    Remove a track from the queue by position.
    Example: !remove 3
    """
    message = await spotify.remove_from_queue(position)
    await ctx.send(message)


@bot.command(name="shuffle")
async def shuffle_queue(ctx: commands.Context):
    """Shuffle the music queue."""
    message = await spotify.shuffle_queue()
    await ctx.send(message)


# =============================================================================
# Bot Management Commands
# =============================================================================

@bot.command(name="reloadext")
@commands.has_permissions(manage_guild=True)
async def reloadext(ctx: commands.Context, *extensions: str):
    """Reload configured extensions (manage_guild only)."""
    targets = extensions or tuple(lifecycle.DEFAULT_EXTENSIONS)
    reloaded, failed = await lifecycle.reload_extensions(bot, targets)
    parts = []
    if reloaded:
        parts.append(f"Reloaded: {', '.join(reloaded)}")
    if failed:
        errs = "; ".join(f"{name} ({err})" for name, err in failed)
        parts.append(f"Failed: {errs}")
    await ctx.send("; ".join(parts) if parts else "No extensions reloaded.")


@bot.command(name="shutdown")
@commands.has_permissions(manage_guild=True)
async def shutdown(ctx: commands.Context):
    """Gracefully shut down the bot (manage_guild only)."""
    await ctx.send("Shutting down...")
    await spotify.stop()
    await lifecycle.graceful_shutdown(bot, twitch)


# =============================================================================
# Moderation Commands
# =============================================================================

@bot.command(name="warn")
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Warn a user (mods/admins)."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    msg = await mod_warn_user(member, reason)
    await ctx.send(msg)


@bot.command(name="mute")
async def mute(ctx: commands.Context, member: discord.Member, duration: str):
    """Mute (timeout) a user for a duration like 10m or 1h."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    seconds = utils_misc.parse_duration(duration)
    msg = await mod_mute_user(member, seconds, reason=f"Muted by {ctx.author}")
    await ctx.send(msg)


@bot.command(name="kick")
async def kick(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    msg = await mod_kick_user(member, reason=reason)
    await ctx.send(msg)


@bot.command(name="ban")
async def ban(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    msg = await mod_ban_user(member, reason=reason)
    await ctx.send(msg)


@bot.command(name="unban")
async def unban(ctx: commands.Context, user_id: int):
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    msg = await mod_unban_user(ctx.guild, user_id, reason=f"Unbanned by {ctx.author}")
    await ctx.send(msg)


@bot.command(name="purge")
async def purge(ctx: commands.Context, amount: int = 10):
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("This command can only be used in a text channel.")
        return
    msg = await purge_messages(ctx.channel, amount, reason=f"Purge by {ctx.author}")
    await ctx.send(msg)


@bot.command(name="lock")
async def lock(ctx: commands.Context):
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("This command can only be used in a text channel.")
        return
    msg = await mod_lock_channel(ctx.channel, reason=f"Locked by {ctx.author}")
    await ctx.send(msg)


@bot.command(name="unlock")
async def unlock(ctx: commands.Context):
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("This command can only be used in a text channel.")
        return
    msg = await mod_unlock_channel(ctx.channel, reason=f"Unlocked by {ctx.author}")
    await ctx.send(msg)


# =============================================================================
# Fun & Games Commands
# =============================================================================

@bot.command(name="roll")
async def roll(ctx: commands.Context, expression: str):
    """Roll dice, e.g., 2d6+1."""
    try:
        total = roll_dice(expression)
    except Exception as exc:
        await ctx.send(f"Invalid dice expression: {exc}")
        return
    await ctx.send(f"Result: {total}")


@bot.command(name="coin")
async def coin(ctx: commands.Context):
    await ctx.send(f"Flipped: {coin_flip()}")


@bot.command(name="rps")
async def rps(ctx: commands.Context, choice: str):
    try:
        result = rps_game(choice)
    except Exception as exc:
        await ctx.send(str(exc))
        return
    await ctx.send(result)


@bot.command(name="poll")
async def poll(ctx: commands.Context, *, payload: str):
    """
    Create a quick poll. Format: question | option1 | option2 | ...
    """
    parts = [part.strip() for part in payload.split("|") if part.strip()]
    if len(parts) < 3:
        await ctx.send("Provide a question and at least two options, separated by '|'.")
        return
    question, options = parts[0], parts[1:]
    try:
        content = poll_creator(question, options)
    except Exception as exc:
        await ctx.send(str(exc))
        return
    await ctx.send(content)


# =============================================================================
# Notification Commands
# =============================================================================

@bot.command(name="announce")
async def announce(ctx: commands.Context, *, content: str):
    await send_announcement(ctx.channel, content)


@bot.command(name="dm")
async def dm(ctx: commands.Context, user_id: int, *, content: str):
    """Send a DM by user id."""
    sent = await notify_user(bot, user_id, content)
    await ctx.send("DM sent." if sent else "Could not send DM.")


@bot.command(name="react")
async def react(ctx: commands.Context, message_id: int, emoji: str):
    try:
        message = await ctx.channel.fetch_message(message_id)
    except Exception:
        await ctx.send("Could not find that message.")
        return
    await react_to_message(message, emoji)
    await ctx.send("Reaction added.")


@bot.command(name="tempmsg")
async def tempmsg(ctx: commands.Context, duration: str, *, content: str):
    """Send a message that deletes itself after the duration."""
    seconds = utils_misc.parse_duration(duration)
    await temporary_message(ctx.channel, content, seconds)


# =============================================================================
# Server Configuration & Maintenance Commands
# =============================================================================

@bot.command(name="backup")
@commands.has_permissions(administrator=True)
async def backup(ctx: commands.Context):
    dest = maintenance.backup_data()
    await ctx.send(f"Backup created at {dest}")


@bot.command(name="restore")
@commands.has_permissions(administrator=True)
async def restore(ctx: commands.Context, backup_name: str):
    dest_path = maintenance.BACKUP_DIR / backup_name
    if not dest_path.exists():
        await ctx.send("Backup not found.")
        return
    maintenance.restore_backup(dest_path)
    await ctx.send(f"Restored backup from {dest_path}")


@bot.command(name="setwelcome")
@commands.has_permissions(manage_guild=True)
async def setwelcome(ctx: commands.Context, channel: discord.TextChannel):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    set_guild_config(ctx.guild.id, "welcome_channel_id", channel.id)
    await ctx.send(f"Welcome channel set to {channel.mention}")


@bot.command(name="setleave")
@commands.has_permissions(manage_guild=True)
async def setleave(ctx: commands.Context, channel: discord.TextChannel):
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    set_guild_config(ctx.guild.id, "leave_channel_id", channel.id)
    await ctx.send(f"Leave channel set to {channel.mention}")


# =============================================================================
# API & Storage Commands
# =============================================================================

@bot.command(name="fetchjson")
async def fetchjson(ctx: commands.Context, url: str):
    """Fetch JSON from a URL (GET) and show a truncated response."""
    try:
        data = storage_api.fetch_api_json(url)
    except Exception as exc:
        await ctx.send(f"Fetch failed: {exc}")
        return
    text = str(data)
    await ctx.send(text[:1900])


def main():
    bot.run(require_token())


if __name__ == "__main__":
    main()
