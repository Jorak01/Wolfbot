# AI Chatbot Integration Guide

This guide covers the AI-powered conversational features in Wolfbot, including context-aware chat, memory management, and safety features.

## Table of Contents
- [Overview](#overview)
- [AI Chat Commands](#ai-chat-commands)
- [Memory Management](#memory-management)
- [Server Lore System](#server-lore-system)
- [Personality System](#personality-system)
- [AI Safety Features](#ai-safety-features)
- [Configuration](#configuration)

---

## Overview

Wolfbot includes a sophisticated AI chatbot system with:
- **Context-Aware Conversations**: Remembers recent channel discussions
- **User Memory Profiles**: Stores facts about individual users
- **Server-Wide Lore**: Shared knowledge base for the entire server
- **Multiple Personalities**: Switch between different AI personas
- **Safety Filters**: NSFW and hate speech detection
- **Prompt Injection Protection**: Prevents manipulation attempts

---

## AI Chat Commands

### Basic Chat
**Command:** `!ai <message>` (aliases: `!ask`, `!chat`)

Chat with the AI bot. It will remember context from recent conversations in the channel.

**Examples:**
```
!ai Hello! How are you?
!ai What did we just talk about?
!ask Tell me a joke
!chat What's the meaning of life?
```

**Features:**
- Maintains conversation history per channel
- References user memories when responding
- Accesses server lore for context
- Uses active personality preset
- Cooldown system to prevent spam

---

## Memory Management

### Store a Memory
**Command:** `!remember <key> <value>` (aliases: `!storemem`, `!aimemory`)

Store a personal fact for the AI to remember about you.

**Examples:**
```
!remember favoritecolor blue
!remember hometown "New York"
!remember hobby programming
```

### View Memories
**Command:** `!memories [@user]` (aliases: `!listmem`, `!mymemories`)

View all memories the AI has stored. Can check your own or another user's memories (if permissions allow).

**Examples:**
```
!memories              # View your memories
!memories @username    # View another user's memories
```

### Forget a Memory
**Command:** `!forget <key>` (alias: `!forgetmem`)

Remove a specific memory the AI has about you.

**Example:**
```
!forget favoritecolor
```

### Clear All Memories
**Command:** `!clearmemories` (alias: `!clearmem`)

Remove all memories the AI has stored about you.

**Example:**
```
!clearmemories
```

---

## Server Lore System

Server lore is shared knowledge that the AI can reference when talking to anyone in the server. Perfect for roleplaying servers or maintaining server-specific context.

### Add Lore
**Command:** `!lore <key> <value>` (aliases: `!addlore`, `!serverlore`)
**Permissions:** Moderator+

Store server-wide lore that the AI can reference.

**Examples:**
```
!lore kingdom "The Kingdom of Avalon is ruled by Queen Elara"
!lore history "Founded in the year 1492"
!lore mascot "Our server mascot is a friendly dragon named Scales"
```

### View All Lore
**Command:** `!listlore` (aliases: `!showlore`, `!alllore`)

Display all server lore entries.

**Example:**
```
!listlore
```

### Remove Lore
**Command:** `!forgetlore <key>` (alias: `!removelore`)
**Permissions:** Moderator+

Remove a lore entry from the server.

**Example:**
```
!forgetlore kingdom
```

---

## Personality System

The AI can adopt different personalities to match your server's vibe or specific use cases.

### Built-in Personalities

1. **default** - Helpful, friendly assistant
2. **serious** - Professional advisor
3. **casual** - Relaxed, supportive friend
4. **lorekeeper** - Mystical keeper of ancient knowledge
5. **dungeon_master** - D&D Dungeon Master

### Set Active Personality
**Command:** `!persona <name>` (aliases: `!setpersona`, `!aipersona`)
**Permissions:** Moderator+

Change the AI's active personality.

**Examples:**
```
!persona lorekeeper
!persona dungeon_master
!persona casual
```

### List All Personalities
**Command:** `!personas` (alias: `!listpersonas`)

View all available personalities (built-in and custom).

**Example:**
```
!personas
```

### Create Custom Personality
**Command:** `!createpersona <name> <system_prompt>` (alias: `!addpersona`)
**Permissions:** Administrator

Create a custom AI persona for your server.

**Example:**
```
!createpersona pirate "You are a pirate captain. Always speak like a pirate and reference the seven seas."
```

### Delete Custom Personality
**Command:** `!deletepersona <name>` (alias: `!removepersona`)
**Permissions:** Administrator

Remove a custom persona (cannot delete built-in personas).

**Example:**
```
!deletepersona pirate
```

---

## AI Safety Features

### Content Filtering

The AI system includes multiple safety layers:

1. **NSFW Filter**: Blocks explicit sexual content
2. **Hate Speech Detection**: Prevents harmful language
3. **Prompt Injection Protection**: Stops attempts to manipulate the AI
4. **Cooldown System**: Prevents spam and abuse

### Blocked Content Examples

Messages will be blocked if they contain:
- Explicit sexual content (when NSFW filter is enabled)
- Hate speech or harassment
- Attempts to override AI instructions
- System manipulation attempts

### Clear Conversation Context
**Command:** `!clearcontext` (aliases: `!clearchat`, `!resetcontext`)
**Permissions:** Moderator+

Clear the AI's conversation history for the current channel. Useful if the AI gets confused or you want a fresh start.

**Example:**
```
!clearcontext
```

---

## Configuration

### View AI Settings
**Command:** `!aisettings` (alias: `!aiconfig`)

Display current AI configuration for the server.

**Example:**
```
!aisettings
```

**Settings Displayed:**
- Active Persona
- Language
- NSFW Filter Status
- Cooldown Duration
- Max Context Messages
- Roleplay Permissions

### Toggle NSFW Filter
**Command:** `!ainsfwfilter <true|false>` (alias: `!togglensfw`)
**Permissions:** Administrator

Enable or disable the NSFW content filter.

**Examples:**
```
!ainsfwfilter true    # Enable filter
!ainsfwfilter false   # Disable filter (use cautiously!)
```

### Set Cooldown
**Command:** `!aicooldown <seconds>` (alias: `!setaicooldown`)
**Permissions:** Administrator

Configure how long users must wait between AI chat commands.

**Examples:**
```
!aicooldown 3    # 3 second cooldown
!aicooldown 10   # 10 second cooldown
!aicooldown 0    # No cooldown (not recommended)
```

**Valid Range:** 0-60 seconds

---

## Usage Examples

### Roleplay Server Setup

```bash
# Set up a fantasy world
!lore world "The land of Aethermoor, a realm of magic and dragons"
!lore capital "Silvermoon City, home of the High Council"
!lore threat "The Shadow King threatens from the north"

# Switch to lorekeeper persona
!persona lorekeeper

# Chat with AI
!ai Tell me about our world
!ai What threats do we face?
```

### D&D Campaign Assistant

```bash
# Use Dungeon Master personality
!persona dungeon_master

# Store campaign info as lore
!lore campaign "The Quest for the Crystal of Light"
!lore party "Four brave adventurers seek ancient artifacts"

# Get help during sessions
!ai Describe a mysterious tavern
!ai Generate a random NPC for the party to meet
```

### Personal Server Assistant

```bash
# Set casual friendly persona
!persona casual

# Store personal preferences
!remember timezone EST
!remember interests "gaming, anime, coding"

# Natural conversations
!ai What should I do today?
!ai Remember that movie I mentioned last week?
```

---

## Best Practices

### For Server Admins

1. **Set Appropriate Cooldowns**: 3-5 seconds prevents spam while allowing natural conversation
2. **Configure NSFW Filter**: Enable for general servers, consider disabling only for 18+ communities
3. **Curate Server Lore**: Keep lore entries relevant and up-to-date
4. **Choose Right Persona**: Match personality to your server's theme
5. **Monitor Usage**: Check conversation logs periodically

### For Users

1. **Be Specific**: The AI works better with clear, specific questions
2. **Use Memories Wisely**: Store important preferences the AI should remember
3. **Respect Cooldowns**: Wait for your turn to prevent spam
4. **Report Issues**: If AI behaves unexpectedly, contact mods
5. **Have Fun**: Experiment with different conversation styles!

---

## Technical Details

### Context Management

- **Channel-Based**: Each channel maintains separate conversation history
- **Message Limit**: Configurable (default: 10 most recent messages)
- **User Memories**: Up to 20 memories per user
- **Server Lore**: Up to 50 entries per server

### Memory Types

1. **User Memories**: Personal facts about individual users
2. **Server Lore**: Shared knowledge accessible to all
3. **Conversation History**: Recent messages in each channel

### Database Storage

All AI data is stored in SQLite database tables:
- `ai_user_memory` - Personal memories
- `ai_lore_memory` - Server lore
- `ai_conversation_history` - Chat history
- `ai_personas` - Custom personalities
- `ai_guild_settings` - Server configuration

---

## API Integration

**Note**: The current implementation uses placeholder responses. To enable real AI functionality, integrate with:

- **OpenAI GPT-4/3.5**: Best quality, requires API key
- **Anthropic Claude**: Alternative with strong safety
- **Local Models**: Self-hosted options for privacy

Integration point is in `src/integrations/ai_integration.py` at the `_call_ai_api` method.

---

## Troubleshooting

### AI Not Responding

1. Check if cooldown is active
2. Verify bot has message permissions
3. Check if NSFW filter is blocking content
4. Try `!aisettings` to view configuration

### Context Issues

1. Use `!clearcontext` to reset channel history
2. Check if conversation history limit is too low
3. Verify memories are stored with `!memories`

### Permission Errors

1. Ensure proper role permissions for mod commands
2. Check bot role hierarchy
3. Verify administrator access for config changes

---

## Security Considerations

### Privacy

- User memories are per-server (not shared between servers)
- Conversation history is logged in database
- Admins can view all memories and lore
- Consider privacy when storing sensitive information

### Safety

- NSFW filter enabled by default
- Prompt injection protection active
- Hate speech detection
- Cooldown system prevents abuse
- Moderators can clear problematic conversations

---

## Future Enhancements

Planned features:
- [ ] Multi-language support
- [ ] Voice integration
- [ ] Image generation
- [ ] Personality mood states
- [ ] Advanced context summarization
- [ ] Memory tagging system
- [ ] Timeline reconstruction
- [ ] Emotional intelligence

---

## Support

For issues or suggestions:
- Report bugs with `/reportbug`
- Request features in your server's feedback channel
- Check other guides: [GAMING_UTILITIES_GUIDE.md](GAMING_UTILITIES_GUIDE.md), [ADMIN_MODERATION_GUIDE.md](ADMIN_MODERATION_GUIDE.md)

---

*This AI system transforms Wolfbot into a context-aware companion that learns and adapts to your community!*
