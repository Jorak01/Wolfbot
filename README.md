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
│  │   ├─ analytics.py         # Event/usage logging
│  │   ├─ command_handler.py   # Command registries, dispatch, cooldowns
│  │   ├─ config_store.py      # JSON-backed guild/user config
│  │   ├─ games.py             # Dice, coin, RPS, poll creation
│  │   ├─ lifecycle.py         # Startup/shutdown helpers
│  │   ├─ maintenance.py       # Backup/restore, dependency/version checks
│  │   ├─ member_roles.py      # Join/leave hooks and role assignment
│  │   ├─ messaging.py         # Message send/edit/pin helpers
│  │   ├─ moderation.py        # Kick/ban/mute/purge utilities
│  │   ├─ notifications.py     # Announcement/DM/react helpers
│  │   ├─ scheduler.py         # Task scheduling and temporary messages
│  │   ├─ security.py          # Permission helpers
│  │   ├─ storage_api.py       # SQLite, cache, HTTP fetch, retry
│  │   ├─ ui_components.py     # Embeds/buttons/dropdowns/modals helpers
│  │   └─ utils_misc.py        # Duration/UUID/url/format helpers
│  ├─ integrations/
│  │   ├─ __init__.py
│  │   ├─ spotify_integration.py  # Spotify API + voice playback with queue
│  │   └─ twitch_integration.py   # Twitch <-> Discord monitor, chat relay
│  ├─ api/                     # API client structure (currently unused)
│  └─ data/                    # Data storage directory
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

## Commands (high level)
- `!status` — stubbed status endpoint via `src/integration.py`.
- `!search <query>` — DuckDuckGo-powered search (top 5 results).
- `!imagine|!art|!image <prompt>` — ChatGPT-style prompt enhancer + OpenAI image generation. Returns an image URL.
- Twitch helpers:
  - `!uptime` — Twitch stream uptime.
  - `!live` — Show live embed if online.
  - `!twitchstats|!tstats` — Summary of viewers/peaks/follows/subs.
  - `!tchat <message>` — Relay message to Twitch chat.
  - `!followers` / `!subs` / `!streamgame` — Pull Twitch metrics.
  - `!health` — Twitch/Discord integration health check.
- Spotify integration:
  - `!spotify|!sp|!nowlistening` — Show what's currently playing on your Spotify account.
  - `!spotifysearch|!spsearch <query>` — Search for tracks on Spotify.
  - `!toptracks [timeframe]` — Show your top tracks (short/medium/long).
  - `!topartists [timeframe]` — Show your top artists (short/medium/long).
  - `!playlists|!myplaylists` — Show your Spotify playlists.
- Voice/music playback (Spotify search + Discord voice):
  - `!join|!connect` — Join your current voice channel.
  - `!leave|!disconnect|!dc` — Leave voice channel and clear queue.
  - `!play|!p <query>` — Search and play a track (auto-joins voice).
  - `!pause` — Pause current playback.
  - `!resume|!unpause` — Resume paused playback.
  - `!skip|!next|!s` — Skip current track.
  - `!stop` — Stop playback and clear queue.
  - `!loop|!repeat <mode>` — Set loop mode (off/track/queue).
  - `!volume|!vol|!v <0-100>` — Set playback volume.
  - `!queue|!q` — Display current queue with rich embed.
  - `!nowplaying|!np|!current` — Show currently playing track.
  - `!clearqueue|!cq|!clear` — Clear the queue.
  - `!remove|!rm <position>` — Remove track from queue by position.
  - `!shuffle` — Shuffle the queue.
 - Moderation/admin:
   - `!warn`, `!mute <duration>`, `!kick`, `!ban`, `!unban <user_id>`, `!purge <n>`, `!lock`, `!unlock`
   - `!reloadext`, `!shutdown` (manage_guild)
   - `!backup`, `!restore <backup_name>` (admin)
   - `!setwelcome #channel`, `!setleave #channel`
 - Fun: `!roll <expr>`, `!coin`, `!rps <choice>`, `!poll question | opt1 | opt2`
 - Notifications: `!announce <text>`, `!dm <user_id> <text>`, `!react <message_id> <emoji>`, `!tempmsg <duration> <text>`
 - HTTP utility: `!fetchjson <url>` (truncated JSON)

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

## Run
- Start the bot from the repo root: `python -m src.bot`
- Invite the bot to your server, then use the commands above.

## Tests
- Run `python -m pytest` from the repo root to exercise the integration stub.
