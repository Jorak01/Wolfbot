import datetime as dt
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
# Import new admin and moderation features
from discord_bot import admin_tools, automod, logging_system, warning_system
# Import new community features
from discord_bot import leveling_system, community_features, welcome_system
# Import gaming utilities
from discord_bot import gaming_utilities
# Import AI integration
from integrations import ai_integration
# Import external APIs
from integrations import external_apis
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

# Initialize integrations with error handling
twitch = None
spotify = None

try:
    twitch = TwitchIntegration(bot)
    print("✓ Twitch integration initialized")
except Exception as e:
    print(f"⚠ Warning: Twitch integration failed to initialize: {e}")
    print("  Twitch commands will be disabled. Check your Twitch API credentials in .env")

try:
    spotify = SpotifyIntegration(bot)
    print("✓ Spotify integration initialized")
except Exception as e:
    print(f"⚠ Warning: Spotify integration failed to initialize: {e}")
    print("  Spotify commands will be disabled. Check your Spotify API credentials in .env")

# Initialize auto-moderation configuration
automod_config = automod.AutoModConfig()
# Configure default settings (can be customized per server)
automod_config.BLOCK_INVITES = True
automod_config.MAX_MESSAGES_PER_WINDOW = 5
automod_config.SPAM_WINDOW_SECONDS = 5


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


def _check_integration(integration, name: str) -> bool:
    """Check if an integration is available."""
    return integration is not None


@bot.event
async def on_ready():
    if check_imports_main:
        check_imports_main()
    if twitch:
        try:
            await lifecycle.on_ready(bot, twitch)
        except Exception as e:
            print(f"⚠ Warning: Twitch on_ready failed: {e}")
    if spotify:
        try:
            await spotify.start()
        except Exception as e:
            print(f"⚠ Warning: Spotify start failed: {e}")
    
    # Load and sync slash commands
    try:
        from discord_bot.slash_commands import create_slash_commands
        create_slash_commands(bot, {'twitch': twitch, 'spotify': spotify})
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"⚠ Warning: Slash command sync failed: {e}")
    
    print("✅ Bot is ready!")


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
    # Update server stats
    await community_features.update_server_stats(member.guild.id, members_joined=1)
    
    # Send enhanced welcome message
    channel = _get_channel_from_config(member.guild, "welcome_channel_id")
    if channel:
        await welcome_system.send_welcome_message(channel, member)
    
    # Check for suspicious alt accounts
    is_suspicious, reason = await automod.detect_alt_account(member)
    if is_suspicious:
        log_channel_id = logging_system.get_log_channel(member.guild.id)
        if log_channel_id:
            log_channel = member.guild.get_channel(log_channel_id)
            if isinstance(log_channel, discord.TextChannel):
                embed = discord.Embed(
                    title="⚠️ Suspicious Account Detected",
                    description=f"{member.mention} ({member.id})",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=True)
                await log_channel.send(embed=embed)
    
    # Check for raids
    is_raid, raid_reason = await automod.check_raid(member, automod_config)
    if is_raid and not automod.is_raid_mode(member.guild.id):
        result = await automod.activate_raid_mode(member.guild, automod_config)
        log_channel_id = logging_system.get_log_channel(member.guild.id)
        if log_channel_id:
            log_channel = member.guild.get_channel(log_channel_id)
            if isinstance(log_channel, discord.TextChannel):
                await log_channel.send(f"🚨 {result}")


@bot.event
async def on_member_remove(member: discord.Member):
    # Update server stats
    await community_features.update_server_stats(member.guild.id, members_left=1)
    
    # Send farewell message
    channel = _get_channel_from_config(member.guild, "leave_channel_id")
    if channel:
        await welcome_system.send_farewell_message(channel, member)


@bot.event
async def on_message(message: discord.Message):
    """Handle messages with auto-moderation, XP gain, and stats."""
    if message.author.bot:
        await bot.process_commands(message)
        return
    
    # Update server stats
    if message.guild:
        await community_features.update_server_stats(message.guild.id, messages_sent=1)
    
    # Process XP gain
    result = await leveling_system.process_message_for_xp(message)
    if result:
        new_level, leveled_up = result
        if leveled_up and isinstance(message.author, discord.Member):
            # Announce level up
            embed = await leveling_system.create_level_up_embed(message.author, new_level)
            await message.channel.send(embed=embed, delete_after=10)
    
    # Process auto-moderation
    action = await automod.process_message(message, automod_config)
    if action:
        # Log the auto-mod action
        log_channel_id = logging_system.get_log_channel(message.guild.id) if message.guild else None
        if log_channel_id and message.guild:
            log_channel = message.guild.get_channel(log_channel_id)
            if isinstance(log_channel, discord.TextChannel):
                embed = discord.Embed(
                    title="🛡️ Auto-Moderation Action",
                    description=action,
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)
    
    await bot.process_commands(message)


@bot.event
async def on_message_delete(message: discord.Message):
    """Log deleted messages."""
    if message.author.bot:
        return
    await logging_system.log_message_delete(message)
    if message.guild:
        embed = await logging_system.create_delete_log_embed(message)
        await logging_system.send_to_log_channel(message.guild, embed)


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """Log edited messages."""
    if before.author.bot:
        return
    await logging_system.log_message_edit(before, after)
    if before.guild:
        embed = await logging_system.create_edit_log_embed(before, after)
        await logging_system.send_to_log_channel(before.guild, embed)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """Handle reaction role assignments."""
    await admin_tools.handle_reaction_role_add(payload, bot)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """Handle reaction role removals."""
    await admin_tools.handle_reaction_role_remove(payload, bot)


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
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    await twitch.check_stream_live()
    await ctx.send(twitch.stream_uptime())


@bot.command(name="live")
async def live(ctx: commands.Context):
    """Check if Twitch stream is live and post embed."""
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    await twitch.check_stream_live()
    if not twitch.state.is_live:
        await ctx.send("Stream is offline.")
        return
    embed = twitch.create_stream_embed(live=True)
    await ctx.send(embed=embed)


@bot.command(name="twitchstats", aliases=["tstats"])
async def twitchstats(ctx: commands.Context):
    """Show Twitch stream stats summary."""
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    summary = await twitch.stream_stats_summary()
    await ctx.send(summary[:1990])


@bot.command(name="tchat")
async def tchat(ctx: commands.Context, *, message: str):
    """Relay a Discord message to Twitch chat."""
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    await twitch.relay_discord_chat_to_twitch(ctx.author.display_name, message)
    await ctx.send("Sent to Twitch chat.")


@bot.command(name="followers")
async def followers(ctx: commands.Context):
    """Show follower count."""
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    count = await twitch.get_follow_count()
    await ctx.send(f"Followers: {count or 'N/A'}")


@bot.command(name="subs")
async def subs(ctx: commands.Context):
    """Show subscriber count."""
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    count = await twitch.get_subscriber_count()
    await ctx.send(f"Subscribers: {count or 'N/A'}")


@bot.command(name="streamgame")
async def streamgame(ctx: commands.Context):
    """Report the current game/category."""
    if not twitch:
        await ctx.send("❌ Twitch integration is not configured.")
        return
    await twitch.check_stream_live()
    await ctx.send(f"Game/category: {twitch.stream_game_category()}")


@bot.command(name="health")
async def health(ctx: commands.Context):
    """Check Twitch/Discord/Spotify integration health."""
    parts = []
    if twitch:
        status = await lifecycle.health_check(bot, twitch)
        parts.append(status)
    else:
        parts.append("Twitch: Not configured")
    
    if spotify:
        spotify_status = await spotify.health_check()
        parts.append(spotify_status)
    else:
        parts.append("Spotify: Not configured")
    
    combined = "\n".join(parts)
    await ctx.send(combined[:1990])


# =============================================================================
# Spotify Commands
# =============================================================================

@bot.command(name="spotify", aliases=["sp", "nowlistening"])
async def spotify_now(ctx: commands.Context):
    """Show what's currently playing on Spotify."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    track = await spotify.get_current_track()
    if not track:
        await ctx.send("Nothing is playing on Spotify right now, or Spotify integration is not configured.")
        return
    embed = spotify.create_now_playing_embed(track)
    await ctx.send(embed=embed)


@bot.command(name="spotifysearch", aliases=["spsearch", "searchtrack"])
async def spotify_search(ctx: commands.Context, *, query: str):
    """Search for tracks on Spotify."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
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
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
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
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
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
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
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
    
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.join_voice(channel)
    await ctx.send(message)


@bot.command(name="leave", aliases=["disconnect", "dc"])
async def leave_voice(ctx: commands.Context):
    """Leave the current voice channel."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.leave_voice()
    await ctx.send(message)


@bot.command(name="play", aliases=["p"])
async def play_music(ctx: commands.Context, *, query: str):
    """
    Play a song from Spotify search.
    Example: !play never gonna give you up
    """
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
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
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.pause()
    await ctx.send(message)


@bot.command(name="resume", aliases=["unpause"])
async def resume_music(ctx: commands.Context):
    """Resume paused playback."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.resume()
    await ctx.send(message)


@bot.command(name="skip", aliases=["next", "s"])
async def skip_music(ctx: commands.Context):
    """Skip the current track."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.skip()
    await ctx.send(message)


@bot.command(name="stop")
async def stop_music(ctx: commands.Context):
    """Stop playback and clear the queue."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.stop_playback()
    await ctx.send(message)


@bot.command(name="loop", aliases=["repeat"])
async def loop_music(ctx: commands.Context, mode: str = "off"):
    """
    Set loop mode.
    Modes: off, track, queue
    Example: !loop track
    """
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.set_loop(mode)
    await ctx.send(message)


@bot.command(name="volume", aliases=["vol", "v"])
async def set_volume(ctx: commands.Context, volume: int):
    """
    Set playback volume (0-100).
    Example: !volume 50
    """
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.set_volume(volume)
    await ctx.send(message)


@bot.command(name="queue", aliases=["q"])
async def show_queue(ctx: commands.Context):
    """Show the current music queue."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    embed = spotify.create_queue_embed()
    await ctx.send(embed=embed)


@bot.command(name="nowplaying", aliases=["np", "current"])
async def now_playing(ctx: commands.Context):
    """Show the currently playing track in voice."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
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
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.clear_queue()
    await ctx.send(message)


@bot.command(name="remove", aliases=["rm"])
async def remove_from_queue(ctx: commands.Context, position: int):
    """
    Remove a track from the queue by position.
    Example: !remove 3
    """
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
    message = await spotify.remove_from_queue(position)
    await ctx.send(message)


@bot.command(name="shuffle")
async def shuffle_queue(ctx: commands.Context):
    """Shuffle the music queue."""
    if not spotify:
        await ctx.send("❌ Spotify integration is not configured.")
        return
    
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
    if spotify:
        await spotify.stop()
    if twitch:
        await lifecycle.graceful_shutdown(bot, twitch)
    else:
        await lifecycle.graceful_shutdown(bot, None)


# =============================================================================
# Moderation Commands
# =============================================================================

@bot.command(name="warn")
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
    """Warn a user with escalation (mods/admins)."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    count, action, escalation_msg = await warning_system.warn_user_with_escalation(
        member, ctx.author, reason
    )
    await ctx.send(f"⚠️ {member.mention} has been warned. Total warnings: {count}")
    if escalation_msg:
        await ctx.send(escalation_msg)


@bot.command(name="warnings")
async def warnings_cmd(ctx: commands.Context, member: discord.Member):
    """View warnings for a user (mods/admins)."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    warns = await warning_system.get_user_warnings(ctx.guild.id, member.id)
    embed = await warning_system.format_warnings_embed(member, warns)
    await ctx.send(embed=embed)


@bot.command(name="clearwarnings")
async def clearwarnings(ctx: commands.Context, member: discord.Member):
    """Clear all warnings for a user (mods/admins)."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    cleared = await warning_system.clear_user_warnings(ctx.guild.id, member.id)
    await ctx.send(f"✅ Cleared {cleared} warning(s) for {member.mention}")


@bot.command(name="removewarn")
async def removewarn(ctx: commands.Context, warning_id: int):
    """Remove a specific warning by ID (mods/admins)."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    
    success = await warning_system.remove_warning(warning_id)
    if success:
        await ctx.send(f"✅ Removed warning #{warning_id}")
    else:
        await ctx.send(f"❌ Could not find warning #{warning_id}")


@bot.command(name="warnleaderboard", aliases=["warnlb"])
async def warnleaderboard(ctx: commands.Context):
    """Show warning leaderboard (mods/admins)."""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    leaderboard = await warning_system.get_leaderboard(ctx.guild.id, limit=10)
    embed = await warning_system.format_leaderboard_embed(ctx.guild, leaderboard)
    await ctx.send(embed=embed)


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


@bot.command(name="raidmode")
async def raidmode(ctx: commands.Context, action: str = "status"):
    """Activate or deactivate raid mode (admins). Usage: !raidmode [on|off|status]"""
    if not isinstance(ctx.author, discord.Member) or not is_admin(ctx.author):
        await ctx.send("You need administrator permissions.")
        return
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    action = action.lower()
    if action == "on":
        result = await automod.activate_raid_mode(ctx.guild, automod_config)
        await ctx.send(result)
    elif action == "off":
        result = await automod.deactivate_raid_mode(ctx.guild, automod_config)
        await ctx.send(result)
    else:
        is_active = automod.is_raid_mode(ctx.guild.id)
        status = "🚨 **ACTIVE**" if is_active else "✅ Inactive"
        await ctx.send(f"Raid mode status: {status}")


@bot.command(name="setlogchannel")
@commands.has_permissions(administrator=True)
async def setlogchannel(ctx: commands.Context, channel: discord.TextChannel):
    """Set the channel for logging events (admins)."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    logging_system.set_log_channel(ctx.guild.id, channel.id)
    await ctx.send(f"✅ Log channel set to {channel.mention}")


@bot.command(name="viewlogs")
async def viewlogs(ctx: commands.Context, log_type: str = "deleted", limit: int = 10):
    """View message logs (mods/admins). Types: deleted, edited, all"""
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    log_type = log_type.lower()
    if log_type == "deleted":
        logs = await logging_system.get_deleted_messages(ctx.guild.id, limit=limit)
        embed = await logging_system.format_message_log_embed(logs, "Deleted Messages")
    elif log_type == "edited":
        logs = await logging_system.get_edited_messages(ctx.guild.id, limit=limit)
        embed = await logging_system.format_message_log_embed(logs, "Edited Messages")
    else:
        await ctx.send("Invalid log type. Use: deleted, edited")
        return
    
    await ctx.send(embed=embed)


# =============================================================================
# Community & Engagement Commands
# =============================================================================

@bot.command(name="rank", aliases=["level", "xp"])
async def rank(ctx: commands.Context, member: discord.Member | None = None):
    """Check your or another user's rank and XP."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    target = member if member else ctx.author
    if not isinstance(target, discord.Member):
        await ctx.send("User not found.")
        return
    
    stats = await leveling_system.get_user_stats(ctx.guild.id, target.id)
    if not stats:
        await ctx.send(f"{target.mention} hasn't earned any XP yet!")
        return
    
    rank = await leveling_system.get_user_rank(ctx.guild.id, target.id)
    embed = await leveling_system.create_rank_card_embed(target, stats, rank)
    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard(ctx: commands.Context):
    """Show the XP leaderboard."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    lb = await leveling_system.get_leaderboard(ctx.guild.id, limit=10)
    embed = await leveling_system.create_leaderboard_embed(ctx.guild, lb)
    await ctx.send(embed=embed)


@bot.command(name="setlevelrole")
@commands.has_permissions(manage_roles=True)
async def setlevelrole(ctx: commands.Context, level: int, role: discord.Role):
    """Set a role reward for reaching a level (admins)."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    await leveling_system.set_level_role(ctx.guild.id, level, role.id)
    await ctx.send(f"✅ Set {role.mention} as reward for reaching Level {level}")


@bot.command(name="karma", aliases=["rep", "reputation"])
async def karma(ctx: commands.Context, member: discord.Member | None = None):
    """Check your or another user's karma."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    target = member if member else ctx.author
    if not isinstance(target, discord.Member):
        await ctx.send("User not found.")
        return
    
    karma = await community_features.get_karma(ctx.guild.id, target.id)
    await ctx.send(f"{target.mention} has **{karma}** karma points! ⭐")


@bot.command(name="givekarma", aliases=["+rep", "thanks"])
async def givekarma(ctx: commands.Context, member: discord.Member, *, reason: str = "Being awesome!"):
    """Give karma to another user."""
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    success, message = await community_features.give_karma(
        ctx.guild.id, ctx.author.id, member.id, reason=reason
    )
    
    if success:
        await ctx.send(f"✅ {ctx.author.mention} → {member.mention}: +1 karma! {message}")
    else:
        await ctx.send(f"❌ {message}")


@bot.command(name="karmaleaderboard", aliases=["karmalb", "toprep"])
async def karmaleaderboard(ctx: commands.Context):
    """Show the karma leaderboard."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    lb = await community_features.get_karma_leaderboard(ctx.guild.id, limit=10)
    
    embed = discord.Embed(
        title=f"⭐ {ctx.guild.name} - Karma Leaderboard",
        color=discord.Color.gold()
    )
    
    if not lb:
        embed.description = "No one has karma yet!"
    else:
        description = ""
        for i, (user_id, karma) in enumerate(lb, 1):
            member = ctx.guild.get_member(user_id)
            if member:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
                description += f"{medal} {member.mention} - **{karma}** karma\n"
        embed.description = description
    
    await ctx.send(embed=embed)


@bot.command(name="giveaway", aliases=["gstart"])
@commands.has_permissions(manage_guild=True)
async def giveaway(ctx: commands.Context, duration: str, winners: int, *, prize: str):
    """Start a giveaway. Example: !giveaway 1h 2 Discord Nitro"""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    seconds = utils_misc.parse_duration(duration)
    giveaway_id = await community_features.create_giveaway(
        ctx.guild.id, ctx.channel.id, prize, seconds, ctx.author.id, winners
    )
    
    end_time = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)
    
    if not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    embed = await community_features.create_giveaway_embed(prize, end_time, ctx.author)
    
    message = await ctx.send(embed=embed)
    await message.add_reaction("🎉")
    
    # Store message ID
    from discord_bot.storage_api import database_connect
    conn = database_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE giveaways SET message_id = ? WHERE id = ?", (message.id, giveaway_id))
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ Giveaway started! Ends <t:{int(end_time.timestamp())}:R>")


@bot.command(name="event", aliases=["createevent"])
async def create_event_cmd(ctx: commands.Context, title: str, start_time: str, *, description: str | None = None):
    """
    Create an event. 
    Example: !event "Game Night" "2024-01-15 20:00" Fun gaming session!
    """
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    try:
        # Parse time (simple format: YYYY-MM-DD HH:MM)
        start_dt = dt.datetime.fromisoformat(start_time).replace(tzinfo=dt.timezone.utc)
    except Exception:
        await ctx.send("Invalid time format! Use: YYYY-MM-DD HH:MM (e.g., 2024-01-15 20:00)")
        return
    
    event_id = await community_features.create_event(
        ctx.guild.id, title, start_dt, ctx.author.id, description or ""
    )
    
    embed = await community_features.create_event_embed(title, start_dt, ctx.author, description or "")
    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    
    await ctx.send(f"✅ Event created! ID: {event_id}")


@bot.command(name="confess", aliases=["confession"])
async def confess(ctx: commands.Context, *, content: str):
    """Submit an anonymous confession (via DM for anonymity)."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    # Delete the command message for privacy
    try:
        await ctx.message.delete()
    except Exception:
        pass
    
    confession_number = await community_features.submit_confession(
        ctx.guild.id, ctx.author.id, content
    )
    
    # Post to confession channel (you can configure this)
    embed = await community_features.create_confession_embed(confession_number, content)
    await ctx.send(embed=embed)


@bot.command(name="serverstats", aliases=["serverinfo"])
async def serverstats(ctx: commands.Context):
    """Show server statistics dashboard."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    stats = await community_features.get_server_stats(ctx.guild.id, days=7)
    embed = await community_features.create_stats_embed(ctx.guild, stats)
    await ctx.send(embed=embed)


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
# Gaming & Nerd Utilities Commands (DnD, MTG, etc.)
# =============================================================================

@bot.command(name="droll", aliases=["dr", "diceroll"])
async def droll(ctx: commands.Context, *, expression: str):
    """
    Advanced dice roller with advantage/disadvantage support.
    Examples: !droll 2d20, !droll 3d6+5, !droll 1d20 advantage
    """
    try:
        result = gaming_utilities.roll_dice_detailed(expression)
    except Exception as exc:
        await ctx.send(f"❌ {exc}")
        return
    
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=result["expression"],
        color=discord.Color.blue()
    )
    
    # Show rolls
    rolls_text = ", ".join(str(r) for r in result["rolls"])
    embed.add_field(name="Rolls", value=rolls_text, inline=False)
    
    # Show advantage/disadvantage info
    if result.get("advantage"):
        embed.add_field(
            name=result["advantage"],
            value=f"Kept: {result['rolls'][0]}, Discarded: {result['discarded']}",
            inline=False
        )
    
    # Show modifier if any
    if result["modifier"] != 0:
        embed.add_field(name="Modifier", value=f"{result['modifier']:+d}", inline=True)
    
    # Show total
    embed.add_field(name="**Total**", value=f"**{result['total']}**", inline=True)
    
    # Add special indicators
    if result.get("critical"):
        embed.add_field(name="✨", value="**CRITICAL!**", inline=True)
    elif result.get("fumble"):
        embed.add_field(name="💀", value="**FUMBLE!**", inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name="stats", aliases=["abilities", "abilityscores"])
async def stats(ctx: commands.Context, method: str = "standard"):
    """
    Generate ability scores for D&D character.
    Methods: standard (4d6 drop lowest), point_buy, array
    Example: !stats standard
    """
    try:
        scores = gaming_utilities.generate_ability_scores(method)
    except Exception as exc:
        await ctx.send(f"❌ {exc}")
        return
    
    embed = discord.Embed(
        title="⚔️ Ability Scores Generated",
        description=f"Method: {method.replace('_', ' ').title()}",
        color=discord.Color.green()
    )
    
    score_text = " | ".join(str(s) for s in scores)
    embed.add_field(name="Scores", value=score_text, inline=False)
    embed.add_field(name="Total", value=str(sum(scores)), inline=True)
    embed.add_field(name="Average", value=f"{sum(scores) / len(scores):.1f}", inline=True)
    
    embed.set_footer(text="Assign these to STR, DEX, CON, INT, WIS, CHA as desired")
    
    await ctx.send(embed=embed)


@bot.command(name="loot", aliases=["treasure", "generateloot"])
async def loot(ctx: commands.Context, rarity: str = "common", count: int = 1):
    """
    Generate random loot from treasure tables.
    Rarities: common, uncommon, rare, legendary
    Example: !loot rare 3
    """
    if count < 1 or count > 10:
        await ctx.send("Count must be between 1 and 10.")
        return
    
    items = gaming_utilities.generate_loot(rarity, count)
    
    embed = discord.Embed(
        title=f"💰 {rarity.title()} Loot",
        description=f"Generated {len(items)} item(s)",
        color=discord.Color.gold()
    )
    
    loot_text = "\n".join(f"• {item}" for item in items)
    embed.add_field(name="Items", value=loot_text, inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="encounter", aliases=["generateencounter"])
async def encounter(ctx: commands.Context, party_level: int, party_size: int = 4):
    """
    Generate a balanced combat encounter.
    Example: !encounter 5 4 (level 5 party of 4)
    """
    if party_level < 1 or party_level > 20:
        await ctx.send("Party level must be between 1 and 20.")
        return
    
    if party_size < 1 or party_size > 10:
        await ctx.send("Party size must be between 1 and 10.")
        return
    
    enc = gaming_utilities.generate_encounter(party_level, party_size)
    
    embed = discord.Embed(
        title="⚔️ Encounter Generated",
        description=f"Party: Level {party_level}, Size {party_size}",
        color=discord.Color.red()
    )
    
    embed.add_field(name="Challenge Rating", value=enc["cr"], inline=True)
    embed.add_field(name="Difficulty", value=enc["difficulty"], inline=True)
    embed.add_field(name="Monster Count", value=str(enc["count"]), inline=True)
    
    monsters_text = "\n".join(f"• {monster}" for monster in enc["monsters"])
    embed.add_field(name="Monsters", value=monsters_text, inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="initiative", aliases=["init"])
async def initiative(ctx: commands.Context, action: str, name: str = "", initiative: int = 0):
    """
    Track initiative for combat.
    Actions: add, remove, next, show, clear
    Examples:
      !initiative add Goblin 15
      !initiative next
      !initiative show
      !initiative clear
    """
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    tracker = gaming_utilities.get_initiative_tracker(ctx.guild.id)
    action = action.lower()
    
    if action == "add":
        if not name:
            await ctx.send("Usage: !initiative add <name> <initiative>")
            return
        tracker.add_combatant(name, initiative)
        await ctx.send(f"✅ Added **{name}** with initiative **{initiative}**")
    
    elif action == "remove":
        if not name:
            await ctx.send("Usage: !initiative remove <name>")
            return
        if tracker.remove_combatant(name):
            await ctx.send(f"✅ Removed **{name}** from initiative")
        else:
            await ctx.send(f"❌ **{name}** not found in initiative")
    
    elif action == "next":
        combatant = tracker.next_turn()
        if not combatant:
            await ctx.send("❌ No combatants in initiative. Use `!initiative add` first.")
            return
        name, init = combatant
        await ctx.send(f"🎯 **Round {tracker.round_number}**: {name}'s turn! (Initiative: {init})")
    
    elif action == "show":
        order = tracker.get_order()
        if not order:
            await ctx.send("❌ No combatants in initiative. Use `!initiative add` first.")
            return
        
        embed = discord.Embed(
            title="⚔️ Initiative Tracker",
            description=f"Round {tracker.round_number}",
            color=discord.Color.purple()
        )
        
        order_text = ""
        for name, init, is_current in order:
            marker = "→" if is_current else " "
            order_text += f"{marker} **{name}**: {init}\n"
        
        embed.add_field(name="Turn Order", value=order_text, inline=False)
        await ctx.send(embed=embed)
    
    elif action == "clear":
        tracker.clear()
        await ctx.send("✅ Initiative tracker cleared")
    
    else:
        await ctx.send("Invalid action. Use: add, remove, next, show, or clear")


@bot.command(name="npc", aliases=["generatenpc", "randomnpc"])
async def npc(ctx: commands.Context):
    """Generate a random NPC with personality and quirk."""
    npc = gaming_utilities.generate_npc()
    
    embed = discord.Embed(
        title=f"👤 {npc['name']}",
        color=discord.Color.teal()
    )
    
    embed.add_field(name="Personality", value=npc["personality"], inline=False)
    embed.add_field(name="Quirk", value=npc["quirk"], inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="quest", aliases=["questhook", "questidea"])
async def quest(ctx: commands.Context):
    """Generate a random quest hook/idea."""
    hook = gaming_utilities.generate_quest_hook()
    
    embed = discord.Embed(
        title="📜 Quest Hook",
        description=hook,
        color=discord.Color.orange()
    )
    
    await ctx.send(embed=embed)


@bot.command(name="name", aliases=["randomname", "fantasyname"])
async def name(ctx: commands.Context):
    """Generate a random fantasy name."""
    import random
    first = random.choice(gaming_utilities.FANTASY_FIRST_NAMES)
    last = random.choice(gaming_utilities.FANTASY_LAST_NAMES)
    full_name = f"{first} {last}"
    
    await ctx.send(f"✨ **{full_name}**")


@bot.command(name="deck", aliases=["decklist", "mtgdeck"])
async def deck(ctx: commands.Context, *, decklist: str):
    """
    Parse MTG decklist from text format.
    Example:
      !deck 4 Lightning Bolt
      2 Counterspell
      20 Island
    """
    deck_data = await gaming_utilities.parse_decklist(decklist)
    embed = gaming_utilities.create_decklist_embed(deck_data, "Your Deck")
    await ctx.send(embed=embed)


# =============================================================================
# AI Chatbot Commands
# =============================================================================

@bot.command(name="ai", aliases=["ask", "chat"])
async def ai_chat(ctx: commands.Context, *, message: str):
    """
    Chat with the AI bot with context awareness and memory.
    Example: !ai What's the weather like?
    """
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    # Check cooldown
    settings = await ai_integration.AISettings.get_settings(ctx.guild.id)
    can_use, remaining = await ai_integration.ai_chat.check_cooldown(
        ctx.author.id, settings["cooldown_seconds"]
    )
    
    if not can_use:
        await ctx.send(f"⏱️ Please wait {remaining:.1f} more seconds before using AI chat again.")
        return
    
    # Show typing indicator
    async with ctx.typing():
        response = await ai_integration.ai_chat.generate_response(
            message, ctx.guild.id, ctx.channel.id, ctx.author.id, ctx.author.display_name
        )
    
    # Set cooldown
    ai_integration.ai_chat.set_cooldown(ctx.author.id)
    
    await ctx.send(response[:2000])


@bot.command(name="remember", aliases=["storemem", "aimemory"])
async def remember(ctx: commands.Context, key: str, *, value: str):
    """
    Store a memory for the AI to remember about you.
    Example: !remember favoritecolor blue
    """
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    await ai_integration.AIMemoryManager.store_user_memory(
        ctx.guild.id, ctx.author.id, key, value
    )
    await ctx.send(f"✅ Remembered: {key} = {value}")


@bot.command(name="forget", aliases=["forgetmem"])
async def forget_memory(ctx: commands.Context, key: str):
    """
    Forget a specific memory the AI has about you.
    Example: !forget favoritecolor
    """
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    success = await ai_integration.AIMemoryManager.forget_user_memory(
        ctx.guild.id, ctx.author.id, key
    )
    
    if success:
        await ctx.send(f"✅ Forgot memory: {key}")
    else:
        await ctx.send(f"❌ No memory found with key: {key}")


@bot.command(name="memories", aliases=["listmem", "mymemories"])
async def list_memories(ctx: commands.Context, member: discord.Member | None = None):
    """
    List all memories the AI has about you or another user.
    Example: !memories @user
    """
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    target = member if member else ctx.author
    if not isinstance(target, discord.Member):
        await ctx.send("User not found.")
        return
    
    memories = await ai_integration.AIMemoryManager.get_user_memories(
        ctx.guild.id, target.id
    )
    
    if not memories:
        await ctx.send(f"No memories stored for {target.mention}")
        return
    
    embed = discord.Embed(
        title=f"🧠 Memories for {target.display_name}",
        color=discord.Color.blue()
    )
    
    for mem in memories[:10]:  # Show first 10
        embed.add_field(
            name=mem["key"],
            value=mem["value"],
            inline=False
        )
    
    if len(memories) > 10:
        embed.set_footer(text=f"Showing 10 of {len(memories)} memories")
    
    await ctx.send(embed=embed)


@bot.command(name="clearmemories", aliases=["clearmem"])
async def clear_memories(ctx: commands.Context):
    """Clear all memories the AI has about you."""
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    count = await ai_integration.AIMemoryManager.clear_user_memories(
        ctx.guild.id, ctx.author.id
    )
    await ctx.send(f"✅ Cleared {count} memory/memories")


@bot.command(name="lore", aliases=["addlore", "serverlore"])
async def add_lore(ctx: commands.Context, key: str, *, value: str):
    """
    Add server-wide lore that the AI can reference.
    Example: !lore kingdom "The Kingdom of Avalon is ruled by Queen Elara"
    """
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions to add lore.")
        return
    
    await ai_integration.AIMemoryManager.store_lore(ctx.guild.id, key, value)
    await ctx.send(f"✅ Added lore: {key}")


@bot.command(name="forgetlore", aliases=["removelore"])
async def forget_lore(ctx: commands.Context, key: str):
    """Remove server-wide lore."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions to remove lore.")
        return
    
    success = await ai_integration.AIMemoryManager.forget_lore(ctx.guild.id, key)
    
    if success:
        await ctx.send(f"✅ Removed lore: {key}")
    else:
        await ctx.send(f"❌ No lore found with key: {key}")


@bot.command(name="listlore", aliases=["showlore", "alllore"])
async def list_lore(ctx: commands.Context):
    """List all server-wide lore."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    lore = await ai_integration.AIMemoryManager.get_lore(ctx.guild.id, limit=10)
    
    if not lore:
        await ctx.send("No server lore stored yet.")
        return
    
    embed = discord.Embed(
        title=f"📚 {ctx.guild.name} - Server Lore",
        color=discord.Color.purple()
    )
    
    for entry in lore:
        embed.add_field(
            name=entry["key"],
            value=entry["value"],
            inline=False
        )
    
    if len(lore) >= 10:
        embed.set_footer(text="Showing first 10 entries")
    
    await ctx.send(embed=embed)


@bot.command(name="persona", aliases=["setpersona", "aipersona"])
async def set_persona(ctx: commands.Context, persona_name: str):
    """
    Set the active AI personality.
    Built-in personas: default, serious, casual, lorekeeper, dungeon_master
    Example: !persona lorekeeper
    """
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions to change AI persona.")
        return
    
    # Check if persona exists
    personas = await ai_integration.get_personas(ctx.guild.id)
    persona_names = [p["name"] for p in personas]
    
    if persona_name not in persona_names:
        await ctx.send(f"❌ Persona '{persona_name}' not found. Available: {', '.join(persona_names)}")
        return
    
    await ai_integration.AISettings.update_setting(ctx.guild.id, "active_persona", persona_name)
    await ctx.send(f"✅ AI persona set to: **{persona_name}**")


@bot.command(name="personas", aliases=["listpersonas"])
async def list_personas(ctx: commands.Context):
    """List all available AI personalities."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    personas = await ai_integration.get_personas(ctx.guild.id)
    
    embed = discord.Embed(
        title="🎭 Available AI Personas",
        color=discord.Color.gold()
    )
    
    for persona in personas:
        persona_type = "Built-in" if persona.get("builtin") else "Custom"
        traits = ", ".join(persona["traits"])
        embed.add_field(
            name=f"{persona['name']} ({persona_type})",
            value=f"{persona['prompt'][:100]}...\nTraits: {traits}",
            inline=False
        )
    
    await ctx.send(embed=embed)


@bot.command(name="createpersona", aliases=["addpersona"])
async def create_persona(ctx: commands.Context, name: str, *, prompt: str):
    """
    Create a custom AI persona (admins only).
    Example: !createpersona pirate "You are a pirate captain. Speak like a pirate."
    """
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return
    
    if not is_admin(ctx.author):
        await ctx.send("You need administrator permissions.")
        return
    
    success = await ai_integration.create_persona(
        ctx.guild.id, name, prompt, ["custom"], ctx.author.id
    )
    
    if success:
        await ctx.send(f"✅ Created custom persona: **{name}**")
    else:
        await ctx.send(f"❌ Failed to create persona. It may already exist.")


@bot.command(name="deletepersona", aliases=["removepersona"])
async def delete_persona(ctx: commands.Context, name: str):
    """Delete a custom AI persona (admins only)."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    if not isinstance(ctx.author, discord.Member) or not is_admin(ctx.author):
        await ctx.send("You need administrator permissions.")
        return
    
    success = await ai_integration.delete_persona(ctx.guild.id, name)
    
    if success:
        await ctx.send(f"✅ Deleted persona: **{name}**")
    else:
        await ctx.send(f"❌ Persona not found or cannot be deleted.")


@bot.command(name="clearcontext", aliases=["clearchat", "resetcontext"])
async def clear_context(ctx: commands.Context):
    """Clear the AI conversation history for this channel."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    if not _mod_check(ctx):
        await ctx.send("You need moderator permissions.")
        return
    
    count = await ai_integration.ConversationContext.clear_channel_history(
        ctx.guild.id, ctx.channel.id
    )
    await ctx.send(f"✅ Cleared {count} message(s) from conversation history")


@bot.command(name="aisettings", aliases=["aiconfig"])
async def ai_settings(ctx: commands.Context):
    """View current AI settings for this server."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    settings = await ai_integration.AISettings.get_settings(ctx.guild.id)
    
    embed = discord.Embed(
        title=f"⚙️ AI Settings - {ctx.guild.name}",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Active Persona", value=settings["active_persona"], inline=True)
    embed.add_field(name="Language", value=settings["language"], inline=True)
    embed.add_field(name="NSFW Filter", value="✅ Enabled" if settings["nsfw_filter"] else "❌ Disabled", inline=True)
    embed.add_field(name="Cooldown", value=f"{settings['cooldown_seconds']}s", inline=True)
    embed.add_field(name="Context Messages", value=str(settings["max_context_messages"]), inline=True)
    embed.add_field(name="Roleplay", value="✅ Allowed" if settings["allow_roleplay"] else "❌ Disabled", inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name="ainsfwfilter", aliases=["togglensfw"])
@commands.has_permissions(administrator=True)
async def toggle_nsfw_filter(ctx: commands.Context, enabled: bool):
    """
    Enable or disable AI NSFW content filter (admins only).
    Example: !ainsfwfilter true
    """
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    await ai_integration.AISettings.update_setting(ctx.guild.id, "nsfw_filter", enabled)
    status = "enabled" if enabled else "disabled"
    await ctx.send(f"✅ NSFW filter {status}")


@bot.command(name="aicooldown", aliases=["setaicooldown"])
@commands.has_permissions(administrator=True)
async def set_ai_cooldown(ctx: commands.Context, seconds: int):
    """
    Set AI chat cooldown in seconds (admins only).
    Example: !aicooldown 5
    """
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    
    if seconds < 0 or seconds > 60:
        await ctx.send("Cooldown must be between 0 and 60 seconds.")
        return
    
    await ai_integration.AISettings.update_setting(ctx.guild.id, "cooldown_seconds", seconds)
    await ctx.send(f"✅ AI cooldown set to {seconds} seconds")


# =============================================================================
# External API Commands (Gaming, Security, etc.)
# =============================================================================

@bot.command(name="mtgcard", aliases=["card", "mtg"])
async def mtgcard(ctx: commands.Context, *, card_name: str):
    """
    Search for a Magic: The Gathering card.
    Example: !mtgcard Lightning Bolt
    """
    card = await external_apis.ScryfallAPI.get_card_by_name(card_name)
    
    if not card:
        await ctx.send(f"❌ Card '{card_name}' not found.")
        return
    
    embed = discord.Embed(
        title=card.get("name", "Unknown"),
        description=card.get("type_line", ""),
        color=discord.Color.purple(),
        url=card.get("scryfall_uri", "")
    )
    
    if card.get("mana_cost"):
        embed.add_field(name="Mana Cost", value=card["mana_cost"], inline=True)
    
    if card.get("oracle_text"):
        text = card["oracle_text"][:1000]
        embed.add_field(name="Text", value=text, inline=False)
    
    if card.get("power") and card.get("toughness"):
        embed.add_field(name="P/T", value=f"{card['power']}/{card['toughness']}", inline=True)
    
    if card.get("image_uris", {}).get("normal"):
        embed.set_image(url=card["image_uris"]["normal"])
    
    await ctx.send(embed=embed)


@bot.command(name="randomcard", aliases=["randommtg"])
async def randomcard(ctx: commands.Context):
    """Get a random Magic: The Gathering card."""
    card = await external_apis.ScryfallAPI.get_random_card()
    
    if not card:
        await ctx.send("❌ Could not fetch random card.")
        return
    
    embed = discord.Embed(
        title=card.get("name", "Unknown"),
        description=card.get("type_line", ""),
        color=discord.Color.purple(),
        url=card.get("scryfall_uri", "")
    )
    
    if card.get("image_uris", {}).get("normal"):
        embed.set_image(url=card["image_uris"]["normal"])
    
    await ctx.send(embed=embed)


@bot.command(name="dndspell", aliases=["spell", "5espell"])
async def dndspell(ctx: commands.Context, *, spell_name: str):
    """
    Search for a D&D 5e spell.
    Example: !dndspell fireball
    """
    spells = await external_apis.Open5eAPI.search_spells(spell_name)
    
    if not spells:
        await ctx.send(f"❌ No spells found for '{spell_name}'")
        return
    
    spell = spells[0]  # Get first result
    
    embed = discord.Embed(
        title=f"📜 {spell.get('name', 'Unknown')}",
        description=spell.get('desc', 'No description'),
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Level", value=f"Level {spell.get('level', '?')}", inline=True)
    embed.add_field(name="School", value=spell.get('school', 'Unknown'), inline=True)
    embed.add_field(name="Casting Time", value=spell.get('casting_time', 'Unknown'), inline=True)
    embed.add_field(name="Range", value=spell.get('range', 'Unknown'), inline=True)
    embed.add_field(name="Duration", value=spell.get('duration', 'Unknown'), inline=True)
    
    if spell.get('components'):
        embed.add_field(name="Components", value=spell['components'], inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name="dndmonster", aliases=["monster", "5emonster"])
async def dndmonster(ctx: commands.Context, *, monster_name: str):
    """
    Search for a D&D 5e monster.
    Example: !dndmonster goblin
    """
    monsters = await external_apis.Open5eAPI.search_monsters(monster_name)
    
    if not monsters:
        await ctx.send(f"❌ No monsters found for '{monster_name}'")
        return
    
    monster = monsters[0]  # Get first result
    
    embed = discord.Embed(
        title=f"👹 {monster.get('name', 'Unknown')}",
        description=f"**{monster.get('size', 'Unknown')} {monster.get('type', 'creature')}**",
        color=discord.Color.red()
    )
    
    embed.add_field(name="CR", value=monster.get('challenge_rating', '?'), inline=True)
    embed.add_field(name="AC", value=monster.get('armor_class', '?'), inline=True)
    embed.add_field(name="HP", value=monster.get('hit_points', '?'), inline=True)
    
    # Add ability scores
    stats = f"**STR** {monster.get('strength', 10)} "
    stats += f"**DEX** {monster.get('dexterity', 10)} "
    stats += f"**CON** {monster.get('constitution', 10)}\n"
    stats += f"**INT** {monster.get('intelligence', 10)} "
    stats += f"**WIS** {monster.get('wisdom', 10)} "
    stats += f"**CHA** {monster.get('charisma', 10)}"
    embed.add_field(name="Ability Scores", value=stats, inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name="github", aliases=["repo", "ghrepo"])
async def github_repo(ctx: commands.Context, owner: str, repo: str):
    """
    Get information about a GitHub repository.
    Example: !github microsoft vscode
    """
    repo_info = await external_apis.GitHubAPI.get_repo_info(owner, repo)
    
    if not repo_info:
        await ctx.send(f"❌ Repository '{owner}/{repo}' not found.")
        return
    
    embed = discord.Embed(
        title=repo_info.get("full_name", "Unknown"),
        description=repo_info.get("description", "No description"),
        color=discord.Color.from_rgb(36, 41, 46),
        url=repo_info.get("html_url", "")
    )
    
    embed.add_field(name="⭐ Stars", value=f"{repo_info.get('stargazers_count', 0):,}", inline=True)
    embed.add_field(name="🍴 Forks", value=f"{repo_info.get('forks_count', 0):,}", inline=True)
    embed.add_field(name="👁️ Watchers", value=f"{repo_info.get('watchers_count', 0):,}", inline=True)
    
    if repo_info.get("language"):
        embed.add_field(name="Language", value=repo_info["language"], inline=True)
    
    if repo_info.get("license"):
        embed.add_field(name="License", value=repo_info["license"].get("name", "Unknown"), inline=True)
    
    embed.add_field(name="Open Issues", value=str(repo_info.get("open_issues_count", 0)), inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name="apistatus", aliases=["apis", "checkapis"])
async def apistatus(ctx: commands.Context):
    """Check the status of all configured external APIs."""
    status = await external_apis.APIStatusChecker.check_all()
    message = external_apis.APIStatusChecker.format_status_message(status)
    
    embed = discord.Embed(
        title="🔌 External API Status",
        description="Showing which APIs are configured and available",
        color=discord.Color.blue()
    )
    
    # Add AI providers
    ai_status = ""
    for name, available in status["ai_providers"].items():
        emoji = "✅" if available else "❌"
        ai_status += f"{emoji} {name.title()}\n"
    embed.add_field(name="AI Providers", value=ai_status or "None", inline=True)
    
    # Add gaming APIs
    gaming_status = ""
    for name, available in status["gaming"].items():
        emoji = "✅" if available else "❌"
        gaming_status += f"{emoji} {name.title()}\n"
    embed.add_field(name="Gaming APIs", value=gaming_status or "None", inline=True)
    
    # Add security APIs
    security_status = ""
    for name, available in status["security"].items():
        emoji = "✅" if available else "❌"
        security_status += f"{emoji} {name.title()}\n"
    embed.add_field(name="Security APIs", value=security_status or "None", inline=True)
    
    embed.set_footer(text="Configure API keys in .env file to enable more features")
    
    await ctx.send(embed=embed)


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
