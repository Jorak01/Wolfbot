# Wolfbot Slash Commands Guide

## Overview

Wolfbot now supports **both prefix commands (!) and slash commands (/)** providing a modern Discord experience with autocomplete and native integration.

## Features

✅ **Hybrid Command System** - Both `!command` and `/command` work
✅ **30+ Slash Commands** - Core functionality available via slash commands
✅ **Autocomplete Support** - Discord's native command picker
✅ **Parameter Descriptions** - Built-in help for each parameter
✅ **Ephemeral Responses** - Private messages where appropriate (e.g., moderation actions)

## Available Slash Commands

### Core Bot Commands
- `/status` - Check the bot status
- `/health` - Check integration health status

### Moderation Commands (Requires Moderator/Admin)
- `/warn <member> [reason]` - Warn a user with escalation
- `/warnings <member>` - View warnings for a user
- `/kick <member> [reason]` - Kick a member from the server
- `/ban <member> [reason]` - Ban a member from the server
- `/mute <member> <duration>` - Mute (timeout) a user
- `/purge [amount]` - Delete multiple messages

### Community & Leveling Commands
- `/rank [member]` - Check your or another user's rank and XP
- `/leaderboard` - Show the XP leaderboard
- `/karma [member]` - Check karma points
- `/givekarma <member> [reason]` - Give karma to another user
- `/serverstats` - Show server statistics dashboard

### Gaming & Fun Commands
- `/roll <expression>` - Roll dice (e.g., 2d6+1)
- `/coinflip` - Flip a coin
- `/droll <expression>` - Advanced D&D dice roller with advantage/disadvantage

### AI Chatbot Commands
- `/ai <message>` - Chat with the AI bot
- `/remember <key> <value>` - Store a memory for the AI
- `/memories [member]` - List AI memories about a user

### External API Commands
- `/mtgcard <card_name>` - Search for a Magic: The Gathering card
- `/dndspell <spell_name>` - Search for a D&D 5e spell

### Music Commands (Requires Spotify Integration)
- `/nowplaying` - Show what's currently playing on Spotify
- `/play <query>` - Play a song from Spotify
- `/queue` - Show the music queue
- `/skip` - Skip the current track

## Usage Examples

### Basic Commands
```
/status
/health
/rank
/leaderboard
```

### With Parameters
```
/warn @user Spamming in chat
/kick @user Violating server rules
/mute @user 10m
/roll 2d6+3
```

### AI Interaction
```
/ai What's the weather like today?
/remember favoritecolor blue
/memories @user
```

### Gaming
```
/droll 1d20 advantage
/mtgcard Lightning Bolt
/dndspell fireball
```

### Music
```
/play never gonna give you up
/queue
/skip
```

## Command Sync

Slash commands are automatically synced when the bot starts:
- **Global sync** may take up to 1 hour to propagate across all Discord servers
- **Guild-specific sync** is instant but only available in that server
- The bot syncs commands globally by default

## Permissions

Slash commands respect the same permission system as prefix commands:
- **Public commands** - Available to everyone
- **Moderator commands** - Requires Moderator or Administrator role
- **Admin commands** - Requires Administrator permission

## Benefits Over Prefix Commands

1. **Discoverability** - Type `/` to see all available commands
2. **Autocomplete** - Command and parameter suggestions as you type
3. **Validation** - Discord validates parameters before sending
4. **Help Text** - Built-in descriptions for every command and parameter
5. **Modern UX** - Native Discord interface

## Compatibility

Both command systems work simultaneously:
- **Prefix commands** (`!command`) - Still fully supported
- **Slash commands** (`/command`) - New modern interface
- Users can choose their preferred method

## Adding More Slash Commands

To add new slash commands, edit `src/discord_bot/slash_commands.py`:

```python
@tree.command(name="mycommand", description="My command description")
@app_commands.describe(param="Parameter description")
async def my_command(interaction: discord.Interaction, param: str):
    await interaction.response.send_message(f"You said: {param}")
```

## Troubleshooting

### Commands Not Showing Up
1. Wait up to 1 hour for global sync to complete
2. Check bot console for sync errors
3. Ensure bot has `applications.commands` scope
4. Try restarting Discord client

### Permission Errors
- Ensure the bot has the `applications.commands` permission
- Check role hierarchy for moderation commands
- Verify the bot can read/send messages in the channel

### Command Conflicts
- If a command exists as both prefix and slash, both will work
- Slash commands take precedence in the Discord UI
- Prefix commands remain available for backwards compatibility

## Notes

- **30+ slash commands** implemented out of 98+ total commands
- More commands will be gradually converted to slash commands
- All prefix commands remain fully functional
- Slash commands provide a better user experience for common operations

---

For more information, see:
- `COMMAND_FUNCTIONALITY_REPORT.md` - Complete command reference
- `README.md` - Bot setup and configuration
- Discord.py documentation - https://discordpy.readthedocs.io/
