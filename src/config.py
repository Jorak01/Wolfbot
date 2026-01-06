"""
Configuration module - Now uses api_manager as single source of truth.
This file provides backward compatibility for existing code.
"""

import os
try:
    from src.api_manager import api_manager
except ImportError:
    from api_manager import api_manager

__all__ = [
    "require_token",
    "DISCORD_TOKEN",
    "API_BASE_URL",
    "API_KEY",
    "API_TIMEOUT",
    "API_TOKENS_RAW",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "OPENAI_IMAGE_MODEL",
    "SEARCH_MAX_RESULTS",
    "TWITCH_CLIENT_ID",
    "TWITCH_CLIENT_SECRET",
    "TWITCH_ACCESS_TOKEN",
    "TWITCH_REFRESH_TOKEN",
    "TWITCH_BROADCASTER_ID",
    "TWITCH_CHANNEL_NAME",
    "TWITCH_LIVE_ROLE_ID",
    "TWITCH_GUILD_ID",
    "TWITCH_ANNOUNCE_CHANNEL_ID",
    "TWITCH_CLIPS_CHANNEL_ID",
    "TWITCH_REMINDER_CHANNEL_ID",
    "TWITCH_MONITOR_INTERVAL",
    "TWITCH_CHAT_ENABLED",
    "TWITCH_EVENT_LOG_CHANNEL_ID",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPOTIFY_REDIRECT_URI",
    "SPOTIFY_REFRESH_TOKEN",
]

# Backward compatibility - expose values from api_manager
DISCORD_TOKEN = api_manager.get_token("discord") or ""
API_BASE_URL = api_manager.get_base_url("generic") or ""
API_KEY = api_manager.get_token("generic") or ""
_generic_config = api_manager.get_api_config("generic")
API_TIMEOUT = _generic_config.timeout if _generic_config else 10.0
API_TOKENS_RAW = os.getenv("API_TOKENS", "")

# OpenAI settings
_openai_config = api_manager.get_api_config("openai")
OPENAI_API_KEY = _openai_config.api_key if _openai_config else ""
OPENAI_BASE_URL = _openai_config.base_url if _openai_config else ""
OPENAI_MODEL = api_manager.get_extra("openai", "model", "gpt-4o-mini")
OPENAI_IMAGE_MODEL = api_manager.get_extra("openai", "image_model", "dall-e-3")

# Search defaults
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))

# Twitch settings
_twitch_config = api_manager.get_api_config("twitch")
TWITCH_CLIENT_ID = _twitch_config.client_id if _twitch_config else ""
TWITCH_CLIENT_SECRET = _twitch_config.client_secret if _twitch_config else ""
TWITCH_ACCESS_TOKEN = _twitch_config.token if _twitch_config else ""
TWITCH_REFRESH_TOKEN = api_manager.get_extra("twitch", "refresh_token", "")
TWITCH_BROADCASTER_ID = api_manager.get_extra("twitch", "broadcaster_id", "")
TWITCH_CHANNEL_NAME = api_manager.get_extra("twitch", "channel_name", "")
TWITCH_LIVE_ROLE_ID = api_manager.get_extra("twitch", "live_role_id", 0)
TWITCH_GUILD_ID = api_manager.get_extra("twitch", "guild_id", 0)
TWITCH_ANNOUNCE_CHANNEL_ID = api_manager.get_extra("twitch", "announce_channel_id", 0)
TWITCH_CLIPS_CHANNEL_ID = api_manager.get_extra("twitch", "clips_channel_id", 0)
TWITCH_REMINDER_CHANNEL_ID = api_manager.get_extra("twitch", "reminder_channel_id", 0)
TWITCH_MONITOR_INTERVAL = api_manager.get_extra("twitch", "monitor_interval", 60)
TWITCH_CHAT_ENABLED = api_manager.get_extra("twitch", "chat_enabled", False)
TWITCH_EVENT_LOG_CHANNEL_ID = api_manager.get_extra("twitch", "event_log_channel_id", 0)


# Spotify settings
_spotify_config = api_manager.get_api_config("spotify")
SPOTIFY_CLIENT_ID = _spotify_config.client_id if _spotify_config else ""
SPOTIFY_CLIENT_SECRET = _spotify_config.client_secret if _spotify_config else ""
SPOTIFY_REDIRECT_URI = api_manager.get_extra("spotify", "redirect_uri", "http://localhost:8888/callback")
SPOTIFY_REFRESH_TOKEN = api_manager.get_extra("spotify", "refresh_token", "")


def require_token() -> str:
    """Return the bot token or raise if missing."""
    return api_manager.require_token("discord")
