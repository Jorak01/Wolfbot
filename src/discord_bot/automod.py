"""
Auto-moderation system for Discord servers.
Includes spam detection, caps lock detection, link filtering, raid protection, and auto-slowmode.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections import defaultdict
from typing import Optional, Dict, List, Tuple

import discord


# =============================
# Configuration
# =============================

class AutoModConfig:
    """Configuration for auto-moderation features."""
    
    # Spam detection
    MAX_MESSAGES_PER_WINDOW = 5
    SPAM_WINDOW_SECONDS = 5
    SPAM_ACTION = "timeout"  # "timeout", "kick", "ban", "warn"
    SPAM_TIMEOUT_DURATION = 300  # 5 minutes
    
    # Caps lock detection
    MAX_CAPS_PERCENTAGE = 70  # % of uppercase characters
    MIN_MESSAGE_LENGTH_FOR_CAPS = 10
    
    # Link filtering
    BLOCK_INVITES = True
    BLOCK_LINKS = False
    ALLOWED_DOMAINS: List[str] = []  # Whitelist domains
    
    # Raid protection
    MAX_JOINS_PER_MINUTE = 10
    RAID_DETECTION_WINDOW = 60  # seconds
    AUTO_LOCKDOWN_ON_RAID = True
    
    # Auto-slowmode
    AUTO_SLOWMODE_ENABLED = True
    SLOWMODE_THRESHOLD = 10  # messages per minute to trigger slowmode
    SLOWMODE_DURATION = 10  # seconds
    SLOWMODE_RESET_DELAY = 300  # seconds before resetting slowmode


# =============================
# Tracking Data
# =============================

# User message tracking: user_id -> [(timestamp, channel_id)]
_message_tracker: Dict[int, List[Tuple[float, int]]] = defaultdict(list)

# Channel message rate tracking: channel_id -> [(timestamp)]
_channel_activity: Dict[int, List[float]] = defaultdict(list)

# Join tracking: guild_id -> [timestamps]
_join_tracker: Dict[int, List[float]] = defaultdict(list)

# Raid mode: guild_id -> is_in_raid
_raid_mode: Dict[int, bool] = {}


# =============================
# Spam Detection
# =============================

async def check_spam(message: discord.Message, config: Optional[AutoModConfig] = None) -> Tuple[bool, str]:
    """
    Check if a message is spam.
    
    Args:
        message: The message to check
        config: Auto-mod configuration
    
    Returns:
        Tuple of (is_spam, reason)
    """
    if not config:
        config = AutoModConfig()
    
    if not message.author or message.author.bot:
        return False, ""
    
    if not isinstance(message.author, discord.Member):
        return False, ""
    
    # Check if user has mod permissions (exempt from spam detection)
    if message.author.guild_permissions.manage_messages:
        return False, ""
    
    user_id = message.author.id
    channel_id = message.channel.id
    current_time = time.time()
    
    # Clean up old messages
    _message_tracker[user_id] = [
        (ts, ch_id) for ts, ch_id in _message_tracker[user_id]
        if current_time - ts < config.SPAM_WINDOW_SECONDS
    ]
    
    # Add current message
    _message_tracker[user_id].append((current_time, channel_id))
    
    # Count recent messages in the same channel
    recent_messages = sum(
        1 for ts, ch_id in _message_tracker[user_id]
        if ch_id == channel_id
    )
    
    if recent_messages > config.MAX_MESSAGES_PER_WINDOW:
        return True, f"Spam detected: {recent_messages} messages in {config.SPAM_WINDOW_SECONDS}s"
    
    return False, ""


async def handle_spam(
    message: discord.Message,
    reason: str,
    config: Optional[AutoModConfig] = None
) -> Optional[str]:
    """
    Handle spam detection by taking action.
    
    Args:
        message: The spam message
        reason: The reason for spam detection
        config: Auto-mod configuration
    
    Returns:
        Action taken message
    """
    if not config:
        config = AutoModConfig()
    
    if not isinstance(message.author, discord.Member):
        return None
    
    # Delete the message
    try:
        await message.delete()
    except discord.HTTPException:
        pass
    
    # Take action based on config
    action_taken = ""
    if config.SPAM_ACTION == "timeout":
        try:
            from . import moderation
            await moderation.timeout_user(
                message.author,
                config.SPAM_TIMEOUT_DURATION,
                reason=reason
            )
            action_taken = f"Timed out {message.author.mention} for spam"
        except Exception as e:
            action_taken = f"Failed to timeout: {e}"
    
    elif config.SPAM_ACTION == "kick":
        try:
            from . import moderation
            await moderation.kick_user(message.author, reason=reason)
            action_taken = f"Kicked {message.author.mention} for spam"
        except Exception as e:
            action_taken = f"Failed to kick: {e}"
    
    elif config.SPAM_ACTION == "ban":
        try:
            from . import moderation
            await moderation.ban_user(message.author, reason=reason)
            action_taken = f"Banned {message.author.mention} for spam"
        except Exception as e:
            action_taken = f"Failed to ban: {e}"
    
    elif config.SPAM_ACTION == "warn":
        try:
            from . import moderation
            await moderation.warn_user(message.author, reason)
            action_taken = f"Warned {message.author.mention} for spam"
        except Exception as e:
            action_taken = f"Failed to warn: {e}"
    
    return action_taken


# =============================
# Caps Lock Detection
# =============================

def check_excessive_caps(content: str, config: Optional[AutoModConfig] = None) -> Tuple[bool, str]:
    """
    Check if message has excessive caps lock.
    
    Args:
        content: Message content
        config: Auto-mod configuration
    
    Returns:
        Tuple of (has_excessive_caps, reason)
    """
    if not config:
        config = AutoModConfig()
    
    # Remove spaces and special characters for accurate counting
    letters_only = re.sub(r'[^a-zA-Z]', '', content)
    
    if len(letters_only) < config.MIN_MESSAGE_LENGTH_FOR_CAPS:
        return False, ""
    
    uppercase_count = sum(1 for c in letters_only if c.isupper())
    caps_percentage = (uppercase_count / len(letters_only)) * 100
    
    if caps_percentage > config.MAX_CAPS_PERCENTAGE:
        return True, f"Excessive caps: {caps_percentage:.1f}% uppercase"
    
    return False, ""


# =============================
# Link Filtering
# =============================

# Regular expressions for detecting links
INVITE_REGEX = re.compile(
    r'(?:https?://)?(?:www\.)?'
    r'(?:discord\.gg|discordapp\.com/invite|discord\.com/invite)/'
    r'[a-zA-Z0-9]+',
    re.IGNORECASE
)

URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    re.IGNORECASE
)


def check_links(content: str, config: Optional[AutoModConfig] = None) -> Tuple[bool, str]:
    """
    Check if message contains blocked links.
    
    Args:
        content: Message content
        config: Auto-mod configuration
    
    Returns:
        Tuple of (has_blocked_links, reason)
    """
    if not config:
        config = AutoModConfig()
    
    # Check for Discord invites
    if config.BLOCK_INVITES:
        if INVITE_REGEX.search(content):
            return True, "Discord invite link detected"
    
    # Check for other links
    if config.BLOCK_LINKS:
        urls = URL_REGEX.findall(content)
        for url in urls:
            # Check if domain is whitelisted
            is_allowed = False
            for allowed_domain in config.ALLOWED_DOMAINS:
                if allowed_domain.lower() in url.lower():
                    is_allowed = True
                    break
            
            if not is_allowed:
                return True, "Unauthorized link detected"
    
    return False, ""


# =============================
# Raid Protection
# =============================

async def check_raid(member: discord.Member, config: Optional[AutoModConfig] = None) -> Tuple[bool, str]:
    """
    Check if a member join is part of a raid.
    
    Args:
        member: The member who joined
        config: Auto-mod configuration
    
    Returns:
        Tuple of (is_raid, reason)
    """
    if not config:
        config = AutoModConfig()
    
    guild_id = member.guild.id
    current_time = time.time()
    
    # Clean up old join timestamps
    _join_tracker[guild_id] = [
        ts for ts in _join_tracker[guild_id]
        if current_time - ts < config.RAID_DETECTION_WINDOW
    ]
    
    # Add current join
    _join_tracker[guild_id].append(current_time)
    
    # Count recent joins
    recent_joins = len(_join_tracker[guild_id])
    joins_per_minute = (recent_joins / config.RAID_DETECTION_WINDOW) * 60
    
    if joins_per_minute > config.MAX_JOINS_PER_MINUTE:
        return True, f"Raid detected: {recent_joins} joins in {config.RAID_DETECTION_WINDOW}s"
    
    return False, ""


async def activate_raid_mode(guild: discord.Guild, config: Optional[AutoModConfig] = None) -> str:
    """
    Activate raid mode for a guild.
    
    Args:
        guild: The guild to activate raid mode for
        config: Auto-mod configuration
    
    Returns:
        Status message
    """
    if not config:
        config = AutoModConfig()
    
    _raid_mode[guild.id] = True
    
    actions = []
    
    # Lock all text channels
    if config.AUTO_LOCKDOWN_ON_RAID:
        from . import moderation
        for channel in guild.text_channels:
            try:
                await moderation.lock_channel(channel, reason="Raid protection activated")
                actions.append(f"Locked {channel.name}")
            except Exception as e:
                actions.append(f"Failed to lock {channel.name}: {e}")
    
    return f"🚨 Raid mode activated!\n" + "\n".join(actions)


async def deactivate_raid_mode(guild: discord.Guild, config: Optional[AutoModConfig] = None) -> str:
    """
    Deactivate raid mode for a guild.
    
    Args:
        guild: The guild to deactivate raid mode for
        config: Auto-mod configuration
    
    Returns:
        Status message
    """
    if not config:
        config = AutoModConfig()
    
    _raid_mode[guild.id] = False
    
    actions = []
    
    # Unlock all text channels
    if config.AUTO_LOCKDOWN_ON_RAID:
        from . import moderation
        for channel in guild.text_channels:
            try:
                await moderation.unlock_channel(channel, reason="Raid protection deactivated")
                actions.append(f"Unlocked {channel.name}")
            except Exception as e:
                actions.append(f"Failed to unlock {channel.name}: {e}")
    
    return f"✅ Raid mode deactivated!\n" + "\n".join(actions)


def is_raid_mode(guild_id: int) -> bool:
    """Check if a guild is in raid mode."""
    return _raid_mode.get(guild_id, False)


# =============================
# Auto-Slowmode
# =============================

async def check_auto_slowmode(
    channel: discord.TextChannel,
    config: Optional[AutoModConfig] = None
) -> Optional[int]:
    """
    Check if auto-slowmode should be activated.
    
    Args:
        channel: The channel to check
        config: Auto-mod configuration
    
    Returns:
        Slowmode delay to set, or None if no action needed
    """
    if not config or not config.AUTO_SLOWMODE_ENABLED:
        return None
    
    channel_id = channel.id
    current_time = time.time()
    
    # Clean up old activity
    _channel_activity[channel_id] = [
        ts for ts in _channel_activity[channel_id]
        if current_time - ts < 60  # Track last minute
    ]
    
    # Add current message
    _channel_activity[channel_id].append(current_time)
    
    # Calculate messages per minute
    messages_per_minute = len(_channel_activity[channel_id])
    
    # Activate slowmode if threshold exceeded
    if messages_per_minute > config.SLOWMODE_THRESHOLD:
        if channel.slowmode_delay == 0:
            return config.SLOWMODE_DURATION
    
    # Deactivate slowmode if activity has calmed down
    elif messages_per_minute < config.SLOWMODE_THRESHOLD // 2:
        if channel.slowmode_delay > 0:
            return 0
    
    return None


async def apply_auto_slowmode(
    channel: discord.TextChannel,
    delay: int,
    reason: str = "Auto-slowmode"
) -> str:
    """
    Apply slowmode to a channel.
    
    Args:
        channel: The channel to apply slowmode to
        delay: Slowmode delay in seconds (0 to disable)
        reason: Reason for applying slowmode
    
    Returns:
        Status message
    """
    try:
        await channel.edit(slowmode_delay=delay, reason=reason)
        if delay > 0:
            return f"⏱️ Activated slowmode in {channel.mention}: {delay}s delay"
        else:
            return f"✅ Deactivated slowmode in {channel.mention}"
    except Exception as e:
        return f"Failed to set slowmode in {channel.mention}: {e}"


# =============================
# Alt Account Detection
# =============================

async def detect_alt_account(member: discord.Member) -> Tuple[bool, str]:
    """
    Detect potential alt accounts based on join date and behavior heuristics.
    
    Args:
        member: The member to check
    
    Returns:
        Tuple of (is_likely_alt, reason)
    """
    reasons = []
    
    # Check account age (less than 7 days old)
    account_age = (discord.utils.utcnow() - member.created_at).days
    if account_age < 7:
        reasons.append(f"Account created {account_age} days ago")
    
    # Check if account has default avatar
    if member.avatar is None:
        reasons.append("Using default avatar")
    
    # Check if username looks suspicious (lots of numbers)
    username_numbers = sum(1 for c in member.name if c.isdigit())
    if username_numbers > len(member.name) * 0.5:
        reasons.append("Username contains many numbers")
    
    # Check for similar names in server
    if member.guild:
        similar_names = [
            m for m in member.guild.members
            if m.id != member.id and
            (m.name.lower() in member.name.lower() or member.name.lower() in m.name.lower())
        ]
        if similar_names:
            reasons.append(f"Similar name to {len(similar_names)} existing member(s)")
    
    is_suspicious = len(reasons) >= 2
    reason_text = "; ".join(reasons) if reasons else "No suspicious indicators"
    
    return is_suspicious, reason_text


# =============================
# Combined Auto-Moderation Handler
# =============================

async def process_message(
    message: discord.Message,
    config: Optional[AutoModConfig] = None
) -> Optional[str]:
    """
    Process a message through all auto-moderation checks.
    
    Args:
        message: The message to process
        config: Auto-mod configuration
    
    Returns:
        Action taken message, or None if no action needed
    """
    if not config:
        config = AutoModConfig()
    
    if not message.guild or not message.author or message.author.bot:
        return None
    
    if not isinstance(message.author, discord.Member):
        return None
    
    # Check spam
    is_spam, spam_reason = await check_spam(message, config)
    if is_spam:
        return await handle_spam(message, spam_reason, config)
    
    # Check caps
    has_caps, caps_reason = check_excessive_caps(message.content, config)
    if has_caps:
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} Please don't use excessive caps lock.",
                delete_after=5
            )
            return f"Deleted message from {message.author.mention}: {caps_reason}"
        except Exception:
            pass
    
    # Check links
    has_blocked_links, link_reason = check_links(message.content, config)
    if has_blocked_links:
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} {link_reason}",
                delete_after=5
            )
            return f"Deleted message from {message.author.mention}: {link_reason}"
        except Exception:
            pass
    
    # Check auto-slowmode
    if isinstance(message.channel, discord.TextChannel):
        slowmode_delay = await check_auto_slowmode(message.channel, config)
        if slowmode_delay is not None:
            await apply_auto_slowmode(message.channel, slowmode_delay)
    
    return None
