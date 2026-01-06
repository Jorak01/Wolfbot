"""
Leveling and XP system for Discord servers.
Tracks user activity and rewards with levels and roles.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Optional, List, Dict, Tuple

import discord

from .storage_api import database_connect


# =============================
# Database Setup
# =============================

def init_leveling_database() -> None:
    """Initialize the leveling system database tables."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # User XP table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_xp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0,
            last_message_time TIMESTAMP,
            total_messages INTEGER DEFAULT 0,
            UNIQUE(guild_id, user_id)
        )
    """)
    
    # Level roles table (role rewards at certain levels)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS level_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            UNIQUE(guild_id, level)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_xp_guild_user 
        ON user_xp(guild_id, user_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_xp_guild_xp 
        ON user_xp(guild_id, xp DESC)
    """)
    
    conn.commit()
    conn.close()


# =============================
# XP Configuration
# =============================

class LevelingConfig:
    """Configuration for leveling system."""
    
    # XP rewards
    MIN_XP_PER_MESSAGE = 15
    MAX_XP_PER_MESSAGE = 25
    XP_COOLDOWN_SECONDS = 60  # Cooldown between XP gains
    
    # Level formula: xp_needed = base * (level ^ exponent)
    XP_BASE = 100
    XP_EXPONENT = 1.5
    
    # Bonus multipliers
    VOICE_XP_PER_MINUTE = 5
    STREAK_BONUS_MULTIPLIER = 1.5  # If active multiple days in a row
    
    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate total XP needed to reach a level."""
        return int(LevelingConfig.XP_BASE * (level ** LevelingConfig.XP_EXPONENT))
    
    @staticmethod
    def level_from_xp(xp: int) -> int:
        """Calculate level from total XP."""
        level = 0
        while xp >= LevelingConfig.xp_for_level(level + 1):
            level += 1
        return level


# =============================
# XP Management
# =============================

async def add_xp(
    guild_id: int,
    user_id: int,
    amount: Optional[int] = None
) -> Tuple[int, int, bool]:
    """
    Add XP to a user.
    
    Args:
        guild_id: The guild ID
        user_id: The user ID
        amount: XP amount (random if None)
    
    Returns:
        Tuple of (new_xp, new_level, leveled_up)
    """
    if amount is None:
        amount = random.randint(
            LevelingConfig.MIN_XP_PER_MESSAGE,
            LevelingConfig.MAX_XP_PER_MESSAGE
        )
    
    conn = database_connect()
    cursor = conn.cursor()
    
    # Get current XP
    cursor.execute("""
        SELECT xp, level FROM user_xp
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    
    result = cursor.fetchone()
    if result:
        current_xp, current_level = result
    else:
        current_xp, current_level = 0, 0
    
    # Add XP
    new_xp = current_xp + amount
    new_level = LevelingConfig.level_from_xp(new_xp)
    leveled_up = new_level > current_level
    
    # Update database
    cursor.execute("""
        INSERT INTO user_xp (guild_id, user_id, xp, level, last_message_time, total_messages)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            xp = ?,
            level = ?,
            last_message_time = ?,
            total_messages = total_messages + 1
    """, (guild_id, user_id, new_xp, new_level, dt.datetime.now(dt.timezone.utc).isoformat(),
          new_xp, new_level, dt.datetime.now(dt.timezone.utc).isoformat()))
    
    conn.commit()
    conn.close()
    
    return new_xp, new_level, leveled_up


async def can_gain_xp(guild_id: int, user_id: int) -> bool:
    """Check if user can gain XP (not on cooldown)."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT last_message_time FROM user_xp
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        return True
    
    last_time = dt.datetime.fromisoformat(result[0])
    now = dt.datetime.now(dt.timezone.utc)
    return (now - last_time).total_seconds() >= LevelingConfig.XP_COOLDOWN_SECONDS


async def get_user_stats(guild_id: int, user_id: int) -> Optional[Dict]:
    """Get user's leveling stats."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT xp, level, total_messages FROM user_xp
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    xp, level, messages = result
    current_level_xp = LevelingConfig.xp_for_level(level)
    next_level_xp = LevelingConfig.xp_for_level(level + 1)
    xp_progress = xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp
    
    return {
        "xp": xp,
        "level": level,
        "messages": messages,
        "xp_progress": xp_progress,
        "xp_needed": xp_needed,
        "progress_percent": (xp_progress / xp_needed * 100) if xp_needed > 0 else 0
    }


async def get_leaderboard(guild_id: int, limit: int = 10) -> List[Tuple[int, int, int]]:
    """
    Get XP leaderboard for a guild.
    
    Returns:
        List of (user_id, xp, level) tuples
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, xp, level FROM user_xp
        WHERE guild_id = ?
        ORDER BY xp DESC
        LIMIT ?
    """, (guild_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows


async def get_user_rank(guild_id: int, user_id: int) -> Optional[int]:
    """Get user's rank in the guild."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) + 1 FROM user_xp
        WHERE guild_id = ? AND xp > (
            SELECT xp FROM user_xp WHERE guild_id = ? AND user_id = ?
        )
    """, (guild_id, guild_id, user_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None


# =============================
# Level Roles
# =============================

async def set_level_role(guild_id: int, level: int, role_id: int) -> None:
    """Set a role reward for reaching a level."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO level_roles (guild_id, level, role_id)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, level) DO UPDATE SET role_id = ?
    """, (guild_id, level, role_id, role_id))
    
    conn.commit()
    conn.close()


async def remove_level_role(guild_id: int, level: int) -> bool:
    """Remove a level role reward."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM level_roles
        WHERE guild_id = ? AND level = ?
    """, (guild_id, level))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success


async def get_level_roles(guild_id: int) -> List[Tuple[int, int]]:
    """Get all level role rewards for a guild."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT level, role_id FROM level_roles
        WHERE guild_id = ?
        ORDER BY level ASC
    """, (guild_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows


async def assign_level_roles(member: discord.Member, level: int) -> List[discord.Role]:
    """Assign all role rewards the user has earned."""
    level_roles = await get_level_roles(member.guild.id)
    assigned = []
    
    for req_level, role_id in level_roles:
        if level >= req_level:
            role = member.guild.get_role(role_id)
            if role and role not in member.roles:
                await member.add_roles(role, reason=f"Level {req_level} reward")
                assigned.append(role)
    
    return assigned


# =============================
# Embeds and Formatting
# =============================

async def create_level_up_embed(member: discord.Member, level: int) -> discord.Embed:
    """Create a level up announcement embed."""
    embed = discord.Embed(
        title="🎉 Level Up!",
        description=f"{member.mention} just reached **Level {level}**!",
        color=discord.Color.gold()
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    # Check for role rewards
    level_roles = await get_level_roles(member.guild.id)
    for req_level, role_id in level_roles:
        if req_level == level:
            role = member.guild.get_role(role_id)
            if role:
                embed.add_field(
                    name="🎁 Role Reward",
                    value=f"You earned the {role.mention} role!",
                    inline=False
                )
                break
    
    return embed


async def create_rank_card_embed(member: discord.Member, stats: Dict, rank: Optional[int]) -> discord.Embed:
    """Create a rank card embed."""
    level = stats["level"]
    xp = stats["xp"]
    messages = stats["messages"]
    progress = stats["progress_percent"]
    
    embed = discord.Embed(
        title=f"📊 Rank Card - {member.display_name}",
        color=discord.Color.blue()
    )
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    embed.add_field(name="Level", value=f"**{level}**", inline=True)
    embed.add_field(name="Total XP", value=f"**{xp:,}**", inline=True)
    embed.add_field(name="Rank", value=f"**#{rank}**" if rank else "Unranked", inline=True)
    
    embed.add_field(name="Messages", value=f"{messages:,}", inline=True)
    embed.add_field(
        name="Progress to Next Level",
        value=f"{stats['xp_progress']}/{stats['xp_needed']} XP ({progress:.1f}%)",
        inline=False
    )
    
    # Progress bar
    bar_length = 20
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    embed.add_field(name="Progress", value=f"`{bar}`", inline=False)
    
    return embed


async def create_leaderboard_embed(guild: discord.Guild, leaderboard: List[Tuple[int, int, int]]) -> discord.Embed:
    """Create a leaderboard embed."""
    embed = discord.Embed(
        title=f"🏆 {guild.name} - XP Leaderboard",
        color=discord.Color.gold(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    if not leaderboard:
        embed.description = "No users have earned XP yet!"
        return embed
    
    description = ""
    for i, (user_id, xp, level) in enumerate(leaderboard, 1):
        member = guild.get_member(user_id)
        if member:
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            description += f"{medal} {member.mention} - Level **{level}** ({xp:,} XP)\n"
        else:
            description += f"**{i}.** User {user_id} - Level **{level}** ({xp:,} XP)\n"
    
    embed.description = description
    
    return embed


# =============================
# Message Handler
# =============================

async def process_message_for_xp(message: discord.Message) -> Optional[Tuple[int, bool]]:
    """
    Process a message for XP gain.
    
    Returns:
        Tuple of (new_level, leveled_up) or None if no XP gained
    """
    if not message.guild or not message.author or message.author.bot:
        return None
    
    # Check if user can gain XP
    if not await can_gain_xp(message.guild.id, message.author.id):
        return None
    
    # Add XP
    _, new_level, leveled_up = await add_xp(message.guild.id, message.author.id)
    
    if leveled_up and isinstance(message.author, discord.Member):
        # Assign role rewards
        await assign_level_roles(message.author, new_level)
    
    return new_level, leveled_up


# Initialize database on module load
init_leveling_database()
