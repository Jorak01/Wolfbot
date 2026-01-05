import os

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("API_KEY", "")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10.0"))
API_TOKENS_RAW = os.getenv("API_TOKENS", "")


def require_token() -> str:
    """Return the bot token or raise if missing."""
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set")
    return DISCORD_TOKEN
