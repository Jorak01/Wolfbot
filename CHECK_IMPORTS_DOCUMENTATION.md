# check_imports.py Documentation

## Overview
The `scripts/check_imports.py` module automatically discovers, validates, and manages Python package dependencies for the Wolfbot project.

## Functionality

### What It Does
1. **Discovers Imports**: Scans all `.py` files in the project to find imported modules
2. **Filters Third-Party Packages**: Distinguishes between:
   - Standard library modules (excluded)
   - Local project modules (excluded)
   - Third-party packages (tracked)
3. **Updates requirements.txt**: Automatically adds newly discovered packages
4. **Installs Missing Packages**: Attempts to install any missing dependencies

### When It Runs
The function is called automatically when the bot starts, in the `on_ready()` event handler in `src/bot.py`:

```python
@bot.event
async def on_ready():
    check_imports_main()  # Runs package verification
    await lifecycle.on_ready(bot, twitch)
```

## Package Detection

### Third-Party Packages Detected
The script correctly identifies these third-party packages used in the project:
- `discord.py` - Discord API wrapper
- `python-dotenv` - Environment variable management
- `httpx` - HTTP client
- `openai` - OpenAI API client
- `pytest` / `pytest-asyncio` - Testing frameworks
- `duckduckgo-search` - Web search functionality
- `yt-dlp` - YouTube/media downloading
- `websockets` - WebSocket support

### Local Modules Excluded
These are correctly identified as local project modules (not third-party):
- `config` (src/config.py)
- `integration` (src/integration.py)
- `tokens` (src/tokens.py)
- `discord_bot` (src/discord_bot/)
- `api` (src/api/)
- `integrations` (src/integrations/)

### Package Name Mapping
The script handles module-to-package name mappings:
```python
PACKAGE_MAP = {
    "discord": "discord.py",
    "dotenv": "python-dotenv",
    "duckduckgo_search": "duckduckgo-search",
    "yt_dlp": "yt-dlp",
}
```

## Key Features

### 1. Smart Filtering
```python
def _filter_third_party(modules: Iterable[str]) -> Set[str]:
    # Excludes:
    # - Standard library modules
    # - Local project modules (both .py files and directories)
    # - Project utility modules (src, scripts)
```

### 2. Automatic Discovery
- Uses AST parsing to find all import statements
- Handles both `import module` and `from module import ...` syntax
- Skips relative imports (they're local by definition)

### 3. Safe Installation
- Checks if packages are already installed before attempting installation
- Uses `subprocess.run()` with `check=False` to avoid crashes
- Provides clear output about what was installed

## Output Example

```
Discovered 36 total modules
Found 7 third-party modules: ['discord', 'dotenv', 'duckduckgo_search', 'httpx', 'openai', 'pytest', 'yt_dlp']
Mapped to 7 packages: ['discord.py', 'duckduckgo-search', 'httpx', 'openai', 'pytest', 'python-dotenv', 'yt-dlp']
No new packages to add to requirements.txt
All required packages are already installed.
```

## Manual Usage

Run the script directly:
```bash
python scripts/check_imports.py
```

Or import and call:
```python
from scripts.check_imports import main as check_imports_main
check_imports_main()
```

## Fixed Issues

### Previous Bug (Now Fixed)
**Issue**: Local modules (`config`, `integration`, `tokens`) were being treated as third-party packages and attempted to be installed from PyPI.

**Root Cause**: The filter only checked for directories under `src/`, not individual `.py` files.

**Fix**: Updated `_filter_third_party()` to check both:
```python
local_dir = ROOT_DIR / "src" / mod
local_file = ROOT_DIR / "src" / f"{mod}.py"
if local_dir.exists() or local_file.exists():
    continue  # Skip local modules
```

## Status
✅ **WORKING CORRECTLY** - All imports are properly detected and categorized
