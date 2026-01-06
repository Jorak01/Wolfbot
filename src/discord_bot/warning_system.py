"""
Warning and strike system with escalation rules for Discord servers.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional, List, Dict, Tuple

import discord

from .storage_api import database_connect


# =============================
# Database Setup
# =============================

def init_warning_database() -> None:
    """Initialize the warning system database tables."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # Warnings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_warnings_user 
        ON warnings(guild_id, user_id, active)
    """)
    
    conn.commit()
    conn.close()


# =============================
# Escalation Rules
# =============================

class EscalationRule:
    """Defines what action to take at each warning threshold."""
    
    def __init__(self, warning_count: int, action: str, duration: Optional[int] = None):
        """
        Args:
            warning_count: Number of warnings to trigger this rule
            action: Action to take ("timeout", "kick", "ban", "none")
            duration: Duration in seconds for timeout/ban (None for permanent)
        """
        self.warning_count = warning_count
        self.action = action
        self.duration = duration


# Default escalation rules
DEFAULT_ESCALATION_RULES = [
    EscalationRule(1, "none"),  # First warning - just warn
    EscalationRule(2, "timeout", 3600),  # 2 warnings - 1 hour timeout
    EscalationRule(3, "timeout", 86400),  # 3 warnings - 24 hour timeout
    EscalationRule(4, "kick"),  # 4 warnings - kick
    EscalationRule(5, "ban"),  # 5 warnings - ban
]


def get_escalation_action(warning_count: int, rules: Optional[List[EscalationRule]] = None) -> Tuple[str, Optional[int]]:
    """
    Get the action to take based on warning count.
    
    Args:
        warning_count: Current number of warnings
        rules: Custom escalation rules (uses defaults if None)
    
    Returns:
        Tuple of (action, duration)
    """
    if rules is None:
        rules = DEFAULT_ESCALATION_RULES
    
    # Sort rules by warning count descending to get the highest applicable rule
    sorted_rules = sorted(rules, key=lambda r: r.warning_count, reverse=True)
    
    for rule in sorted_rules:
        if warning_count >= rule.warning_count:
            return rule.action, rule.duration
    
    return "none", None


# =============================
# Warning Management
# =============================

async def add_warning(
    guild_id: int,
    user_id: int,
    moderator_id: int,
    reason: str
) -> int:
    """
    Add a warning to a user.
    
    Args:
        guild_id: The guild ID
        user_id: The user ID
        moderator_id: The moderator ID who issued the warning
        reason: The reason for the warning
    
    Returns:
        The warning ID
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
        VALUES (?, ?, ?, ?)
    """, (guild_id, user_id, moderator_id, reason))
    
    warning_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Ensure we always return an int (lastrowid should never be None after INSERT)
    if warning_id is None:
        raise RuntimeError("Failed to retrieve warning ID after insert")
    
    return warning_id


async def remove_warning(warning_id: int) -> bool:
    """
    Remove (deactivate) a warning.
    
    Args:
        warning_id: The warning ID
    
    Returns:
        True if warning was removed, False otherwise
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE warnings
        SET active = 0
        WHERE id = ?
    """, (warning_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success


async def get_user_warnings(
    guild_id: int,
    user_id: int,
    active_only: bool = True
) -> List[Dict]:
    """
    Get all warnings for a user.
    
    Args:
        guild_id: The guild ID
        user_id: The user ID
        active_only: Only return active warnings
    
    Returns:
        List of warning dictionaries
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    if active_only:
        cursor.execute("""
            SELECT * FROM warnings
            WHERE guild_id = ? AND user_id = ? AND active = 1
            ORDER BY timestamp DESC
        """, (guild_id, user_id))
    else:
        cursor.execute("""
            SELECT * FROM warnings
            WHERE guild_id = ? AND user_id = ?
            ORDER BY timestamp DESC
        """, (guild_id, user_id))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


async def get_warning_count(guild_id: int, user_id: int) -> int:
    """
    Get the number of active warnings for a user.
    
    Args:
        guild_id: The guild ID
        user_id: The user ID
    
    Returns:
        Number of active warnings
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM warnings
        WHERE guild_id = ? AND user_id = ? AND active = 1
    """, (guild_id, user_id))
    
    result = cursor.fetchone()
    count = result[0] if result else 0
    conn.close()
    
    return count


async def clear_user_warnings(guild_id: int, user_id: int) -> int:
    """
    Clear all warnings for a user.
    
    Args:
        guild_id: The guild ID
        user_id: The user ID
    
    Returns:
        Number of warnings cleared
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE warnings
        SET active = 0
        WHERE guild_id = ? AND user_id = ? AND active = 1
    """, (guild_id, user_id))
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return count


# =============================
# Warning System with Escalation
# =============================

async def warn_user_with_escalation(
    member: discord.Member,
    moderator: discord.Member,
    reason: str,
    rules: Optional[List[EscalationRule]] = None
) -> Tuple[int, str, Optional[str]]:
    """
    Warn a user and apply escalation rules.
    
    Args:
        member: The member to warn
        moderator: The moderator issuing the warning
        reason: The reason for the warning
        rules: Custom escalation rules (uses defaults if None)
    
    Returns:
        Tuple of (warning_count, action_taken, escalation_message)
    """
    # Add the warning
    warning_id = await add_warning(
        member.guild.id,
        member.id,
        moderator.id,
        reason
    )
    
    # Get new warning count
    warning_count = await get_warning_count(member.guild.id, member.id)
    
    # Get escalation action
    action, duration = get_escalation_action(warning_count, rules)
    
    # Notify user
    try:
        await member.send(
            f"⚠️ You have been warned in **{member.guild.name}**\n"
            f"**Reason:** {reason}\n"
            f"**Total Warnings:** {warning_count}"
        )
    except Exception:
        pass  # Can't DM user
    
    # Apply escalation action
    escalation_message = None
    if action == "timeout" and duration:
        from . import moderation
        await moderation.timeout_user(member, duration, reason=f"Warning escalation: {reason}")
        escalation_message = f"⏱️ {member.mention} has been timed out for {duration} seconds (Warning #{warning_count})"
    
    elif action == "kick":
        from . import moderation
        await moderation.kick_user(member, reason=f"Warning escalation: {reason}")
        escalation_message = f"👢 {member.mention} has been kicked (Warning #{warning_count})"
    
    elif action == "ban":
        from . import moderation
        await moderation.ban_user(member, reason=f"Warning escalation: {reason}")
        escalation_message = f"🔨 {member.mention} has been banned (Warning #{warning_count})"
    
    return warning_count, action, escalation_message


async def format_warnings_embed(
    member: discord.Member,
    warnings: List[Dict]
) -> discord.Embed:
    """
    Format warnings into an embed.
    
    Args:
        member: The member whose warnings to display
        warnings: List of warning dictionaries
    
    Returns:
        Formatted embed
    """
    warning_count = len([w for w in warnings if w.get("active", 0)])
    
    embed = discord.Embed(
        title=f"⚠️ Warnings for {member.display_name}",
        description=f"**Active Warnings:** {warning_count}",
        color=discord.Color.orange(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    if not warnings:
        embed.add_field(
            name="No Warnings",
            value="This user has a clean record.",
            inline=False
        )
        return embed
    
    # Show up to 10 most recent warnings
    for i, warning in enumerate(warnings[:10], 1):
        status = "✅ Active" if warning.get("active", 0) else "❌ Removed"
        reason = warning.get("reason", "No reason provided")
        timestamp = warning.get("timestamp", "Unknown")
        warning_id = warning.get("id", "Unknown")
        
        field_value = f"**Status:** {status}\n"
        field_value += f"**Reason:** {reason}\n"
        field_value += f"**Date:** {timestamp}\n"
        field_value += f"**ID:** {warning_id}"
        
        embed.add_field(
            name=f"Warning #{i}",
            value=field_value,
            inline=False
        )
    
    if len(warnings) > 10:
        embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")
    
    return embed


async def get_leaderboard(guild_id: int, limit: int = 10) -> List[Tuple[int, int]]:
    """
    Get warning leaderboard for a guild.
    
    Args:
        guild_id: The guild ID
        limit: Maximum number of users to return
    
    Returns:
        List of (user_id, warning_count) tuples
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, COUNT(*) as warning_count
        FROM warnings
        WHERE guild_id = ? AND active = 1
        GROUP BY user_id
        ORDER BY warning_count DESC
        LIMIT ?
    """, (guild_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows


async def format_leaderboard_embed(
    guild: discord.Guild,
    leaderboard: List[Tuple[int, int]]
) -> discord.Embed:
    """
    Format warning leaderboard into an embed.
    
    Args:
        guild: The guild
        leaderboard: List of (user_id, warning_count) tuples
    
    Returns:
        Formatted embed
    """
    embed = discord.Embed(
        title="⚠️ Warning Leaderboard",
        description="Users with the most active warnings",
        color=discord.Color.red(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    if not leaderboard:
        embed.add_field(
            name="No Warnings",
            value="No users have active warnings!",
            inline=False
        )
        return embed
    
    leaderboard_text = ""
    for i, (user_id, count) in enumerate(leaderboard, 1):
        member = guild.get_member(user_id)
        if member:
            leaderboard_text += f"**{i}.** {member.mention} - {count} warning(s)\n"
        else:
            leaderboard_text += f"**{i}.** User {user_id} - {count} warning(s)\n"
    
    embed.add_field(name="Top Users", value=leaderboard_text, inline=False)
    
    return embed


# =============================
# Automatic Warning Decay
# =============================

async def decay_old_warnings(
    guild_id: int,
    days_old: int = 30
) -> int:
    """
    Automatically deactivate warnings older than specified days.
    
    Args:
        guild_id: The guild ID
        days_old: Age threshold in days
    
    Returns:
        Number of warnings decayed
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_old)
    
    cursor.execute("""
        UPDATE warnings
        SET active = 0
        WHERE guild_id = ? 
        AND active = 1 
        AND timestamp < ?
    """, (guild_id, cutoff_date.isoformat()))
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return count


# Initialize database on module load
init_warning_database()
