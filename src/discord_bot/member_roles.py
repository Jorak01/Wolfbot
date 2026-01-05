"""
Member and role management helpers.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import discord


async def on_member_join(member: discord.Member, welcome_channel: Optional[discord.TextChannel] = None):
    if welcome_channel:
        await welcome_channel.send(f"Welcome, {member.mention}!")


async def on_member_remove(member: discord.Member, log_channel: Optional[discord.TextChannel] = None):
    if log_channel:
        await log_channel.send(f"{member.display_name} has left the server.")


async def assign_role(member: discord.Member, role_id: int, reason: str | None = None):
    role = member.guild.get_role(role_id)
    if role and role not in member.roles:
        await member.add_roles(role, reason=reason)
    return role


async def remove_role(member: discord.Member, role_id: int, reason: str | None = None):
    role = member.guild.get_role(role_id)
    if role and role in member.roles:
        await member.remove_roles(role, reason=reason)
    return role


async def sync_roles(member: discord.Member, desired_role_ids: list[int]):
    """
    Ensure member has exactly the desired roles (add missing, remove extras).
    """
    current_ids = {r.id for r in member.roles}
    desired = set(desired_role_ids)
    # Never try to remove the @everyone role.
    if member.guild and member.guild.default_role:
        desired.add(member.guild.default_role.id)
    to_add = desired - current_ids
    to_remove = current_ids - desired
    added = []
    removed = []
    for rid in to_add:
        role = member.guild.get_role(rid)
        if role:
            await member.add_roles(role, reason="Role sync add")
            added.append(role)
    for rid in to_remove:
        role = member.guild.get_role(rid)
        if role:
            await member.remove_roles(role, reason="Role sync remove")
            removed.append(role)
    return added, removed


async def temporary_role(member: discord.Member, role_id: int, duration: int):
    """
    Grant a role for `duration` seconds, then remove it.
    """
    role = await assign_role(member, role_id, reason="Temporary role grant")
    if not role:
        return None

    async def _revoke():
        await asyncio.sleep(duration)
        await remove_role(member, role_id, reason="Temporary role expired")

    asyncio.create_task(_revoke())
    return role
