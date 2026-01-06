# Community Features Guide

This guide covers the community engagement features in Wolfbot, including karma/reputation system, giveaways, events, anonymous confessions, and server statistics.

## 📋 Table of Contents

1. [Karma System](#karma-system)
2. [Giveaways](#giveaways)
3. [Events](#events)
4. [Anonymous Confessions](#anonymous-confessions)
5. [Server Statistics](#server-statistics)
6. [Integration Guide](#integration-guide)
7. [Database Schema](#database-schema)

---

## ⭐ Karma System

The karma (reputation) system allows members to recognize and reward each other for helpful behavior, contributions, and positive interactions.

### View Karma
**Command:** `!karma [@member]` (aliases: `!rep`, `!reputation`)

Check how much karma you or another member has earned.

**Examples:**
```
!karma              # View your own karma
!karma @username    # View another member's karma
!rep @username      # Same as !karma
```

**Output:**
- Member's display name and avatar
- Total karma points
- Number of times they've given karma
- Recent karma received

---

### Give Karma
**Command:** `!givekarma <member> [reason]` (aliases: `!+rep`, `!thanks`)

Award karma to another member to recognize their helpfulness or contributions.

**Examples:**
```
!givekarma @helper Thanks for helping me with setup!
!+rep @contributor Great suggestion in #feedback
!thanks @helper You're awesome!
```

**Rules:**
- Cannot give karma to yourself
- Cannot give karma to bots
- Can only give karma to each person once per hour (cooldown)
- Reason is optional but encouraged

**Features:**
- Automatic cooldown tracking (60 minutes per recipient)
- Tracks who gave karma and when
- Shows reason for karma in logs
- Optional notification to recipient

---

### Karma Leaderboard
**Command:** `!karmaleaderboard` (aliases: `!karmalb`, `!toprep`)

Display the members with the most karma on the server.

**Example:**
```
!karmaleaderboard
!karmalb
!toprep
```

**Leaderboard Shows:**
- Top 10 members by karma
- Total karma points for each
- Rank position with medals (🥇🥈🥉) for top 3
- Ties are sorted by user ID

---

## 🎁 Giveaways

Create exciting giveaways for your community with automatic winner selection.

### Create Giveaway
**Command:** `!giveaway <duration> <winners> <prize>` (aliases: `!gstart`)
**Permissions:** Manage Guild

Start a giveaway that members can enter by reacting.

**Examples:**
```
!giveaway 1h 1 Discord Nitro
!giveaway 24h 3 $10 Steam Gift Cards
!giveaway 3d 5 Custom Roles
!gstart 12h 2 VIP Access for 1 Month
```

**Duration Format:**
- `s` = seconds (e.g., `30s`)
- `m` = minutes (e.g., `15m`)
- `h` = hours (e.g., `2h`)
- `d` = days (e.g., `7d`)

**Features:**
- Automatic winner selection when time expires
- Members enter by reacting with 🎉
- Can't enter multiple times
- Winner announcement in the same channel
- Reroll command for invalid winners

**Giveaway Embed Includes:**
- Prize description
- Number of winners
- End time (countdown)
- Host information
- Entry count (updates live)
- React with 🎉 to enter instruction

---

### Manual Winner Selection

The bot automatically selects winners when the giveaway ends. Winners are:
- Selected randomly from all valid entries
- Checked to ensure they're still in the server
- Announced with mentions
- Notified via DM (if possible)

---

## 📅 Events

Create and manage server events that members can RSVP to.

### Create Event
**Command:** `!event <title> <start_time> [description]` (aliases: `!createevent`)

Schedule an event that members can sign up for.

**Examples:**
```
!event "Movie Night" "2026-01-15 20:00" Join us for movie night!
!event "Gaming Tournament" "tomorrow 3pm" Fortnite tournament
!event "Study Session" "Friday 6pm" Let's study together
```

**Time Format Examples:**
- `2026-01-15 20:00` (ISO format)
- `tomorrow 3pm`
- `Friday 6pm`
- `next Monday 8pm`
- `in 2 hours`

**Features:**
- Members RSVP by reacting with ✅
- Automatic attendee tracking
- Event reminders (optional)
- Display of confirmed attendees
- Event embed with all details

**Event Embed Includes:**
- Event title
- Start time
- Description
- Host information
- List of attendees (updates live)
- RSVP instructions

---

### RSVP to Events

Members RSVP to events by reacting with ✅ on the event message. The bot tracks:
- Who has RSVP'd
- When they RSVP'd
- Total attendee count
- Updates embed with current count

---

## 🎭 Anonymous Confessions

Allow members to share thoughts anonymously in a safe, moderated environment.

### Submit Confession
**Command:** `!confess <content>` (aliases: `!confession`)

Send an anonymous confession to a dedicated confession channel.

**Examples:**
```
!confess I actually really enjoy pineapple on pizza
!confession Sometimes I pretend to be AFK when I don't want to talk
```

**How It Works:**
1. Member sends confession via command (in DM or any channel)
2. Bot deletes the command message immediately
3. Bot posts confession anonymously in confession channel
4. Confession is numbered (Confession #123)
5. Original author is logged in database for moderation

**Features:**
- Complete anonymity to other members
- Numbered confessions for reference
- Moderation logging (admins can trace if needed)
- Content filtering (optional)
- Configurable confession channel

**Safety Features:**
- Commands are deleted immediately
- Only admins can see original authors (via database)
- Can be combined with auto-mod filters
- Option to disable confessions per server

---

## 📊 Server Statistics

Track and display server activity and growth metrics.

### View Server Stats
**Command:** `!serverstats` (aliases: `!serverinfo`)

Display comprehensive statistics about your server.

**Example:**
```
!serverstats
!serverinfo
```

**Statistics Include:**

**Member Stats:**
- Total members
- Online members
- Bots count
- Member growth (24h, 7d, 30d)

**Channel Stats:**
- Total channels
- Text channels
- Voice channels
- Categories

**Role Stats:**
- Total roles
- Hoisted roles
- Managed roles

**Activity Stats:**
- Messages sent (24h, 7d)
- Active users (24h, 7d)
- Most active channel
- Peak online members

**Server Info:**
- Server creation date
- Server owner
- Boost level
- Boost count
- Server features

---

### Automated Stats Tracking

The bot continuously tracks:
- Member joins/leaves (with timestamps)
- Message counts per channel
- Active user tracking
- Peak online member count
- Daily/weekly trends

---

## 🔧 Integration Guide

### Setup Karma System

```python
import discord
from discord.ext import commands
from src.discord_bot import community_features

# Initialize database
community_features.init_community_database()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.command(name="karma", aliases=["rep", "reputation"])
async def karma(ctx, member: discord.Member = None):
    member = member or ctx.author
    karma_points = await community_features.get_karma(ctx.guild.id, member.id)
    
    embed = discord.Embed(
        title=f"{member.display_name}'s Karma",
        description=f"**{karma_points}** karma points",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="givekarma", aliases=["+rep", "thanks"])
async def givekarma(ctx, member: discord.Member, *, reason: str = "Being awesome!"):
    if member == ctx.author:
        await ctx.send("❌ You can't give karma to yourself!")
        return
    
    if member.bot:
        await ctx.send("❌ You can't give karma to bots!")
        return
    
    success, new_karma = await community_features.give_karma(
        guild_id=ctx.guild.id,
        giver_id=ctx.author.id,
        receiver_id=member.id,
        reason=reason
    )
    
    if success:
        await ctx.send(
            f"✅ {member.mention} received karma! "
            f"They now have **{new_karma}** karma.\n"
            f"Reason: {reason}"
        )
    else:
        await ctx.send("❌ You can only give karma once per hour to each person!")
```

---

### Setup Giveaways

```python
@bot.command(name="giveaway", aliases=["gstart"])
@commands.has_permissions(manage_guild=True)
async def giveaway(ctx, duration: str, winners: int, *, prize: str):
    # Parse duration
    from src.discord_bot.utils_misc import parse_duration
    seconds = parse_duration(duration)
    
    if seconds < 10:
        await ctx.send("❌ Duration must be at least 10 seconds!")
        return
    
    if winners < 1 or winners > 20:
        await ctx.send("❌ Number of winners must be between 1 and 20!")
        return
    
    # Calculate end time
    import datetime as dt
    end_time = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)
    
    # Create giveaway
    giveaway_id = await community_features.create_giveaway(
        guild_id=ctx.guild.id,
        channel_id=ctx.channel.id,
        host_id=ctx.author.id,
        prize=prize,
        winners=winners,
        end_time=end_time
    )
    
    # Create embed
    embed = await community_features.create_giveaway_embed(
        prize=prize,
        end_time=end_time,
        host=ctx.author,
        entries=0
    )
    
    # Send and add reaction
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    
    # Schedule winner selection
    from src.discord_bot.scheduler import schedule_task
    
    async def select_winners():
        entries = await community_features.get_giveaway_entries(giveaway_id)
        result = await community_features.end_giveaway(giveaway_id)
        
        if result and result['winners']:
            winner_mentions = " ".join(f"<@{w}>" for w in result['winners'])
            await ctx.channel.send(
                f"🎉 **Giveaway Ended!**\n"
                f"Prize: {prize}\n"
                f"Winners: {winner_mentions}\n"
                f"Congratulations!"
            )
    
    schedule_task(end_time.timestamp(), select_winners)
```

---

### Setup Events

```python
@bot.command(name="event", aliases=["createevent"])
async def create_event_cmd(ctx, title: str, start_time: str, *, description: str = None):
    # Parse time (simplified example)
    import dateparser
    parsed_time = dateparser.parse(start_time)
    
    if not parsed_time:
        await ctx.send("❌ Invalid time format!")
        return
    
    # Create event
    event_id = await community_features.create_event(
        guild_id=ctx.guild.id,
        channel_id=ctx.channel.id,
        host_id=ctx.author.id,
        title=title,
        start_time=parsed_time,
        description=description
    )
    
    # Create embed
    embed = await community_features.create_event_embed(
        title=title,
        start_time=parsed_time,
        description=description,
        host=ctx.author,
        attendees=0
    )
    
    # Send and add reaction
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
```

---

### Setup Confessions

```python
@bot.command(name="confess", aliases=["confession"])
async def confess(ctx, *, content: str):
    # Delete command immediately
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Get confession channel (configure this per server)
    confession_channel_id = 123456789  # Your confession channel ID
    confession_channel = bot.get_channel(confession_channel_id)
    
    if not confession_channel:
        return
    
    # Store confession
    confession_id = await community_features.submit_confession(
        guild_id=ctx.guild.id,
        user_id=ctx.author.id,
        content=content
    )
    
    # Create embed
    embed = await community_features.create_confession_embed(
        confession_number=confession_id,
        content=content
    )
    
    # Post confession
    await confession_channel.send(embed=embed)
    
    # Notify user (optional)
    try:
        await ctx.author.send("✅ Your confession has been posted anonymously!")
    except:
        pass
```

---

## 💾 Database Schema

### Karma Table
```sql
CREATE TABLE karma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    karma INTEGER DEFAULT 0,
    given_count INTEGER DEFAULT 0,
    UNIQUE(guild_id, user_id)
)
```

### Karma History Table
```sql
CREATE TABLE karma_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    giver_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Giveaways Table
```sql
CREATE TABLE giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER,
    host_id INTEGER NOT NULL,
    prize TEXT NOT NULL,
    winners_count INTEGER DEFAULT 1,
    end_time TIMESTAMP NOT NULL,
    ended BOOLEAN DEFAULT 0
)
```

### Giveaway Entries Table
```sql
CREATE TABLE giveaway_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    giveaway_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(giveaway_id, user_id)
)
```

### Events Table
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Event Attendees Table
```sql
CREATE TABLE event_attendees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, user_id)
)
```

### Confessions Table
```sql
CREATE TABLE confessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Server Stats Table
```sql
CREATE TABLE server_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    date DATE NOT NULL,
    member_count INTEGER,
    message_count INTEGER,
    joins INTEGER DEFAULT 0,
    leaves INTEGER DEFAULT 0,
    UNIQUE(guild_id, date)
)
```

---

## 📈 Best Practices

### Karma System
1. **Set Clear Guidelines**: Define what deserves karma
2. **Moderate Karma Farming**: Watch for abuse
3. **Reward Meaningfully**: Consider karma milestones with rewards
4. **Don't Over-Reward**: Keep karma special

### Giveaways
1. **Clear Rules**: State eligibility requirements
2. **Reasonable Duration**: 1-48 hours is typical
3. **Verify Winners**: Check winners are eligible
4. **Fair Prizes**: Match prize value to entry requirements

### Events
1. **Advance Notice**: Create events days ahead
2. **Clear Details**: Time zone, requirements, etc.
3. **Send Reminders**: Notify attendees before event
4. **Follow Up**: Thank attendees after event

### Confessions
1. **Set Guidelines**: Rules about appropriate content
2. **Moderate Carefully**: Remove harmful confessions
3. **Privacy First**: Never reveal authors publicly
4. **Optional Feature**: Consider if it fits your community

---

## 🚀 Advanced Features

### Karma Rewards

Reward members who reach karma milestones:

```python
@bot.event
async def on_karma_milestone(member, karma):
    milestones = {
        10: "Helper",
        50: "Contributor",
        100: "Legend"
    }
    
    if karma in milestones:
        role_name = milestones[karma]
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
```

### Giveaway Requirements

Add requirements to giveaways:

```python
# Require specific role
@bot.command()
async def giveaway_role(ctx, role: discord.Role, duration: str, *, prize: str):
    # Only members with role can enter
    pass

# Require minimum level
@bot.command()
async def giveaway_level(ctx, min_level: int, duration: str, *, prize: str):
    # Only members at or above level can enter
    pass
```

---

## 🔍 Troubleshooting

### Karma Not Working
1. Check database initialization
2. Verify cooldown isn't active
3. Ensure bot has database permissions

### Giveaway Winners Not Selected
1. Verify scheduler is running
2. Check bot has message permissions
3. Ensure entries were recorded

### Confessions Not Posting
1. Verify confession channel is set
2. Check bot has send permission in channel
3. Ensure message deletion permission

---

## 📚 Additional Resources

- **Module Reference**: `src/discord_bot/community_features.py`
- **Related Guides**:
  - [LEVELING_SYSTEM_GUIDE.md](LEVELING_SYSTEM_GUIDE.md) - XP and levels
  - [ADMIN_MODERATION_GUIDE.md](ADMIN_MODERATION_GUIDE.md) - Moderation tools
  - [README.md](README.md) - General bot setup

---

**Version:** 1.0  
**Last Updated:** January 2026  
**Compatibility:** discord.py 2.x+
