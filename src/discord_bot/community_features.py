"""
Community engagement features: reputation, giveaways, events, confessions, server stats.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import random
from typing import Optional, List, Dict, Tuple
from zoneinfo import ZoneInfo

import discord

from .storage_api import database_connect


# =============================
# Database Setup
# =============================

def init_community_database() -> None:
    """Initialize community features database tables."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # Reputation system
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reputation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            karma INTEGER DEFAULT 0,
            given_today INTEGER DEFAULT 0,
            last_reset_date TEXT,
            UNIQUE(guild_id, user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reputation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Giveaways
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            prize TEXT NOT NULL,
            winner_count INTEGER DEFAULT 1,
            end_time TIMESTAMP NOT NULL,
            host_id INTEGER NOT NULL,
            ended BOOLEAN DEFAULT 0,
            winner_ids TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giveaway_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(giveaway_id, user_id),
            FOREIGN KEY(giveaway_id) REFERENCES giveaways(id)
        )
    """)
    
    # Events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            timezone TEXT DEFAULT 'UTC',
            host_id INTEGER NOT NULL,
            channel_id INTEGER,
            max_attendees INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(event_id, user_id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)
    
    # Confessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            confession_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guild_id, confession_number)
        )
    """)
    
    # Server stats tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_members INTEGER DEFAULT 0,
            messages_sent INTEGER DEFAULT 0,
            members_joined INTEGER DEFAULT 0,
            members_left INTEGER DEFAULT 0,
            UNIQUE(guild_id, date)
        )
    """)
    
    conn.commit()
    conn.close()


# =============================
# Reputation / Karma System
# =============================

async def give_karma(
    guild_id: int,
    from_user_id: int,
    to_user_id: int,
    amount: int = 1,
    reason: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Give karma to another user.
    
    Returns:
        Tuple of (success, message)
    """
    if from_user_id == to_user_id:
        return False, "You cannot give karma to yourself!"
    
    conn = database_connect()
    cursor = conn.cursor()
    
    # Check daily limit
    today = dt.date.today().isoformat()
    cursor.execute("""
        SELECT given_today, last_reset_date FROM reputation
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, from_user_id))
    
    result = cursor.fetchone()
    given_today = 0
    
    if result:
        given_today, last_reset = result
        if last_reset != today:
            # Reset daily counter
            given_today = 0
            cursor.execute("""
                UPDATE reputation
                SET given_today = 0, last_reset_date = ?
                WHERE guild_id = ? AND user_id = ?
            """, (today, guild_id, from_user_id))
    
    # Check limit (default 3 per day)
    if given_today >= 3:
        return False, "You've reached your daily karma limit! (3/day)"
    
    # Add karma to recipient
    cursor.execute("""
        INSERT INTO reputation (guild_id, user_id, karma)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET karma = karma + ?
    """, (guild_id, to_user_id, amount, amount))
    
    # Update giver's daily count
    cursor.execute("""
        INSERT INTO reputation (guild_id, user_id, given_today, last_reset_date)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            given_today = given_today + 1,
            last_reset_date = ?
    """, (guild_id, from_user_id, today, today))
    
    # Log the transaction
    cursor.execute("""
        INSERT INTO reputation_log (guild_id, from_user_id, to_user_id, amount, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (guild_id, from_user_id, to_user_id, amount, reason))
    
    conn.commit()
    conn.close()
    
    return True, f"Gave {amount} karma! ({given_today + 1}/3 today)"


async def get_karma(guild_id: int, user_id: int) -> int:
    """Get user's karma score."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT karma FROM reputation
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 0


async def get_karma_leaderboard(guild_id: int, limit: int = 10) -> List[Tuple[int, int]]:
    """Get karma leaderboard."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, karma FROM reputation
        WHERE guild_id = ?
        ORDER BY karma DESC
        LIMIT ?
    """, (guild_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows


# =============================
# Giveaway System
# =============================

async def create_giveaway(
    guild_id: int,
    channel_id: int,
    prize: str,
    duration_seconds: int,
    host_id: int,
    winner_count: int = 1
) -> int:
    """Create a new giveaway."""
    conn = database_connect()
    cursor = conn.cursor()
    
    end_time = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=duration_seconds)
    
    cursor.execute("""
        INSERT INTO giveaways (guild_id, channel_id, prize, winner_count, end_time, host_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (guild_id, channel_id, prize, winner_count, end_time.isoformat(), host_id))
    
    giveaway_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    assert giveaway_id is not None, "Failed to create giveaway: lastrowid is None"
    return giveaway_id


async def enter_giveaway(giveaway_id: int, user_id: int) -> Tuple[bool, str]:
    """Enter a user into a giveaway."""
    conn = database_connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO giveaway_entries (giveaway_id, user_id)
            VALUES (?, ?)
        """, (giveaway_id, user_id))
        conn.commit()
        return True, "You're entered in the giveaway!"
    except Exception:
        return False, "You're already entered!"
    finally:
        conn.close()


async def get_giveaway_entries(giveaway_id: int) -> List[int]:
    """Get all user IDs entered in a giveaway."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id FROM giveaway_entries
        WHERE giveaway_id = ?
    """, (giveaway_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


async def end_giveaway(giveaway_id: int) -> Optional[Dict]:
    """End a giveaway and select winners."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # Get giveaway info
    cursor.execute("""
        SELECT prize, winner_count, ended FROM giveaways
        WHERE id = ?
    """, (giveaway_id,))
    
    result = cursor.fetchone()
    if not result or result[2]:  # Already ended
        conn.close()
        return None
    
    prize, winner_count, _ = result
    
    # Get entries
    entries = await get_giveaway_entries(giveaway_id)
    if not entries:
        cursor.execute("""
            UPDATE giveaways SET ended = 1 WHERE id = ?
        """, (giveaway_id,))
        conn.commit()
        conn.close()
        return {"prize": prize, "winners": []}
    
    # Select winners
    winners = random.sample(entries, min(winner_count, len(entries)))
    
    # Update giveaway
    cursor.execute("""
        UPDATE giveaways
        SET ended = 1, winner_ids = ?
        WHERE id = ?
    """, (",".join(map(str, winners)), giveaway_id))
    
    conn.commit()
    conn.close()
    
    return {"prize": prize, "winners": winners, "total_entries": len(entries)}


async def create_giveaway_embed(prize: str, end_time: dt.datetime, host: discord.Member, entries: int = 0) -> discord.Embed:
    """Create giveaway announcement embed."""
    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=f"**Prize:** {prize}",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Hosted by", value=host.mention, inline=True)
    embed.add_field(name="Entries", value=str(entries), inline=True)
    embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=False)
    embed.set_footer(text="React with 🎉 to enter!")
    
    return embed


# =============================
# Event Scheduling
# =============================

async def create_event(
    guild_id: int,
    title: str,
    start_time: dt.datetime,
    host_id: int,
    description: Optional[str] = None,
    end_time: Optional[dt.datetime] = None,
    timezone: str = "UTC",
    channel_id: Optional[int] = None,
    max_attendees: Optional[int] = None
) -> int:
    """Create a scheduled event."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO events (guild_id, title, description, start_time, end_time, timezone, host_id, channel_id, max_attendees)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (guild_id, title, description, start_time.isoformat(), 
          end_time.isoformat() if end_time else None, timezone, host_id, channel_id, max_attendees))
    
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    assert event_id is not None, "Failed to create event: lastrowid is None"
    return event_id


async def rsvp_event(event_id: int, user_id: int) -> Tuple[bool, str]:
    """RSVP to an event."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # Check max attendees
    cursor.execute("""
        SELECT max_attendees FROM events WHERE id = ?
    """, (event_id,))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False, "Event not found!"
    
    max_attendees = result[0]
    
    if max_attendees:
        cursor.execute("""
            SELECT COUNT(*) FROM event_attendees WHERE event_id = ?
        """, (event_id,))
        result = cursor.fetchone()
        current = result[0] if result else 0
        
        if current >= max_attendees:
            conn.close()
            return False, "Event is full!"
    
    try:
        cursor.execute("""
            INSERT INTO event_attendees (event_id, user_id)
            VALUES (?, ?)
        """, (event_id, user_id))
        conn.commit()
        return True, "✅ RSVP confirmed!"
    except Exception:
        return False, "You're already registered!"
    finally:
        conn.close()


async def get_event_attendees(event_id: int) -> List[int]:
    """Get all user IDs attending an event."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id FROM event_attendees WHERE event_id = ?
    """, (event_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


async def create_event_embed(
    title: str,
    start_time: dt.datetime,
    host: discord.Member,
    description: Optional[str] = None,
    end_time: Optional[dt.datetime] = None,
    attendees: int = 0,
    max_attendees: Optional[int] = None
) -> discord.Embed:
    """Create event announcement embed."""
    embed = discord.Embed(
        title=f"📅 {title}",
        description=description or "Join us for this event!",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Host", value=host.mention, inline=True)
    embed.add_field(name="Start Time", value=f"<t:{int(start_time.timestamp())}:F>", inline=False)
    
    if end_time:
        embed.add_field(name="End Time", value=f"<t:{int(end_time.timestamp())}:F>", inline=False)
    
    attendee_text = f"{attendees}"
    if max_attendees:
        attendee_text += f"/{max_attendees}"
    embed.add_field(name="Attendees", value=attendee_text, inline=True)
    
    embed.set_footer(text="React with ✅ to RSVP!")
    
    return embed


# =============================
# Anonymous Confessions
# =============================

async def submit_confession(guild_id: int, user_id: int, content: str) -> int:
    """Submit an anonymous confession."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # Get next confession number for guild
    cursor.execute("""
        SELECT MAX(confession_number) FROM confessions WHERE guild_id = ?
    """, (guild_id,))
    
    result = cursor.fetchone()
    next_number = (result[0] if result and result[0] else 0) + 1
    
    cursor.execute("""
        INSERT INTO confessions (guild_id, confession_number, content, user_id)
        VALUES (?, ?, ?, ?)
    """, (guild_id, next_number, content, user_id))
    
    conn.commit()
    conn.close()
    
    return next_number


async def create_confession_embed(confession_number: int, content: str) -> discord.Embed:
    """Create confession embed."""
    embed = discord.Embed(
        title=f"🤫 Anonymous Confession #{confession_number}",
        description=content,
        color=discord.Color.purple(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    embed.set_footer(text="All confessions are anonymous")
    
    return embed


# =============================
# Server Stats Dashboard
# =============================

async def update_server_stats(
    guild_id: int,
    members_joined: int = 0,
    members_left: int = 0,
    messages_sent: int = 0
) -> None:
    """Update daily server statistics."""
    conn = database_connect()
    cursor = conn.cursor()
    
    today = dt.date.today().isoformat()
    
    cursor.execute("""
        INSERT INTO server_stats (guild_id, date, members_joined, members_left, messages_sent)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, date) DO UPDATE SET
            members_joined = members_joined + ?,
            members_left = members_left + ?,
            messages_sent = messages_sent + ?
    """, (guild_id, today, members_joined, members_left, messages_sent,
          members_joined, members_left, messages_sent))
    
    conn.commit()
    conn.close()


async def get_server_stats(guild_id: int, days: int = 7) -> List[Dict]:
    """Get server stats for the past N days."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, total_members, messages_sent, members_joined, members_left
        FROM server_stats
        WHERE guild_id = ?
        ORDER BY date DESC
        LIMIT ?
    """, (guild_id, days))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "date": row[0],
            "total_members": row[1],
            "messages_sent": row[2],
            "members_joined": row[3],
            "members_left": row[4]
        }
        for row in rows
    ]


async def create_stats_embed(guild: discord.Guild, stats: List[Dict]) -> discord.Embed:
    """Create server stats dashboard embed."""
    embed = discord.Embed(
        title=f"📊 {guild.name} - Server Statistics",
        color=discord.Color.blue(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    # Current stats
    embed.add_field(name="Total Members", value=f"{guild.member_count:,}", inline=True)
    embed.add_field(name="Channels", value=f"{len(guild.channels)}", inline=True)
    embed.add_field(name="Roles", value=f"{len(guild.roles)}", inline=True)
    
    # Recent activity
    if stats:
        recent = stats[0]
        embed.add_field(
            name="📨 Messages (Today)",
            value=f"{recent['messages_sent']:,}",
            inline=True
        )
        embed.add_field(
            name="➕ Joined (Today)",
            value=f"{recent['members_joined']}",
            inline=True
        )
        embed.add_field(
            name="➖ Left (Today)",
            value=f"{recent['members_left']}",
            inline=True
        )
        
        # Weekly totals
        total_messages = sum(s['messages_sent'] for s in stats)
        total_joined = sum(s['members_joined'] for s in stats)
        total_left = sum(s['members_left'] for s in stats)
        
        embed.add_field(
            name=f"📈 Past {len(stats)} Days",
            value=f"**Messages:** {total_messages:,}\n**Joined:** {total_joined}\n**Left:** {total_left}",
            inline=False
        )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(text=f"Server created")
    embed.timestamp = guild.created_at
    
    return embed


# Initialize database on module load
init_community_database()
