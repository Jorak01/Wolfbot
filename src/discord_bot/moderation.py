"""
Moderation utilities for Discord servers.
"""

from __future__ import annotations

import datetime as dt

import discord


async def warn_user(member: discord.Member, reason: str):
    try:
        await member.send(f"You have been warned: {reason}")
    except Exception:
        pass
    return f"Warned {member.display_name}: {reason}"


async def mute_user(member: discord.Member, duration: int, reason: str | None = None):
    """Apply a timed timeout (mute) using Discord's timeout feature."""
    until = discord.utils.utcnow() + dt.timedelta(seconds=duration)
    await member.edit(timed_out_until=until, reason=reason or "Muted")
    return f"Muted {member.display_name} for {duration} seconds."


async def timeout_user(member: discord.Member, duration: int, reason: str | None = None):
    return await mute_user(member, duration, reason)


async def kick_user(member: discord.Member, reason: str | None = None):
    await member.kick(reason=reason)
    return f"Kicked {member.display_name}."


async def ban_user(member: discord.Member, reason: str | None = None, delete_message_days: int = 1):
    await member.ban(reason=reason, delete_message_seconds=delete_message_days * 86400)
    return f"Banned {member.display_name}."


async def unban_user(guild: discord.Guild, user_id: int, reason: str | None = None):
    user = discord.Object(id=user_id)
    await guild.unban(user, reason=reason)
    return f"Unbanned user {user_id}."


async def purge_messages(channel: discord.TextChannel, amount: int, reason: str | None = None):
    deleted = await channel.purge(limit=amount, reason=reason)
    return f"Deleted {len(deleted)} messages."


async def lock_channel(channel: discord.TextChannel, reason: str | None = None):
    overwrite = channel.overwrites_for(channel.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(channel.guild.default_role, overwrite=overwrite, reason=reason)
    return f"Locked {channel.name}."


async def unlock_channel(channel: discord.TextChannel, reason: str | None = None):
    overwrite = channel.overwrites_for(channel.guild.default_role)
    overwrite.send_messages = None
    await channel.set_permissions(channel.guild.default_role, overwrite=overwrite, reason=reason)
    return f"Unlocked {channel.name}."
