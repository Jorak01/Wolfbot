# Wolfbot Starter

Baseline Discord bot structure with integration logic separated from the Discord wiring. Uses `discord.py` with a simple `!status` command that pulls from `src/integration.py`.

## Layout
```
.
├─ src/
│  ├─ bot.py            # Discord entrypoint
│  ├─ config.py         # Env loading and token validation
│  ├─ integration.py    # External service / business logic
│  └─ api/              # Outbound API client(s)
│     ├─ __init__.py    # Centralized API entrypoint and shared instances
│     ├─ client.py      # HTTP client wrapper
│     ├─ services.py    # High-level API calls (per-endpoint functions)
│     ├─ registry.py    # Register and dispatch API calls by name
│     └─ tokens.py      # Token registry parsed from env
│  └─ __init__.py
├─ tests/
│  └─ test_integration.py
├─ requirements.txt
└─ .gitignore
```

## Setup
1) Create and activate a venv (recommended):
   - Windows: `python -m venv .venv && .\.venv\Scripts\activate`
   - Unix: `python -m venv .venv && source .venv/bin/activate`
2) Install deps: `pip install -r requirements.txt`
3) Create `.env` with your bot token:
```
DISCORD_TOKEN=your_bot_token_here
API_BASE_URL=https://api.example.com
API_KEY=your_optional_api_key
API_TIMEOUT=10.0
# Optional: multiple per-service tokens (e.g., "status=tokenA;service2=tokenB")
API_TOKENS=status=tokenA;service2=tokenB
```

## Run
- Start the bot from the repo root: `python -m src.bot`
- Use `!status` in any server where the bot is invited to see the stub integration response.

## Tests
- Run `pytest` from the repo root to exercise the integration stub.

## Next steps
- Replace `get_status` in `src/integration.py` with real API calls or business logic.
- Add more commands or cogs in `src/bot.py` while keeping integrations isolated in their own module(s).
