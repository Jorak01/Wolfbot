# Leveling System Guide

This guide covers the XP and leveling system in Wolfbot, including rank tracking, leaderboards, and level-based role rewards.

## 📋 Table of Contents

1. [Overview](#overview)
2. [How XP Works](#how-xp-works)
3. [User Commands](#user-commands)
4. [Admin Commands](#admin-commands)
5. [Configuration](#configuration)
6. [Integration Guide](#integration-guide)
7. [Database Schema](#database-schema)

---

## 🎯 Overview

The leveling system rewards active members with XP (experience points) for participating in your server. As members gain XP, they level up and can receive role rewards at specific milestones.

**Key Features:**
- Automatic XP gain from messages
- XP cooldown to prevent spam farming
- Customizable XP amounts per message
- Level-based role rewards
- Server leaderboards
- Beautiful rank cards with embeds
- Per-server tracking (separate levels per server)

---

## 📊 How XP Works

### XP Gain Formula

Members earn XP by sending messages in your server:
- **Base XP per message**: 15-25 XP (random)
- **Cooldown between gains**: 60 seconds (configurable)
- **Messages must be**: At least 3 characters long

### Level Calculation

The XP required for each level increases exponentially:

```python
XP for level N = 100 * (N ^ 2)
```

**Example Level Requirements:**
- Level 1: 100 XP
- Level 2: 400 XP (total)
- Level 3: 900 XP (total)
- Level 5: 2,500 XP (total)
- Level 10: 10,000 XP (total)
- Level 20: 40,000 XP (total)
- Level 50: 250,000 XP (total)

### XP Cooldown

To prevent spam, members can only gain XP once every 60 seconds. This encourages quality conversation over rapid-fire messages.

---

## 👤 User Commands

### View Your Rank
**Command:** `!rank [@member]` (aliases: `!level`, `!xp`)

Display your current level, XP, and rank on the server.

**Examples:**
```
!rank              # View your own rank
!rank @username    # View another user's rank
!level             # Same as !rank
!xp @username      # Same as !rank @username
```

**Rank Card Shows:**
- Member's display name and avatar
- Current level
- Total XP earned
- XP progress to next level (with progress bar)
- Server rank (e.g., "Rank #5 of 100")

---

### View Leaderboard
**Command:** `!leaderboard` (aliases: `!lb`, `!top`)

Display the top 10 members by level and XP.

**Example:**
```
!leaderboard
!lb
!top
```

**Leaderboard Shows:**
- Top 10 members ranked by XP
- Each member's level and total XP
- Rank position with medals (🥇🥈🥉) for top 3

---

## 🛠️ Admin Commands

### Set Level Role Rewards
**Command:** `!setlevelrole <level> <role>`
**Permissions:** Manage Roles

Assign a role as a reward when members reach a specific level.

**Examples:**
```
!setlevelrole 5 @Active Member
!setlevelrole 10 @Veteran
!setlevelrole 25 @Legend
!setlevelrole 50 @Elite
```

**Features:**
- Multiple roles can be set for different levels
- Roles are automatically assigned when members level up
- Previous level roles are kept (roles stack)
- Bot must have Manage Roles permission
- Bot's role must be higher than the reward role

---

## ⚙️ Configuration

### Leveling Settings

**Module:** `src/discord_bot/leveling_system.py`

```python
from src.discord_bot.leveling_system import LevelingConfig

# Default configuration
config = LevelingConfig()
config.MIN_XP_PER_MESSAGE = 15
config.MAX_XP_PER_MESSAGE = 25
config.XP_COOLDOWN_SECONDS = 60
config.MIN_MESSAGE_LENGTH = 3
config.ANNOUNCE_LEVEL_UP = True
```

### Customization Options

**XP Gain per Message:**
```python
config.MIN_XP_PER_MESSAGE = 10  # Minimum XP
config.MAX_XP_PER_MESSAGE = 30  # Maximum XP
# Each message gives random XP between min and max
```

**XP Cooldown:**
```python
config.XP_COOLDOWN_SECONDS = 60  # Wait time between XP gains
# Lower = faster leveling, but more spam-friendly
# Higher = slower leveling, but more spam-resistant
```

**Level-Up Announcements:**
```python
config.ANNOUNCE_LEVEL_UP = True  # Send level-up messages
# Set to False to disable level-up announcements
```

---

## 🔧 Integration Guide

### Enable Leveling in Your Bot

The leveling system processes messages automatically when integrated:

```python
import discord
from discord.ext import commands
from src.discord_bot import leveling_system

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Process leveling
    result = await leveling_system.process_message_for_xp(message)
    
    if result:
        new_level, leveled_up = result
        
        if leveled_up:
            # Create level-up embed
            embed = await leveling_system.create_level_up_embed(
                message.author, 
                new_level
            )
            await message.channel.send(embed=embed)
            
            # Assign level role rewards
            if isinstance(message.author, discord.Member):
                roles = await leveling_system.assign_level_roles(
                    message.author, 
                    new_level
                )
                if roles:
                    role_names = ", ".join(r.name for r in roles)
                    await message.channel.send(
                        f"🎉 {message.author.mention} earned: {role_names}!"
                    )
    
    # Process commands
    await bot.process_commands(message)
```

---

### Commands Setup

```python
@bot.command(name="rank", aliases=["level", "xp"])
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    
    # Get user stats
    stats = await leveling_system.get_user_stats(ctx.guild.id, member.id)
    if not stats:
        await ctx.send(f"{member.mention} hasn't earned any XP yet!")
        return
    
    # Get rank
    rank = await leveling_system.get_user_rank(ctx.guild.id, member.id)
    
    # Create rank card
    embed = await leveling_system.create_rank_card_embed(member, stats, rank)
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard(ctx):
    # Get top 10
    lb = await leveling_system.get_leaderboard(ctx.guild.id, limit=10)
    
    # Create leaderboard embed
    embed = await leveling_system.create_leaderboard_embed(ctx.guild, lb)
    await ctx.send(embed=embed)

@bot.command(name="setlevelrole")
@commands.has_permissions(manage_roles=True)
async def setlevelrole(ctx, level: int, role: discord.Role):
    await leveling_system.set_level_role(ctx.guild.id, level, role.id)
    await ctx.send(f"✅ Level {level} reward set to {role.mention}")
```

---

## 💾 Database Schema

### User Levels Table

```sql
CREATE TABLE user_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    last_xp_time TIMESTAMP,
    UNIQUE(guild_id, user_id)
)
```

### Level Roles Table

```sql
CREATE TABLE level_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    UNIQUE(guild_id, level)
)
```

---

## 🎨 Level-Up Embed Customization

Customize the appearance of level-up notifications:

```python
async def custom_level_up_embed(member, level):
    embed = discord.Embed(
        title="🎉 Level Up!",
        description=f"{member.mention} reached **Level {level}**!",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Keep Going!", value="Stay active to earn more XP!", inline=False)
    embed.set_footer(text=f"Level {level}")
    return embed
```

---

## 📈 Best Practices

### For Server Admins

1. **Set Meaningful Rewards**: Create role rewards at milestones (5, 10, 25, 50, etc.)
2. **Don't Over-Reward**: Too many level roles can clutter your server
3. **Balance XP Gain**: Adjust cooldown based on server activity
4. **Monitor Spam**: Watch for users trying to farm XP with spam
5. **Celebrate Milestones**: Announce major level-ups in a dedicated channel

### Recommended Role Structure

```
Level 5   → @Active Member (basic perks)
Level 10  → @Contributor (voice channel access)
Level 20  → @Veteran (special channels)
Level 35  → @Legend (exclusive perks)
Level 50  → @Elite (highest tier)
```

### XP Cooldown Guidelines

- **Very Active Servers** (100+ messages/hour): 90-120 seconds
- **Active Servers** (50-100 messages/hour): 60 seconds (default)
- **Small Servers** (<50 messages/hour): 30-45 seconds

---

## 🚀 Advanced Features

### Manual XP Management

```python
from src.discord_bot.leveling_system import add_xp

# Manually award XP
new_level, leveled_up = await add_xp(
    guild_id=ctx.guild.id,
    user_id=member.id,
    amount=500,  # XP to add
    bypass_cooldown=True  # Skip cooldown check
)
```

### Get User Stats

```python
from src.discord_bot.leveling_system import get_user_stats

stats = await get_user_stats(guild_id, user_id)
# Returns: {'xp': 5000, 'level': 15, 'last_xp_time': datetime}
```

### Check XP Cooldown

```python
from src.discord_bot.leveling_system import can_gain_xp

can_gain = await can_gain_xp(guild_id, user_id)
# Returns True if cooldown expired, False otherwise
```

---

## 🔍 Troubleshooting

### Members Not Gaining XP

1. **Check Message Length**: Messages must be 3+ characters
2. **Verify Cooldown**: Members can only gain XP once per minute
3. **Bot Permissions**: Ensure bot can read messages
4. **Database Connection**: Check if database is initialized

### Level Roles Not Assigning

1. **Bot Role Position**: Bot's role must be higher than reward roles
2. **Manage Roles Permission**: Bot needs "Manage Roles" permission
3. **Role Hierarchy**: Verify role positions in server settings
4. **Check Configuration**: Use `!setlevelrole` to verify role is set

### Leaderboard Empty

1. **No Activity**: Members need to send messages to gain XP
2. **Database Issues**: Check if leveling database is initialized
3. **Guild ID**: Ensure bot is tracking the correct guild

---

## 🎯 Example Implementation

Complete example for bot.py:

```python
import discord
from discord.ext import commands
from src.discord_bot import leveling_system

# Initialize database
leveling_system.init_leveling_database()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Leveling system active in {len(bot.guilds)} servers")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    
    # Process XP
    result = await leveling_system.process_message_for_xp(message)
    if result:
        new_level, leveled_up = result
        if leveled_up:
            embed = await leveling_system.create_level_up_embed(
                message.author, new_level
            )
            await message.channel.send(embed=embed)
            
            roles = await leveling_system.assign_level_roles(
                message.author, new_level
            )
    
    await bot.process_commands(message)

@bot.command(name="rank", aliases=["level", "xp"])
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    stats = await leveling_system.get_user_stats(ctx.guild.id, member.id)
    
    if not stats:
        await ctx.send(f"{member.display_name} hasn't earned any XP yet!")
        return
    
    rank = await leveling_system.get_user_rank(ctx.guild.id, member.id)
    embed = await leveling_system.create_rank_card_embed(member, stats, rank)
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard(ctx):
    lb = await leveling_system.get_leaderboard(ctx.guild.id, limit=10)
    embed = await leveling_system.create_leaderboard_embed(ctx.guild, lb)
    await ctx.send(embed=embed)

@bot.command(name="setlevelrole")
@commands.has_permissions(manage_roles=True)
async def setlevelrole(ctx, level: int, role: discord.Role):
    await leveling_system.set_level_role(ctx.guild.id, level, role.id)
    await ctx.send(f"✅ Level {level} reward set to {role.mention}")

bot.run("YOUR_TOKEN")
```

---

## 📚 Additional Resources

- **Module Reference**: `src/discord_bot/leveling_system.py`
- **Related Guides**:
  - [ADMIN_MODERATION_GUIDE.md](ADMIN_MODERATION_GUIDE.md) - Role management
  - [COMMUNITY_FEATURES_GUIDE.md](COMMUNITY_FEATURES_GUIDE.md) - Karma system
  - [README.md](README.md) - General bot setup

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Compatibility:** discord.py 2.x+
