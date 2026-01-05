#!/usr/bin/env python
"""Comprehensive validation of all discord_bot modules."""

import sys
sys.path.insert(0, 'src')

files = [
    "analytics", "audio", "command_handler", "config_store", 
    "games", "lifecycle", "maintenance", "member_roles",
    "messaging", "moderation", "notifications", "scheduler",
    "security", "storage_api", "ui_components", "utils_misc"
]

issues = []
success = []

for fname in files:
    try:
        mod = __import__(f"discord_bot.{fname}", fromlist=[fname])
        
        # Check if module has __all__ and all exports are available
        if hasattr(mod, "__all__"):
            for name in mod.__all__:
                if not hasattr(mod, name):
                    issues.append(f"{fname}: Missing exported name '{name}' in __all__")
        
        success.append(fname)
        print(f"✓ {fname}")
        
    except Exception as e:
        issues.append(f"{fname}: {type(e).__name__}: {e}")
        print(f"✗ {fname}: {e}")

print("\n" + "="*60)
print(f"Validation: {len(success)} OK, {len(issues)} issues")
print("="*60)

if issues:
    print("\nIssues found:")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)
else:
    print("\n✓ All modules validated - no issues found")
    sys.exit(0)
