import discord
from discord.ext import commands

from . import integration
from .config import require_token
from .discord_bot import analytics, command_handler, lifecycle, maintenance, storage_api, utils_misc
from .discord_bot.audio import AudioController
from .discord_bot.config_store import get_guild_config, set_guild_config
from .discord_bot.games import coin_flip, poll_creator, rps_game, roll_dice
from .discord_bot.member_roles import (
    on_member_join as handle_member_join,
    on_member_remove as handle_member_remove,
)
from .discord_bot.moderation import (
    ban_user as mod_ban_user,
    kick_user as mod_kick_user,
    lock_channel as mod_lock_channel,
    mute_user as mod_mute_user,
    purge_messages,
    unban_user as mod_unban_user,
    unlock_channel as mod_unlock_channel,
    warn_user as mod_warn_user,
)
from .discord_bot.notifications import notify_user, react_to_message, send_announcement
from .discord_bot.scheduler import temporary_message
from .discord_bot.security import is_admin, is_moderator
from .integrations.twitch_integration import TwitchIntegration
from scripts.check_imports import main as check_imports_main

intents = discord.Intents.default()
intents.message_content = True  # Enable for prefix commands
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
audio = AudioController(bot)
twitch = TwitchIntegration(bot)


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
    check_imports_main()
    await lifecycle.on_ready(bot, twitch)


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


@bot.command(name="join")
async def join(ctx: commands.Context):
    """Have the bot join your current voice channel."""
    try:
        await audio.join(ctx)
    except Exception as exc:
        await ctx.send(f"Could not join: {exc}")


@bot.command(name="play", aliases=["p"])
async def play(ctx: commands.Context, *, query: str):
    """
    Queue a YouTube/Spotify URL or search term for playback.
    Requires FFmpeg installed on the host.
    """
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return

    try:
        track = await audio.enqueue(ctx, query)
    except Exception as exc:
        await ctx.send(f"Could not play that: {exc}")
        return

    await ctx.send(f"Queued **{track.title}** ({track.webpage_url})")


@bot.command(name="skip")
async def skip(ctx: commands.Context):
    """Skip the current track."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    message = await audio.skip(ctx.guild.id)
    await ctx.send(message)


@bot.command(name="stop")
async def stop(ctx: commands.Context):
    """Stop playback and clear the queue."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    message = await audio.stop(ctx.guild.id)
    await ctx.send(message)


@bot.command(name="leave", aliases=["disconnect", "dc"])
async def leave(ctx: commands.Context):
    """Disconnect the bot from voice."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    await audio.leave(ctx.guild.id)
    await ctx.send("Disconnected.")


@bot.command(name="np", aliases=["nowplaying"])
async def now_playing(ctx: commands.Context):
    """Display the currently playing track."""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server.")
        return
    track = audio.now_playing(ctx.guild.id)
    if not track:
        await ctx.send("Nothing is playing.")
        return
    duration = f" [{track.duration // 60}:{track.duration % 60:02d}]" if track.duration else ""
    await ctx.send(f"Now playing: **{track.title}**{duration}\n{track.webpage_url}")


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
    """Check Twitch/Discord integration health."""
    status = await lifecycle.health_check(bot, twitch)
    await ctx.send(status)


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
    await lifecycle.graceful_shutdown(bot, twitch)


# --- Moderation commands -----------------------------------------------------
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


# --- Fun/games ---------------------------------------------------------------
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


# --- Notifications -----------------------------------------------------------
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


# --- Maintenance / config ----------------------------------------------------
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


# --- Storage / API -----------------------------------------------------------
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
