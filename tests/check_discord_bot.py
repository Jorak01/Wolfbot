#!/usr/bin/env python
"""Check all discord_bot modules for errors."""

import sys
import importlib
import traceback

sys.path.insert(0, 'src')

modules = [
    'discord_bot.analytics',
    'discord_bot.audio',
    'discord_bot.command_handler',
    'discord_bot.config_store',
    'discord_bot.games',
    'discord_bot.lifecycle',
    'discord_bot.maintenance',
    'discord_bot.member_roles',
    'discord_bot.messaging',
    'discord_bot.moderation',
    'discord_bot.notifications',
    'discord_bot.scheduler',
    'discord_bot.security',
    'discord_bot.storage_api',
    'discord_bot.ui_components',
    'discord_bot.utils_misc',
]

errors = []
success = []

for module_name in modules:
    try:
        module = importlib.import_module(module_name)
        success.append(module_name)
        print(f"✓ {module_name}")
    except Exception as e:
        errors.append((module_name, e))
        print(f"✗ {module_name}")
        print(f"  Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        print()

print("\n" + "="*60)
print(f"Summary: {len(success)} OK, {len(errors)} ERRORS")
print("="*60)

if errors:
    print("\nErrors found:")
    for module_name, error in errors:
        print(f"  - {module_name}: {type(error).__name__}: {error}")
    sys.exit(1)
else:
    print("\nAll modules loaded successfully!")
    sys.exit(0)
