import os

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("API_KEY", "")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10.0"))
API_TOKENS_RAW = os.getenv("API_TOKENS", "")

# OpenAI / ChatGPT-style settings for text + image generation.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")

# Search defaults.
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "5"))

# Twitch settings.
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN", "")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN", "")
TWITCH_BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID", "")
TWITCH_CHANNEL_NAME = os.getenv("TWITCH_CHANNEL_NAME", "")
TWITCH_LIVE_ROLE_ID = int(os.getenv("TWITCH_LIVE_ROLE_ID", "0") or 0)
TWITCH_GUILD_ID = int(os.getenv("TWITCH_GUILD_ID", "0") or 0)
TWITCH_ANNOUNCE_CHANNEL_ID = int(os.getenv("TWITCH_ANNOUNCE_CHANNEL_ID", "0") or 0)
TWITCH_CLIPS_CHANNEL_ID = int(os.getenv("TWITCH_CLIPS_CHANNEL_ID", "0") or 0)
TWITCH_REMINDER_CHANNEL_ID = int(os.getenv("TWITCH_REMINDER_CHANNEL_ID", "0") or 0)
TWITCH_MONITOR_INTERVAL = int(os.getenv("TWITCH_MONITOR_INTERVAL", "60") or 60)
TWITCH_CHAT_ENABLED = os.getenv("TWITCH_CHAT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
TWITCH_EVENT_LOG_CHANNEL_ID = int(os.getenv("TWITCH_EVENT_LOG_CHANNEL_ID", "0") or 0)


def require_token() -> str:
    """Return the bot token or raise if missing."""
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set")
    return DISCORD_TOKEN
