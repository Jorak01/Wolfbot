"""
Permission and security helpers for Discord members.
"""

from __future__ import annotations

import time
from typing import Optional

import discord

# Simple per-user rate limits: user_id -> next_allowed_ts
_RATE_LIMITS = {}
RATE_LIMIT_SECONDS = 3


def is_admin(member: discord.Member) -> bool:
    return bool(member.guild_permissions.administrator)


def is_moderator(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return bool(perms.manage_guild or perms.manage_messages or perms.kick_members or perms.ban_members)


def has_role(member: discord.Member, role_id: int) -> bool:
    return any(role.id == role_id for role in member.roles)


def has_permission(member: discord.Member, permission: str) -> bool:
    return bool(getattr(member.guild_permissions, permission, False))


def owner_only_check(member: discord.Member) -> bool:
    guild = member.guild
    return guild is not None and guild.owner_id == member.id


def rate_limit_check(user_id: int, *, cooldown_seconds: Optional[int] = None) -> bool:
    """Return True if user may proceed; records the next allowed timestamp."""
    now = time.time()
    cooldown = RATE_LIMIT_SECONDS if cooldown_seconds is None else cooldown_seconds
    next_allowed = _RATE_LIMITS.get(user_id, 0)
    if now < next_allowed:
        return False
    _RATE_LIMITS[user_id] = now + cooldown
    return True
