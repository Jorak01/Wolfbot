# Wolfbot Starter

Baseline Discord bot structure with integration logic separated from the Discord wiring. Uses `discord.py` with a simple `!status` command that pulls from `src/integration.py`.

## Layout
```
.
├─ src/
│  ├─ bot.py                   # Discord entrypoint + commands
│  ├─ config.py                # Env loading and token validation
│  ├─ integration.py           # External service / business logic
│  ├─ api_manager.py           # Centralized API management and token handling
│  ├─ __init__.py
│  ├─ discord_bot/             # Bot utilities and helpers
│  │   ├─ __init__.py
│  │   ├─ admin_tools.py       # Role assignment (buttons/reactions), audit logs
│  │   ├─ analytics.py         # Event/usage logging
│  │   ├─ automod.py           # Spam detection, raid protection, content filtering
│  │   ├─ command_handler.py   # Command registries, dispatch, cooldowns
│  │   ├─ community_features.py # Karma, giveaways, events, confessions
│  │   ├─ config_store.py      # JSON-backed guild/user config
│  │   ├─ games.py             # Dice, coin, RPS, poll creation
│  │   ├─ gaming_utilities.py  # D&D tools, initiative tracker, loot generator
│  │   ├─ leveling_system.py   # XP tracking, level-up, role rewards
│  │   ├─ lifecycle.py         # Startup/shutdown helpers
│  │   ├─ logging_system.py    # Message logging (delete/edit), log channels
│  │   ├─ maintenance.py       # Backup/restore, dependency/version checks
│  │   ├─ member_roles.py      # Join/leave hooks and role assignment
│  │   ├─ messaging.py         # Message send/edit/pin helpers
│  │   ├─ moderation.py        # Kick/ban/mute/purge utilities
│  │   ├─ notifications.py     # Announcement/DM/react helpers
│  │   ├─ scheduler.py         # Task scheduling and temporary messages
│  │   ├─ security.py          # Permission helpers
│  │   ├─ storage_api.py       # SQLite, cache, HTTP fetch, retry
│  │   ├─ ui_components.py     # Embeds/buttons/dropdowns/modals helpers
│  │   ├─ utils_misc.py        # Duration/UUID/url/format helpers
│  │   ├─ warning_system.py    # Warning/strike system with auto-escalation
│  │   └─ welcome_system.py    # Welcome/farewell messages with buttons
│  ├─ integrations/
│  │   ├─ __init__.py
│  │   ├─ ai_integration.py       # AI chatbot with memory & personas
│  │   ├─ external_apis.py        # MTG, D&D, GitHub, AI providers
│  │   ├─ spotify_integration.py  # Spotify API + voice playback with queue
│  │   └─ twitch_integration.py   # Twitch <-> Discord monitor, chat relay
│  ├─ api/                     # API client structure
│  │   └─ tokens.py            # Token management
│  └─ data/                    # Data storage directory (SQLite databases)
├─ scripts/
│  └─ check_imports.py         # Import validation and dependency checker
├─ tests/
│  ├─ check_discord_bot.py     # Discord bot validation tests
│  ├─ check_syntax.py          # Syntax checker
│  ├─ test_api_manager.py      # API manager tests
│  ├─ test_config_store.py     # Config store tests
│  ├─ test_games.py            # Games module tests
│  ├─ test_integration.py      # Integration tests
│  ├─ test_scheduler.py        # Scheduler tests
│  ├─ test_utils_misc.py       # Utilities tests
│  ├─ validate_all.py          # Comprehensive validation
│  └─ verify_env_integration.py # Environment integration tests
├─ .env.template               # Environment variables template
├─ .gitignore
├─ API_MANAGER_GUIDE.md        # API manager documentation
├─ CHECK_IMPORTS_DOCUMENTATION.md  # Import checker docs
├─ MUSIC_PLAYBACK_GUIDE.md     # Music playback comprehensive guide
├─ README.md
├─ requirements.txt
├─ SETUP_GUIDE.md              # Setup instructions
└─ SPOTIFY_SETUP_GUIDE.md      # Spotify integration setup
```

## Setup
1) Create and activate a venv (recommended):
   - Windows: `python -m venv .venv && .\.venv\Scripts\activate`
   - Unix: `python -m venv .venv && source .venv/bin/activate`
2) Install deps: `pip install -r requirements.txt`
3) Install FFmpeg and ensure it is on your PATH for audio playback.
4) Create `.env` with your bot token and any API keys:
```
DISCORD_TOKEN=your_bot_token_here

# Optional HTTP status stub
API_BASE_URL=https://api.example.com
API_KEY=your_optional_api_key
API_TIMEOUT=10.0
API_TOKENS=status=tokenA;service2=tokenB

# OpenAI / Copilot-style art generation
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=optional_custom_base
OPENAI_MODEL=gpt-4o-mini
OPENAI_IMAGE_MODEL=dall-e-3

# Search result limit (default 5)
SEARCH_MAX_RESULTS=5

# Twitch integration (chat + live monitoring)
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TWITCH_ACCESS_TOKEN=oauth_token_with_scopes
TWITCH_REFRESH_TOKEN=refresh_token_with_scopes
TWITCH_BROADCASTER_ID=your_twitch_user_id
TWITCH_CHANNEL_NAME=yourchannel
TWITCH_GUILD_ID=discord_guild_id
TWITCH_LIVE_ROLE_ID=discord_role_id_for_live
TWITCH_ANNOUNCE_CHANNEL_ID=discord_channel_id_for_live_alerts
TWITCH_EVENT_LOG_CHANNEL_ID=discord_channel_id_for_chat/logs
TWITCH_CLIPS_CHANNEL_ID=discord_channel_id_for_vods_clips
TWITCH_REMINDER_CHANNEL_ID=discord_channel_id_for_reminders
TWITCH_MONITOR_INTERVAL=60
TWITCH_CHAT_ENABLED=true

# Spotify integration (music search and playback)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_REFRESH_TOKEN=your_spotify_refresh_token
```

## Commands Overview

### 🔍 General & Utility
- `!status` — Integration status check
- `!search <query>` — DuckDuckGo-powered web search
- `!imagine|!art|!image <prompt>` — AI image generation via OpenAI DALL-E
- `!health` — System health check
- `!apistatus|!apis|!checkapis` — Check status of all API integrations
- `!fetchjson <url>` — Fetch and display JSON from URL

### 📺 Twitch Integration
- `!uptime` — Stream uptime
- `!live` — Show live stream embed
- `!twitchstats|!tstats` — Viewer stats, peaks, follows, subs
- `!tchat <message>` — Relay message to Twitch chat
- `!followers` — Follower count
- `!subs` — Subscriber count
- `!streamgame` — Current game/category

### 🎵 Spotify & Music
**Account Info:**
- `!spotify|!sp|!nowlistening` — Show currently playing track
- `!spotifysearch|!spsearch <query>` — Search Spotify catalog
- `!toptracks [timeframe]` — Your top tracks (short/medium/long)
- `!topartists [timeframe]` — Your top artists
- `!playlists|!myplaylists` — Your Spotify playlists

**Voice Playback:**
- `!join|!connect` — Join voice channel
- `!leave|!disconnect|!dc` — Leave voice channel
- `!play|!p <query>` — Play track (auto-joins voice)
- `!pause` — Pause playback
- `!resume|!unpause` — Resume playback
- `!skip|!next|!s` — Skip current track
- `!stop` — Stop and clear queue
- `!loop|!repeat <mode>` — Loop mode (off/track/queue)
- `!volume|!vol|!v <0-100>` — Set volume
- `!queue|!q` — Show queue
- `!nowplaying|!np|!current` — Currently playing
- `!clearqueue|!cq|!clear` — Clear queue
- `!remove|!rm <position>` — Remove track from queue
- `!shuffle` — Shuffle queue

### 🤖 AI Chatbot
- `!ai|!ask|!chat <message>` — Chat with AI
- `!remember <key> <value>` — Store personal memory
- `!forget <key>` — Forget a memory
- `!memories [@user]` — View memories
- `!clearmemories` — Clear all memories
- `!lore <key> <value>` — Add server lore (mod+)
- `!listlore` — View all lore
- `!forgetlore <key>` — Remove lore (mod+)
- `!persona <name>` — Set AI personality (mod+)
- `!personas` — List available personas
- `!createpersona <name> <prompt>` — Create custom persona (admin)
- `!deletepersona <name>` — Delete persona (admin)
- `!clearcontext` — Clear conversation history (mod+)
- `!aisettings` — View AI configuration
- `!ainsfwfilter <true|false>` — Toggle NSFW filter (admin)
- `!aicooldown <seconds>` — Set cooldown (admin)

### 🛡️ Moderation
**Warning System:**
- `!warn <member> <reason>` — Issue warning
- `!warnings <member>` — View warnings
- `!clearwarnings <member>` — Clear all warnings
- `!removewarn <id>` — Remove specific warning
- `!warnleaderboard|!warnlb` — Warning leaderboard

**Actions:**
- `!mute <member> <duration>` — Mute user
- `!kick <member> [reason]` — Kick member
- `!ban <member> [reason]` — Ban member
- `!unban <user_id>` — Unban user
- `!purge <amount>` — Delete messages
- `!lock` — Lock channel
- `!unlock` — Unlock channel
- `!raidmode <on|off|status>` — Raid protection

**Logging:**
- `!setlogchannel <channel>` — Set log channel (admin)
- `!viewlogs [type] [limit]` — View message logs

### ⭐ Leveling System
- `!rank|!level|!xp [@member]` — View rank/level
- `!leaderboard|!lb|!top` — Server leaderboard
- `!setlevelrole <level> <role>` — Set level reward role (mod+)

### 🎉 Community Features
**Karma System:**
- `!karma|!rep [@member]` — View karma
- `!givekarma|!+rep <member> [reason]` — Give karma
- `!karmaleaderboard|!karmalb` — Karma leaderboard

**Events & Activities:**
- `!giveaway|!gstart <duration> <winners> <prize>` — Create giveaway (mod+)
- `!event <title> <time> [description]` — Create event
- `!confess|!confession <content>` — Anonymous confession
- `!serverstats|!serverinfo` — Server statistics

### 🎲 Gaming Utilities
**Dice & Random:**
- `!roll <expression>` — Basic dice roll
- `!droll|!dr <expression>` — Advanced dice with advantage/disadvantage
- `!coin` — Flip coin
- `!rps <choice>` — Rock paper scissors
- `!poll <question | option1 | option2>` — Create poll

**D&D Tools:**
- `!stats|!abilities [method]` — Generate ability scores
- `!encounter <level> [size]` — Generate encounter
- `!initiative|!init <action>` — Track initiative
- `!loot|!treasure [rarity] [count]` — Generate loot
- `!npc` — Random NPC generator
- `!quest` — Random quest hook
- `!name` — Random fantasy name
- `!dndspell|!spell <name>` — Look up D&D spell
- `!dndmonster|!monster <name>` — Look up D&D monster

**MTG Tools:**
- `!mtgcard|!card <name>` — Look up MTG card
- `!randomcard` — Random MTG card
- `!deck <decklist>` — Parse MTG decklist

### 🔧 Admin Tools
- `!announce <message>` — Server announcement (mod+)
- `!dm <user_id> <message>` — DM a user (mod+)
- `!react <message_id> <emoji>` — Add reaction to message (mod+)
- `!tempmsg <duration> <message>` — Temporary message (mod+)
- `!setwelcome <channel>` — Set welcome channel (mod+)
- `!setleave <channel>` — Set leave channel (mod+)
- `!backup` — Backup bot data (admin)
- `!restore <name>` — Restore from backup (admin)
- `!reloadext` — Reload extensions (admin)
- `!shutdown` — Shutdown bot (admin)

### 🌐 External APIs
- `!github|!repo <owner> <repo>` — GitHub repository info

## Twitch integration highlights
- Stream monitoring: live/offline detection, uptime, category, peak viewers, live/end notifications, presence update, optional live role assignment.
- Chat relay: relay Discord → Twitch chat via `!tchat`, Twitch → Discord mirror, simple Twitch command handling/sync.
- Community & moderation: follower/sub alerts, active viewer tracking, ban/timeout helpers, mod status check, mod-role sync stub.
- Monetization hooks: bits/subs/resubs/gifted subs/hype train trackers and leaderboards.
- Channel points: placeholder listeners for redemptions with custom reward handler and cooldown tracker.
- Automation: schedule reminders, daily checks, auto-post VOD/clip links, health check, token refresh, rate-limit handler.
- Discord UX: streaming embeds, presence updates, stub slash/button/dropdown handlers, owner/scope validation helpers.

## Spotify integration highlights
- Music search: Search Spotify catalog, view track details with artist, album, duration, and preview URLs.
- User stats: View your top tracks and artists with customizable timeframes (4 weeks, 6 months, all time).
- Playlist management: Browse your Spotify playlists with track counts and owner info.
- Now playing: Display currently playing tracks from your Spotify account with rich embeds.
- Voice playback: Full Discord voice channel integration with queue management.
- Queue system: Add multiple tracks, view queue with rich embeds, remove/shuffle tracks, track requester info.
- Playback controls: Play, pause, resume, skip, stop with complete state management.
- Loop modes: Loop individual tracks, entire queue, or disable looping.
- Volume control: Adjustable playback volume (0-100%) with real-time updates.
- Auto-join: Bot automatically joins your voice channel when you use play commands.
- Rich embeds: Beautiful queue displays with track info, duration, loop status, and volume indicators.

See [MUSIC_PLAYBACK_GUIDE.md](MUSIC_PLAYBACK_GUIDE.md) for detailed music playback documentation.

## 📚 Documentation

Comprehensive guides are available for all major features:

### Core Guides
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup instructions and troubleshooting
- **[API_MANAGER_GUIDE.md](API_MANAGER_GUIDE.md)** - API token management and configuration
- **[README.md](README.md)** - This file - overview and quick reference

### Feature-Specific Guides
- **[ADMIN_MODERATION_GUIDE.md](ADMIN_MODERATION_GUIDE.md)** - Moderation, warnings, auto-mod, logging, role management
- **[LEVELING_SYSTEM_GUIDE.md](LEVELING_SYSTEM_GUIDE.md)** - XP system, ranks, leaderboards, level rewards
- **[COMMUNITY_FEATURES_GUIDE.md](COMMUNITY_FEATURES_GUIDE.md)** - Karma, giveaways, events, confessions, server stats
- **[AI_CHATBOT_GUIDE.md](AI_CHATBOT_GUIDE.md)** - AI chat, memory system, personas, safety features
- **[GAMING_UTILITIES_GUIDE.md](GAMING_UTILITIES_GUIDE.md)** - D&D tools, MTG cards, dice rolling, external APIs
- **[MUSIC_PLAYBACK_GUIDE.md](MUSIC_PLAYBACK_GUIDE.md)** - Spotify integration, voice playback, queue management
- **[SPOTIFY_SETUP_GUIDE.md](SPOTIFY_SETUP_GUIDE.md)** - Detailed Spotify API setup instructions

### Developer Guides
- **[CHECK_IMPORTS_DOCUMENTATION.md](CHECK_IMPORTS_DOCUMENTATION.md)** - Import validation and dependency checking

## Run
- Start the bot from the repo root: `python -m src.bot`
- Invite the bot to your server, then use the commands above.

## Tests
- Run `python -m pytest` from the repo root to exercise the integration stub.
