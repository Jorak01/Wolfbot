"""
Advanced administration tools for Discord servers.
Includes role assignment systems, audit log viewing, and more.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, List, Dict

import discord
from discord.ext import commands


# =============================
# Role Assignment Systems
# =============================

class RoleButton(discord.ui.Button):
    """Button for role assignment."""
    
    def __init__(self, role: discord.Role, label: Optional[str] = None):
        self.role = role
        super().__init__(
            label=label or role.name,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_{role.id}"
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Toggle role when button is clicked."""
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        
        member = interaction.user
        if self.role in member.roles:
            await member.remove_roles(self.role, reason="Button role removal")
            await interaction.response.send_message(
                f"Removed role: {self.role.name}", ephemeral=True
            )
        else:
            await member.add_roles(self.role, reason="Button role assignment")
            await interaction.response.send_message(
                f"Assigned role: {self.role.name}", ephemeral=True
            )


class RoleView(discord.ui.View):
    """View containing role assignment buttons."""
    
    def __init__(self, roles: List[discord.Role]):
        super().__init__(timeout=None)  # Persistent view
        for role in roles:
            self.add_item(RoleButton(role))


async def create_role_button_message(
    channel: discord.TextChannel,
    roles: List[discord.Role],
    title: str = "Select Your Roles",
    description: str = "Click the buttons below to assign or remove roles."
) -> discord.Message:
    """
    Create a persistent message with role assignment buttons.
    
    Args:
        channel: The channel to send the message to
        roles: List of roles to include as buttons
        title: Embed title
        description: Embed description
    
    Returns:
        The created message
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )
    
    # Add role information to embed
    role_list = "\n".join([f"• {role.mention}" for role in roles])
    embed.add_field(name="Available Roles", value=role_list, inline=False)
    
    view = RoleView(roles)
    message = await channel.send(embed=embed, view=view)
    return message


# Reaction role storage: message_id -> {emoji: role_id}
REACTION_ROLES: Dict[int, Dict[str, int]] = {}


async def setup_reaction_roles(
    message: discord.Message,
    role_emoji_map: Dict[discord.Role, str]
) -> None:
    """
    Set up reaction-based role assignment on a message.
    
    Args:
        message: The message to add reactions to
        role_emoji_map: Dictionary mapping roles to emoji strings
    """
    REACTION_ROLES[message.id] = {}
    
    for role, emoji in role_emoji_map.items():
        await message.add_reaction(emoji)
        REACTION_ROLES[message.id][str(emoji)] = role.id


async def handle_reaction_role_add(
    payload: discord.RawReactionActionEvent,
    bot: commands.Bot
) -> Optional[str]:
    """
    Handle reaction add for role assignment.
    
    Args:
        payload: The reaction event payload
        bot: The bot instance
    
    Returns:
        Status message or None
    """
    if bot.user and payload.user_id == bot.user.id:
        return None
    
    if payload.message_id not in REACTION_ROLES:
        return None
    
    emoji_str = str(payload.emoji)
    role_id = REACTION_ROLES[payload.message_id].get(emoji_str)
    
    if not role_id or not payload.guild_id:
        return None
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return None
    
    member = guild.get_member(payload.user_id)
    role = guild.get_role(role_id)
    
    if not member or not role:
        return None
    
    if role not in member.roles:
        await member.add_roles(role, reason="Reaction role assignment")
        return f"Assigned {role.name} to {member.display_name}"
    
    return None


async def handle_reaction_role_remove(
    payload: discord.RawReactionActionEvent,
    bot: commands.Bot
) -> Optional[str]:
    """
    Handle reaction remove for role removal.
    
    Args:
        payload: The reaction event payload
        bot: The bot instance
    
    Returns:
        Status message or None
    """
    if bot.user and payload.user_id == bot.user.id:
        return None
    
    if payload.message_id not in REACTION_ROLES:
        return None
    
    emoji_str = str(payload.emoji)
    role_id = REACTION_ROLES[payload.message_id].get(emoji_str)
    
    if not role_id or not payload.guild_id:
        return None
    
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return None
    
    member = guild.get_member(payload.user_id)
    role = guild.get_role(role_id)
    
    if not member or not role:
        return None
    
    if role in member.roles:
        await member.remove_roles(role, reason="Reaction role removal")
        return f"Removed {role.name} from {member.display_name}"
    
    return None


# =============================
# Slash Command Role Assignment
# =============================

async def slash_assign_role(
    interaction: discord.Interaction,
    member: discord.Member,
    role: discord.Role,
    reason: Optional[str] = None
) -> None:
    """
    Assign a role via slash command.
    
    Args:
        interaction: The interaction object
        member: The member to assign the role to
        role: The role to assign
        reason: Optional reason for the assignment
    """
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    # Permission check
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)
        return
    
    # Role hierarchy check
    if interaction.user.top_role <= role:
        await interaction.response.send_message("You cannot assign a role equal to or higher than your highest role.", ephemeral=True)
        return
    
    if role in member.roles:
        await interaction.response.send_message(f"{member.mention} already has the {role.mention} role.", ephemeral=True)
        return
    
    await member.add_roles(role, reason=reason or f"Assigned by {interaction.user.display_name}")
    await interaction.response.send_message(f"✅ Assigned {role.mention} to {member.mention}", ephemeral=True)


async def slash_remove_role(
    interaction: discord.Interaction,
    member: discord.Member,
    role: discord.Role,
    reason: Optional[str] = None
) -> None:
    """
    Remove a role via slash command.
    
    Args:
        interaction: The interaction object
        member: The member to remove the role from
        role: The role to remove
        reason: Optional reason for the removal
    """
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    # Permission check
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)
        return
    
    # Role hierarchy check
    if interaction.user.top_role <= role:
        await interaction.response.send_message("You cannot remove a role equal to or higher than your highest role.", ephemeral=True)
        return
    
    if role not in member.roles:
        await interaction.response.send_message(f"{member.mention} doesn't have the {role.mention} role.", ephemeral=True)
        return
    
    await member.remove_roles(role, reason=reason or f"Removed by {interaction.user.display_name}")
    await interaction.response.send_message(f"✅ Removed {role.mention} from {member.mention}", ephemeral=True)


# =============================
# Audit Log Viewer
# =============================

async def get_audit_logs(
    guild: discord.Guild,
    *,
    limit: int = 10,
    action: Optional[discord.AuditLogAction] = None,
    user: Optional[discord.User] = None,
    before: Optional[dt.datetime] = None,
    after: Optional[dt.datetime] = None
) -> List[discord.AuditLogEntry]:
    """
    Retrieve audit log entries.
    
    Args:
        guild: The guild to fetch logs from
        limit: Maximum number of entries to retrieve
        action: Filter by specific action type
        user: Filter by user who performed the action
        before: Only fetch entries before this date
        after: Only fetch entries after this date
    
    Returns:
        List of audit log entries
    """
    entries = []
    async for entry in guild.audit_logs(
        limit=limit,
        action=action if action is not None else discord.utils.MISSING,
        user=user if user is not None else discord.utils.MISSING,
        before=before if before is not None else discord.utils.MISSING,
        after=after if after is not None else discord.utils.MISSING
    ):
        entries.append(entry)
    return entries


async def format_audit_log_embed(entries: List[discord.AuditLogEntry]) -> discord.Embed:
    """
    Format audit log entries into an embed.
    
    Args:
        entries: List of audit log entries
    
    Returns:
        Formatted embed
    """
    embed = discord.Embed(
        title="📋 Audit Log",
        color=discord.Color.blue(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    if not entries:
        embed.description = "No audit log entries found."
        return embed
    
    for entry in entries[:10]:  # Limit to 10 entries to avoid embed limits
        action_name = entry.action.name.replace("_", " ").title()
        user_mention = entry.user.mention if entry.user else "Unknown"
        target = getattr(entry.target, "name", str(entry.target)) if entry.target else "Unknown"
        
        field_value = f"**User:** {user_mention}\n"
        field_value += f"**Target:** {target}\n"
        
        if entry.reason:
            field_value += f"**Reason:** {entry.reason}\n"
        
        timestamp = entry.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        field_value += f"**Time:** {timestamp}"
        
        embed.add_field(
            name=f"{action_name}",
            value=field_value,
            inline=False
        )
    
    return embed


async def view_audit_log(
    interaction: discord.Interaction,
    limit: int = 10,
    action_type: Optional[str] = None
) -> None:
    """
    View audit logs via slash command.
    
    Args:
        interaction: The interaction object
        limit: Number of entries to show
        action_type: Filter by action type (e.g., "ban", "kick", "channel_create")
    """
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    # Permission check
    if not interaction.user.guild_permissions.view_audit_log:
        await interaction.response.send_message("You don't have permission to view audit logs.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Map action type string to AuditLogAction
    action = None
    if action_type:
        action_type = action_type.lower()
        action_map = {
            "ban": discord.AuditLogAction.ban,
            "unban": discord.AuditLogAction.unban,
            "kick": discord.AuditLogAction.kick,
            "member_update": discord.AuditLogAction.member_update,
            "channel_create": discord.AuditLogAction.channel_create,
            "channel_delete": discord.AuditLogAction.channel_delete,
            "channel_update": discord.AuditLogAction.channel_update,
            "role_create": discord.AuditLogAction.role_create,
            "role_delete": discord.AuditLogAction.role_delete,
            "role_update": discord.AuditLogAction.role_update,
            "message_delete": discord.AuditLogAction.message_delete,
        }
        action = action_map.get(action_type)
    
    entries = await get_audit_logs(interaction.guild, limit=limit, action=action)
    embed = await format_audit_log_embed(entries)
    
    await interaction.followup.send(embed=embed, ephemeral=True)
