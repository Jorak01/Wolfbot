# Administration & Moderation Guide

This guide covers all the administration and moderation features available in Wolfbot.

## 📋 Table of Contents

1. [Role Assignment Systems](#role-assignment-systems)
2. [Auto-Moderation](#auto-moderation)
3. [Message Logging](#message-logging)
4. [Warning & Strike System](#warning--strike-system)
5. [Audit Log Viewer](#audit-log-viewer)
6. [Channel Management](#channel-management)
7. [Alt Account Detection](#alt-account-detection)

---

## 🎭 Role Assignment Systems

### Button-Based Roles

Create interactive role selection messages with buttons.

**Module:** `src/discord_bot/admin_tools.py`

**Key Functions:**
```python
from src.discord_bot.admin_tools import create_role_button_message

# Create a role selection message
roles = [role1, role2, role3]  # List of discord.Role objects
await create_role_button_message(
    channel=text_channel,
    roles=roles,
    title="Select Your Roles",
    description="Click buttons to assign/remove roles"
)
```

**Features:**
- Persistent buttons (survive bot restarts when re-registered)
- Toggle functionality (click to add/remove)
- Up to 25 roles per message (Discord limit)

---

### Reaction-Based Roles

Traditional reaction role system using emoji reactions.

**Setup:**
```python
from src.discord_bot.admin_tools import setup_reaction_roles

# Map roles to emojis
role_emoji_map = {
    role1: "🎮",
    role2: "🎵",
    role3: "🎨"
}

await setup_reaction_roles(message, role_emoji_map)
```

**Event Handlers:**
```python
from src.discord_bot.admin_tools import handle_reaction_role_add, handle_reaction_role_remove

@bot.event
async def on_raw_reaction_add(payload):
    await handle_reaction_role_add(payload, bot)

@bot.event
async def on_raw_reaction_remove(payload):
    await handle_reaction_role_remove(payload, bot)
```

---

### Slash Command Roles

Assign/remove roles via slash commands with permission checks.

**Functions:**
```python
from src.discord_bot.admin_tools import slash_assign_role, slash_remove_role

# Assign a role
await slash_assign_role(interaction, member, role, reason="Promoted")

# Remove a role
await slash_remove_role(interaction, member, role, reason="Demoted")
```

**Features:**
- Permission validation (manage_roles required)
- Role hierarchy checking
- Reason logging

---

## 🛡️ Auto-Moderation

### Configuration

**Module:** `src/discord_bot/automod.py`

Configure auto-mod settings:
```python
from src.discord_bot.automod import AutoModConfig

config = AutoModConfig()
config.MAX_MESSAGES_PER_WINDOW = 5
config.SPAM_WINDOW_SECONDS = 5
config.SPAM_ACTION = "timeout"  # "timeout", "kick", "ban", "warn"
config.MAX_CAPS_PERCENTAGE = 70
config.BLOCK_INVITES = True
config.BLOCK_LINKS = False
config.ALLOWED_DOMAINS = ["youtube.com", "github.com"]
```

---

### Spam Detection

Automatically detects and handles spam messages.

**Features:**
- Configurable message rate limits
- Per-user tracking
- Automatic action (timeout/kick/ban/warn)
- Moderator exemption

**Usage:**
```python
from src.discord_bot.automod import check_spam, handle_spam

@bot.event
async def on_message(message):
    is_spam, reason = await check_spam(message, config)
    if is_spam:
        await handle_spam(message, reason, config)
```

---

### Caps Lock Detection

Detects excessive use of capital letters.

```python
from src.discord_bot.automod import check_excessive_caps

has_caps, reason = check_excessive_caps(message.content, config)
```

---

### Link Filtering

Block Discord invites and unauthorized links.

```python
from src.discord_bot.automod import check_links

has_blocked_links, reason = check_links(message.content, config)
```

**Configuration:**
- `BLOCK_INVITES`: Block Discord server invites
- `BLOCK_LINKS`: Block all links except whitelisted domains
- `ALLOWED_DOMAINS`: Whitelist specific domains

---

### Raid Protection

Detect and respond to server raids automatically.

```python
from src.discord_bot.automod import check_raid, activate_raid_mode, deactivate_raid_mode

@bot.event
async def on_member_join(member):
    is_raid, reason = await check_raid(member, config)
    if is_raid:
        await activate_raid_mode(member.guild, config)
```

**Features:**
- Join rate monitoring
- Automatic channel lockdown
- Manual activation/deactivation

---

### Auto-Slowmode

Automatically applies slowmode during high activity.

```python
from src.discord_bot.automod import check_auto_slowmode, apply_auto_slowmode

# Check if slowmode should be applied
slowmode_delay = await check_auto_slowmode(channel, config)
if slowmode_delay is not None:
    await apply_auto_slowmode(channel, slowmode_delay)
```

---

### Alt Account Detection

Identify suspicious new accounts based on heuristics.

```python
from src.discord_bot.automod import detect_alt_account

is_suspicious, reason = await detect_alt_account(member)
```

**Detection Criteria:**
- Account age < 7 days
- Default avatar
- Username with many numbers
- Similar names to existing members

---

## 📝 Message Logging

### Setup

**Module:** `src/discord_bot/logging_system.py`

The logging database is automatically initialized on import.

---

### Log Message Events

```python
from src.discord_bot.logging_system import (
    log_message_delete,
    log_message_edit,
    log_bulk_delete
)

@bot.event
async def on_message_delete(message):
    await log_message_delete(message)

@bot.event
async def on_message_edit(before, after):
    await log_message_edit(before, after)

@bot.event
async def on_bulk_message_delete(messages):
    await log_bulk_delete(messages, channel)
```

---

### Retrieve Logs

```python
from src.discord_bot.logging_system import (
    get_user_message_history,
    get_deleted_messages,
    get_edited_messages
)

# Get user's message history
logs = await get_user_message_history(user_id, guild_id, limit=50)

# Get deleted messages
deleted = await get_deleted_messages(guild_id, limit=50, user_id=None)

# Get edited messages
edited = await get_edited_messages(guild_id, limit=50, user_id=None)
```

---

### Log Channel System

Configure a dedicated channel for logging events.

```python
from src.discord_bot.logging_system import (
    set_log_channel,
    create_delete_log_embed,
    create_edit_log_embed,
    send_to_log_channel
)

# Set log channel
set_log_channel(guild.id, channel.id)

# Send log embeds
@bot.event
async def on_message_delete(message):
    embed = await create_delete_log_embed(message)
    await send_to_log_channel(message.guild, embed)
```

---

## ⚠️ Warning & Strike System

### Setup

**Module:** `src/discord_bot/warning_system.py`

The warning database is automatically initialized on import.

---

### Issue Warnings

```python
from src.discord_bot.warning_system import warn_user_with_escalation

# Warn a user with automatic escalation
warning_count, action, message = await warn_user_with_escalation(
    member=member,
    moderator=moderator,
    reason="Spamming in chat"
)
```

---

### Escalation Rules

Default escalation:
- **1 warning**: Just warn
- **2 warnings**: 1-hour timeout
- **3 warnings**: 24-hour timeout
- **4 warnings**: Kick
- **5+ warnings**: Ban

**Custom Rules:**
```python
from src.discord_bot.warning_system import EscalationRule

custom_rules = [
    EscalationRule(1, "none"),
    EscalationRule(2, "timeout", 1800),  # 30 minutes
    EscalationRule(3, "kick"),
    EscalationRule(4, "ban")
]

await warn_user_with_escalation(member, moderator, reason, rules=custom_rules)
```

---

### Manage Warnings

```python
from src.discord_bot.warning_system import (
    get_user_warnings,
    get_warning_count,
    remove_warning,
    clear_user_warnings
)

# Get warnings
warnings = await get_user_warnings(guild_id, user_id)

# Get count
count = await get_warning_count(guild_id, user_id)

# Remove specific warning
await remove_warning(warning_id)

# Clear all warnings
cleared = await clear_user_warnings(guild_id, user_id)
```

---

### Display Warnings

```python
from src.discord_bot.warning_system import format_warnings_embed

warnings = await get_user_warnings(guild_id, user_id)
embed = await format_warnings_embed(member, warnings)
await channel.send(embed=embed)
```

---

### Warning Leaderboard

```python
from src.discord_bot.warning_system import get_leaderboard, format_leaderboard_embed

leaderboard = await get_leaderboard(guild_id, limit=10)
embed = await format_leaderboard_embed(guild, leaderboard)
await channel.send(embed=embed)
```

---

### Warning Decay

Automatically remove old warnings:

```python
from src.discord_bot.warning_system import decay_old_warnings

# Decay warnings older than 30 days
decayed = await decay_old_warnings(guild_id, days_old=30)
```

---

## 📋 Audit Log Viewer

View Discord's audit logs with filtering.

**Module:** `src/discord_bot/admin_tools.py`

```python
from src.discord_bot.admin_tools import view_audit_log

# View recent audit logs
await view_audit_log(interaction, limit=10, action_type="ban")
```

**Supported Action Types:**
- `ban`, `unban`, `kick`
- `member_update`
- `channel_create`, `channel_delete`, `channel_update`
- `role_create`, `role_delete`, `role_update`
- `message_delete`

---

## 🔒 Channel Management

### Lock/Unlock Channels

**Module:** `src/discord_bot/moderation.py`

```python
from src.discord_bot.moderation import lock_channel, unlock_channel

# Lock a channel
await lock_channel(text_channel, reason="Raid protection")

# Unlock a channel
await unlock_channel(text_channel, reason="Situation resolved")
```

---

### Purge Messages

```python
from src.discord_bot.moderation import purge_messages

# Delete last 50 messages
await purge_messages(channel, amount=50, reason="Cleanup")
```

---

## 🔍 Alt Account Detection

Automatically flag suspicious accounts.

```python
from src.discord_bot.automod import detect_alt_account

@bot.event
async def on_member_join(member):
    is_suspicious, reason = await detect_alt_account(member)
    if is_suspicious:
        # Log to mod channel
        await mod_channel.send(f"⚠️ Suspicious account joined: {member.mention}\n{reason}")
```

---

## 🎯 Best Practices

### 1. **Set up logging channels**
Configure dedicated channels for different log types (mod logs, message logs, etc.)

### 2. **Configure auto-mod gradually**
Start with lenient settings and adjust based on your server's needs.

### 3. **Regular warning decay**
Set up automatic warning decay (e.g., 30 days) to give users fresh starts.

### 4. **Backup your database**
The SQLite database is stored in `src/data/db.sqlite3` - back it up regularly.

### 5. **Test permissions**
Ensure the bot has necessary permissions:
- `manage_roles` for role assignment
- `manage_messages` for message deletion
- `kick_members` and `ban_members` for moderation
- `view_audit_log` for audit log viewing
- `manage_channels` for slowmode/lockdown

---

## 🚀 Quick Start Example

Here's a complete example integrating multiple features:

```python
import discord
from discord.ext import commands
from src.discord_bot import automod, logging_system, warning_system, admin_tools

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Configure auto-mod
automod_config = automod.AutoModConfig()
automod_config.BLOCK_INVITES = True
automod_config.MAX_MESSAGES_PER_WINDOW = 5

# Set up log channel
@bot.command()
@commands.has_permissions(administrator=True)
async def setlogchannel(ctx, channel: discord.TextChannel):
    logging_system.set_log_channel(ctx.guild.id, channel.id)
    await ctx.send(f"✅ Log channel set to {channel.mention}")

# Message event with auto-mod
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Process auto-moderation
    action = await automod.process_message(message, automod_config)
    if action:
        # Log the action
        print(f"Auto-mod action: {action}")
    
    await bot.process_commands(message)

# Log deleted messages
@bot.event
async def on_message_delete(message):
    await logging_system.log_message_delete(message)
    embed = await logging_system.create_delete_log_embed(message)
    await logging_system.send_to_log_channel(message.guild, embed)

# Warn command with escalation
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str):
    count, action, escalation_msg = await warning_system.warn_user_with_escalation(
        member, ctx.author, reason
    )
    await ctx.send(f"⚠️ {member.mention} has been warned. Total warnings: {count}")
    if escalation_msg:
        await ctx.send(escalation_msg)

# View warnings
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member):
    warns = await warning_system.get_user_warnings(ctx.guild.id, member.id)
    embed = await warning_system.format_warnings_embed(member, warns)
    await ctx.send(embed=embed)

bot.run("YOUR_TOKEN")
```

---

## 📊 Database Schema

### Message Logs Table
```sql
CREATE TABLE message_logs (
    id INTEGER PRIMARY KEY,
    message_id INTEGER,
    channel_id INTEGER,
    guild_id INTEGER,
    author_id INTEGER,
    author_name TEXT,
    content TEXT,
    event_type TEXT,
    timestamp TIMESTAMP,
    edited_content TEXT,
    attachments TEXT
)
```

### Warnings Table
```sql
CREATE TABLE warnings (
    id INTEGER PRIMARY KEY,
    guild_id INTEGER,
    user_id INTEGER,
    moderator_id INTEGER,
    reason TEXT,
    timestamp TIMESTAMP,
    active BOOLEAN
)
```

---

## 🔧 Troubleshooting

### Database Issues
If you encounter database errors, try:
```python
from src.discord_bot.logging_system import init_logging_database
from src.discord_bot.warning_system import init_warning_database

init_logging_database()
init_warning_database()
```

### Permission Errors
Ensure bot role is positioned correctly in role hierarchy and has required permissions.

### Rate Limits
Discord has rate limits. If you're processing many actions, implement delays:
```python
import asyncio
await asyncio.sleep(1)  # Wait 1 second between actions
```

---

## 📚 Additional Resources

- **Discord.py Documentation**: https://discordpy.readthedocs.io/
- **Discord Developer Portal**: https://discord.com/developers/docs
- **Bot Permissions Calculator**: https://discordapi.com/permissions.html

---

## 🤝 Support

For issues or questions:
1. Check existing code comments and docstrings
2. Review this documentation
3. Test in a development server first
4. Check Discord.py version compatibility

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Compatibility:** discord.py 2.x+
