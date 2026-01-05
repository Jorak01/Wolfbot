# API Manager - Centralized API Management Guide

## Overview
`src/api_manager.py` provides a centralized system for managing all API tokens, configurations, and clients in one place.

## Quick Start

### 1. Import the Manager
```python
from api_manager import api_manager, get_token, require_token
```

### 2. Get API Tokens
```python
# Get a token (returns None if not configured)
openai_key = api_manager.get_token("openai")

# Get a required token (raises error if not configured)
discord_token = api_manager.require_token("discord")

# Get with fallback
token = api_manager.get_token("my_api", fallback="default_token")
```

### 3. Get Full API Configuration
```python
# Get complete configuration
config = api_manager.get_api_config("twitch")
if config:
    print(f"Token: {config.token}")
    print(f"Client ID: {config.client_id}")
    print(f"Channel: {config.extra['channel_name']}")
```

### 4. Register Custom APIs
```python
# Register a new API
api_manager.register_api(
    "my_service",
    token="your_token_here",
    base_url="https://api.example.com",
    timeout=15.0,
    extra={"version": "v1", "region": "us-east"}
)

# Use it
token = api_manager.get_token("my_service")
base_url = api_manager.get_base_url("my_service")
version = api_manager.get_extra("my_service", "version")
```

### 5. Register API Clients
```python
# Initialize and register a client
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=api_manager.get_token("openai"))
api_manager.register_client("openai", openai_client)

# Get the client from anywhere
client = api_manager.get_client("openai")
```

## Pre-Configured APIs

### Discord
```python
token = api_manager.get_token("discord")
# Or use the convenience function
token = require_token("discord")
```

### OpenAI
```python
config = api_manager.get_api_config("openai")
api_key = config.api_key
model = config.extra["model"]  # gpt-4o-mini
image_model = config.extra["image_model"]  # dall-e-3
```

### Twitch
```python
config = api_manager.get_api_config("twitch")
client_id = config.client_id
client_secret = config.client_secret
token = config.token
broadcaster_id = config.extra["broadcaster_id"]
channel_name = config.extra["channel_name"]
```

### Generic API
```python
config = api_manager.get_api_config("generic")
api_key = config.api_key
base_url = config.base_url
```

## Environment Variables

Set these in your `.env` file:

```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token

# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
OPENAI_MODEL=gpt-4o-mini
OPENAI_IMAGE_MODEL=dall-e-3

# Twitch
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
TWITCH_ACCESS_TOKEN=your_access_token
TWITCH_REFRESH_TOKEN=your_refresh_token
TWITCH_BROADCASTER_ID=your_broadcaster_id
TWITCH_CHANNEL_NAME=your_channel_name
TWITCH_GUILD_ID=123456789
TWITCH_LIVE_ROLE_ID=123456789
TWITCH_ANNOUNCE_CHANNEL_ID=123456789
TWITCH_MONITOR_INTERVAL=60
TWITCH_CHAT_ENABLED=true

# Generic API
API_KEY=your_generic_api_key
API_BASE_URL=https://api.example.com
API_TIMEOUT=10.0

# Additional APIs (semicolon-separated)
API_TOKENS=service1=token1;service2=token2;service3=token3
```

## Usage Examples

### Example 1: Using in Discord Bot Commands
```python
from discord.ext import commands
from api_manager import api_manager

@bot.command()
async def check_apis(ctx: commands.Context):
    """Check which APIs are configured."""
    status = api_manager.list_apis()
    lines = []
    for api_name, is_configured in status.items():
        status_icon = "✅" if is_configured else "❌"
        lines.append(f"{status_icon} {api_name}")
    await ctx.send("\n".join(lines))
```

### Example 2: Using in API Services
```python
from api_manager import api_manager
import httpx

async def fetch_data_from_custom_api():
    config = api_manager.get_api_config("my_service")
    if not config:
        return {"error": "API not configured"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{config.base_url}/endpoint",
            headers={"Authorization": f"Bearer {config.auth_token}"},
            timeout=config.timeout
        )
        return response.json()
```

### Example 3: Initializing OpenAI Client
```python
from openai import AsyncOpenAI
from api_manager import api_manager

def init_openai():
    config = api_manager.get_api_config("openai")
    if not config or not config.api_key:
        return None
    
    client = AsyncOpenAI(
        api_key=config.api_key,
        base_url=config.base_url
    )
    api_manager.register_client("openai", client)
    return client

# Use it
client = init_openai()
if client:
    # Client is now available anywhere via:
    # api_manager.get_client("openai")
    pass
```

### Example 4: Dynamic API Registration
```python
from api_manager import api_manager

# Register a new third-party API at runtime
def add_weather_api(api_key: str):
    api_manager.register_api(
        "weather",
        api_key=api_key,
        base_url="https://api.weatherapi.com/v1",
        extra={
            "default_location": "New York",
            "units": "imperial"
        }
    )

# Use it
add_weather_api("your_weather_api_key")
weather_key = api_manager.get_token("weather")
location = api_manager.get_extra("weather", "default_location")
```

## API Configuration Object

The `APIConfig` dataclass contains:

```python
@dataclass
class APIConfig:
    name: str                      # Unique identifier
    token: Optional[str]           # Authentication token
    api_key: Optional[str]         # Alternative to token
    client_id: Optional[str]       # OAuth client ID
    client_secret: Optional[str]   # OAuth client secret
    base_url: Optional[str]        # API base URL
    timeout: float                 # Request timeout (default: 10.0)
    extra: Dict[str, Any]          # Additional configuration
    
    @property
    def auth_token(self) -> Optional[str]:
        """Returns token or api_key, whichever is set"""
```

## Manager Methods Reference

| Method | Description | Example |
|--------|-------------|---------|
| `register_api()` | Register/update an API | `api_manager.register_api("service", token="abc")` |
| `get_api_config()` | Get full config | `config = api_manager.get_api_config("openai")` |
| `get_token()` | Get auth token | `token = api_manager.get_token("discord")` |
| `get_client_id()` | Get OAuth client ID | `id = api_manager.get_client_id("twitch")` |
| `get_client_secret()` | Get OAuth secret | `secret = api_manager.get_client_secret("twitch")` |
| `get_base_url()` | Get API base URL | `url = api_manager.get_base_url("generic")` |
| `get_extra()` | Get extra config value | `val = api_manager.get_extra("openai", "model")` |
| `register_client()` | Register initialized client | `api_manager.register_client("openai", client)` |
| `get_client()` | Get registered client | `client = api_manager.get_client("openai")` |
| `is_configured()` | Check if API is set up | `if api_manager.is_configured("twitch"):` |
| `list_apis()` | Get all APIs and status | `apis = api_manager.list_apis()` |
| `require_token()` | Get token or raise error | `token = api_manager.require_token("discord")` |

## Backward Compatibility

For existing code, these convenience functions are available:

```python
from api_manager import get_token, require_token, get_api_config, is_api_configured

# These work exactly like the old system:
token = get_token("openai")
discord_token = require_token("discord")
config = get_api_config("twitch")
is_setup = is_api_configured("generic")
```

## Migration from Old System

### Before (using config.py):
```python
from config import OPENAI_API_KEY, TWITCH_CLIENT_ID

if OPENAI_API_KEY:
    # use key
    pass
```

### After (using api_manager):
```python
from api_manager import api_manager

if api_manager.is_configured("openai"):
    key = api_manager.get_token("openai")
    # use key
```

## Best Practices

1. **Always check if configured** before using an API:
   ```python
   if api_manager.is_configured("openai"):
       # safe to use
   ```

2. **Use `require_token()` for critical APIs**:
   ```python
   # This will raise an error if not set, preventing silent failures
   token = api_manager.require_token("discord")
   ```

3. **Register clients early** in your app startup:
   ```python
   # In your bot's on_ready() or main()
   from openai import AsyncOpenAI
   
   if api_manager.is_configured("openai"):
       client = AsyncOpenAI(api_key=api_manager.get_token("openai"))
       api_manager.register_client("openai", client)
   ```

4. **Use extra config for API-specific settings**:
   ```python
   # Instead of separate variables
   model = api_manager.get_extra("openai", "model", "gpt-4o-mini")
   ```

## Benefits

✅ **Single Source of Truth** - All API configs in one place  
✅ **Type-Safe** - Structured APIConfig dataclass  
✅ **Flexible** - Support for tokens, OAuth, custom configs  
✅ **Discoverable** - Easy to see what APIs are available  
✅ **Testable** - Mock or replace APIs easily  
✅ **Extensible** - Add new APIs at runtime  
✅ **Backward Compatible** - Works with existing code  

## Status
✅ **READY TO USE** - All features implemented and tested
