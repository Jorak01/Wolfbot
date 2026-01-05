"""
Centralized command handling utilities for prefix, slash, and context menu flows.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, Iterable

import discord
from discord.ext import commands

# Registries
PrefixHandler = Callable[[commands.Context], Awaitable[None]]
SlashHandler = Callable[[discord.Interaction], Awaitable[None]]
ContextHandler = Callable[[discord.Interaction], Awaitable[None]]
AutocompleteHandler = Callable[[discord.Interaction, str], Awaitable[Iterable[str]]]

PREFIX_COMMANDS: Dict[str, PrefixHandler] = {}
SLASH_COMMANDS: Dict[str, SlashHandler] = {}
CONTEXT_COMMANDS: Dict[str, ContextHandler] = {}
AUTOCOMPLETE: Dict[str, AutocompleteHandler] = {}

# Cooldown tracking: command -> user_id -> next_allowed_ts
COOLDOWNS: Dict[str, Dict[int, float]] = {}


def register_commands(
    prefix_cmds: Dict[str, PrefixHandler] | None = None,
    slash_cmds: Dict[str, SlashHandler] | None = None,
    context_cmds: Dict[str, ContextHandler] | None = None,
    autocomplete_cmds: Dict[str, AutocompleteHandler] | None = None,
) -> None:
    """Register handlers into in-memory registries."""
    if prefix_cmds:
        PREFIX_COMMANDS.update({k.lower(): v for k, v in prefix_cmds.items()})
    if slash_cmds:
        SLASH_COMMANDS.update({k.lower(): v for k, v in slash_cmds.items()})
    if context_cmds:
        CONTEXT_COMMANDS.update({k.lower(): v for k, v in context_cmds.items()})
    if autocomplete_cmds:
        AUTOCOMPLETE.update({k.lower(): v for k, v in autocomplete_cmds.items()})


async def handle_prefix_command(ctx: commands.Context):
    """Dispatch prefix command from the registry after permission/cooldown checks."""
    name = (ctx.command.name if ctx.command else "").lower()
    handler = PREFIX_COMMANDS.get(name)
    if not handler:
        return
    if not ctx.author:
        return
    if not validate_command_permissions(ctx):
        await ctx.send("You do not have permission to run this command.")
        return
    if not cooldown_check(ctx.author.id, name):
        await ctx.send("Slow down, you are on cooldown.")
        return
    await handler(ctx)


async def handle_slash_command(interaction: discord.Interaction):
    """Dispatch slash command from the registry."""
    name = (interaction.command.name if interaction.command else "").lower()
    handler = SLASH_COMMANDS.get(name)
    if not handler:
        return
    if not validate_command_permissions(interaction):
        await _send_interaction_message(interaction, "Permission denied.", ephemeral=True)
        return
    user_id = interaction.user.id if interaction.user else 0
    if not cooldown_check(user_id, name):
        await _send_interaction_message(interaction, "On cooldown.", ephemeral=True)
        return
    await handler(interaction)


async def handle_context_menu(interaction: discord.Interaction):
    """Dispatch context menu command from the registry."""
    name = (interaction.command.name if interaction.command else "").lower()
    handler = CONTEXT_COMMANDS.get(name)
    if not handler:
        return
    if not validate_command_permissions(interaction):
        await _send_interaction_message(interaction, "Permission denied.", ephemeral=True)
        return
    await handler(interaction)


def validate_command_permissions(target) -> bool:
    """
    Simple permission check: allow DMs, otherwise require send_messages.
    Extend with role checks as needed.
    """
    if isinstance(target, commands.Context):
        if target.guild is None:
            return True
        if target.channel is None:
            return False
        perms = target.channel.permissions_for(target.author)
        return perms.send_messages
    if isinstance(target, discord.Interaction):
        if target.guild is None:
            return True
        member = target.user
        if isinstance(member, discord.Member):
            if target.channel is None:
                return False
            perms = target.channel.permissions_for(member)
            return perms.send_messages
    return False


def cooldown_check(user_id: int, command: str, *, cooldown_seconds: int = 3) -> bool:
    """
    Return True if allowed; records the next allowed timestamp.
    """
    import time

    now = time.time()
    per_user = COOLDOWNS.setdefault(command, {})
    next_allowed = per_user.get(user_id, 0)
    if now < next_allowed:
        return False
    per_user[user_id] = now + cooldown_seconds
    return True


async def autocomplete_handler(interaction: discord.Interaction, value: str):
    """
    Dispatch to a registered autocomplete handler.
    """
    name = (interaction.command.name if interaction.command else "").lower()
    handler = AUTOCOMPLETE.get(name)
    if not handler:
        return []
    return await handler(interaction, value)


async def _send_interaction_message(
    interaction: discord.Interaction,
    content: str,
    *,
    ephemeral: bool = True,
):
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content, ephemeral=ephemeral)
