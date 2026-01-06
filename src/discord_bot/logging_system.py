"""
Message and event logging system for Discord servers.
Tracks message edits, deletions, and other important events.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Optional, List, Dict

import discord

from .storage_api import database_connect, DATA_DIR


# =============================
# Database Setup
# =============================

def init_logging_database() -> None:
    """Initialize the logging database tables."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # Message log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT,
            event_type TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            edited_content TEXT,
            attachments TEXT
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_message_id 
        ON message_logs(message_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_guild_channel 
        ON message_logs(guild_id, channel_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_author 
        ON message_logs(author_id)
    """)
    
    conn.commit()
    conn.close()


# =============================
# Message Logging
# =============================

async def log_message_delete(
    message: discord.Message,
    deleted_by: Optional[discord.Member] = None
) -> None:
    """
    Log a deleted message.
    
    Args:
        message: The deleted message
        deleted_by: The member who deleted the message (if known)
    """
    if not message.guild:
        return
    
    # Prepare attachment info
    attachments = ""
    if message.attachments:
        attachment_names = [att.filename for att in message.attachments]
        attachments = ", ".join(attachment_names)
    
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO message_logs 
        (message_id, channel_id, guild_id, author_id, author_name, content, event_type, attachments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        message.id,
        message.channel.id,
        message.guild.id,
        message.author.id,
        str(message.author),
        message.content,
        "delete",
        attachments
    ))
    
    conn.commit()
    conn.close()


async def log_message_edit(
    before: discord.Message,
    after: discord.Message
) -> None:
    """
    Log an edited message.
    
    Args:
        before: The message before editing
        after: The message after editing
    """
    if not before.guild:
        return
    
    # Only log if content actually changed
    if before.content == after.content:
        return
    
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO message_logs 
        (message_id, channel_id, guild_id, author_id, author_name, content, event_type, edited_content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        before.id,
        before.channel.id,
        before.guild.id,
        before.author.id,
        str(before.author),
        before.content,
        "edit",
        after.content
    ))
    
    conn.commit()
    conn.close()


async def log_bulk_delete(
    messages: List[discord.Message],
    channel: discord.TextChannel
) -> None:
    """
    Log bulk deleted messages.
    
    Args:
        messages: List of deleted messages
        channel: The channel where messages were deleted
    """
    if not channel.guild:
        return
    
    conn = database_connect()
    cursor = conn.cursor()
    
    for message in messages:
        attachments = ""
        if message.attachments:
            attachment_names = [att.filename for att in message.attachments]
            attachments = ", ".join(attachment_names)
        
        cursor.execute("""
            INSERT INTO message_logs 
            (message_id, channel_id, guild_id, author_id, author_name, content, event_type, attachments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message.id,
            channel.id,
            channel.guild.id,
            message.author.id,
            str(message.author),
            message.content,
            "bulk_delete",
            attachments
        ))
    
    conn.commit()
    conn.close()


# =============================
# Log Retrieval
# =============================

async def get_user_message_history(
    user_id: int,
    guild_id: int,
    limit: int = 50
) -> List[Dict]:
    """
    Get message history for a specific user.
    
    Args:
        user_id: The user ID
        guild_id: The guild ID
        limit: Maximum number of messages to retrieve
    
    Returns:
        List of message log dictionaries
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM message_logs
        WHERE author_id = ? AND guild_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, guild_id, limit))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


async def get_channel_message_history(
    channel_id: int,
    limit: int = 50
) -> List[Dict]:
    """
    Get message history for a specific channel.
    
    Args:
        channel_id: The channel ID
        limit: Maximum number of messages to retrieve
    
    Returns:
        List of message log dictionaries
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM message_logs
        WHERE channel_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (channel_id, limit))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


async def get_deleted_messages(
    guild_id: int,
    limit: int = 50,
    user_id: Optional[int] = None
) -> List[Dict]:
    """
    Get deleted messages.
    
    Args:
        guild_id: The guild ID
        limit: Maximum number of messages to retrieve
        user_id: Optional user ID to filter by
    
    Returns:
        List of deleted message log dictionaries
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT * FROM message_logs
            WHERE guild_id = ? AND event_type IN ('delete', 'bulk_delete') AND author_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (guild_id, user_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM message_logs
            WHERE guild_id = ? AND event_type IN ('delete', 'bulk_delete')
            ORDER BY timestamp DESC
            LIMIT ?
        """, (guild_id, limit))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


async def get_edited_messages(
    guild_id: int,
    limit: int = 50,
    user_id: Optional[int] = None
) -> List[Dict]:
    """
    Get edited messages.
    
    Args:
        guild_id: The guild ID
        limit: Maximum number of messages to retrieve
        user_id: Optional user ID to filter by
    
    Returns:
        List of edited message log dictionaries
    """
    conn = database_connect()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT * FROM message_logs
            WHERE guild_id = ? AND event_type = 'edit' AND author_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (guild_id, user_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM message_logs
            WHERE guild_id = ? AND event_type = 'edit'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (guild_id, limit))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


# =============================
# Log Formatting
# =============================

async def format_message_log_embed(
    logs: List[Dict],
    title: str = "Message Logs"
) -> discord.Embed:
    """
    Format message logs into an embed.
    
    Args:
        logs: List of log dictionaries
        title: Embed title
    
    Returns:
        Formatted embed
    """
    embed = discord.Embed(
        title=title,
        color=discord.Color.blue(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    if not logs:
        embed.description = "No logs found."
        return embed
    
    for log in logs[:10]:  # Limit to 10 to avoid embed size limits
        event_type = log.get("event_type", "unknown")
        author_name = log.get("author_name", "Unknown")
        content = log.get("content", "")
        edited_content = log.get("edited_content", "")
        timestamp = log.get("timestamp", "")
        attachments = log.get("attachments", "")
        
        # Truncate content if too long
        if len(content) > 200:
            content = content[:200] + "..."
        
        if len(edited_content) > 200:
            edited_content = edited_content[:200] + "..."
        
        field_value = f"**User:** {author_name}\n"
        
        if event_type == "delete" or event_type == "bulk_delete":
            field_value += f"**Content:** {content or '(no content)'}\n"
            if attachments:
                field_value += f"**Attachments:** {attachments}\n"
        elif event_type == "edit":
            field_value += f"**Before:** {content or '(no content)'}\n"
            field_value += f"**After:** {edited_content or '(no content)'}\n"
        
        field_value += f"**Time:** {timestamp}"
        
        embed.add_field(
            name=f"{event_type.title()} - Message {log.get('message_id', 'Unknown')}",
            value=field_value,
            inline=False
        )
    
    return embed


# =============================
# Log Channel System
# =============================

# Storage for log channels: guild_id -> channel_id
_log_channels: Dict[int, int] = {}


def set_log_channel(guild_id: int, channel_id: int) -> None:
    """
    Set the log channel for a guild.
    
    Args:
        guild_id: The guild ID
        channel_id: The log channel ID
    """
    _log_channels[guild_id] = channel_id


def get_log_channel(guild_id: int) -> Optional[int]:
    """
    Get the log channel for a guild.
    
    Args:
        guild_id: The guild ID
    
    Returns:
        Channel ID or None
    """
    return _log_channels.get(guild_id)


async def send_to_log_channel(
    guild: discord.Guild,
    embed: discord.Embed
) -> bool:
    """
    Send an embed to the configured log channel.
    
    Args:
        guild: The guild
        embed: The embed to send
    
    Returns:
        True if sent successfully, False otherwise
    """
    channel_id = get_log_channel(guild.id)
    if not channel_id:
        return False
    
    channel = guild.get_channel(channel_id)
    if not channel or not isinstance(channel, discord.TextChannel):
        return False
    
    try:
        await channel.send(embed=embed)
        return True
    except Exception:
        return False


async def create_delete_log_embed(message: discord.Message) -> discord.Embed:
    """Create an embed for a deleted message."""
    embed = discord.Embed(
        title="🗑️ Message Deleted",
        color=discord.Color.red(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    embed.add_field(name="Author", value=message.author.mention, inline=True)
    
    channel_mention = message.channel.mention if isinstance(message.channel, discord.TextChannel) else str(message.channel)
    embed.add_field(name="Channel", value=channel_mention, inline=True)
    embed.add_field(name="Message ID", value=str(message.id), inline=True)
    
    content = message.content or "(no content)"
    if len(content) > 1024:
        content = content[:1021] + "..."
    embed.add_field(name="Content", value=content, inline=False)
    
    if message.attachments:
        attachment_info = "\n".join([f"• {att.filename}" for att in message.attachments])
        embed.add_field(name="Attachments", value=attachment_info, inline=False)
    
    if message.author.avatar:
        embed.set_thumbnail(url=message.author.avatar.url)
    
    return embed


async def create_edit_log_embed(before: discord.Message, after: discord.Message) -> discord.Embed:
    """Create an embed for an edited message."""
    embed = discord.Embed(
        title="✏️ Message Edited",
        color=discord.Color.orange(),
        timestamp=dt.datetime.now(dt.timezone.utc)
    )
    
    embed.add_field(name="Author", value=before.author.mention, inline=True)
    
    channel_mention = before.channel.mention if isinstance(before.channel, discord.TextChannel) else str(before.channel)
    embed.add_field(name="Channel", value=channel_mention, inline=True)
    embed.add_field(name="Message ID", value=str(before.id), inline=True)
    
    before_content = before.content or "(no content)"
    if len(before_content) > 1024:
        before_content = before_content[:1021] + "..."
    embed.add_field(name="Before", value=before_content, inline=False)
    
    after_content = after.content or "(no content)"
    if len(after_content) > 1024:
        after_content = after_content[:1021] + "..."
    embed.add_field(name="After", value=after_content, inline=False)
    
    embed.add_field(
        name="Jump to Message",
        value=f"[Click here]({after.jump_url})",
        inline=False
    )
    
    if before.author.avatar:
        embed.set_thumbnail(url=before.author.avatar.url)
    
    return embed


# Initialize database on module load
init_logging_database()
