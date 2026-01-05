#!/usr/bin/env python
"""Comprehensive syntax and error checker for discord_bot."""

import ast
import sys
from pathlib import Path

errors = []
warnings = []
success = []

discord_bot_dir = Path("src/discord_bot")
files = list(discord_bot_dir.glob("*.py"))

print(f"Checking {len(files)} files in discord_bot...\n")

for file in sorted(files):
    try:
        # Try to parse as AST
        content = file.read_text(encoding="utf-8")
        ast.parse(content, filename=str(file))
        
        # Try to compile
        compile(content, str(file), 'exec')
        
        success.append(file.name)
        print(f"✓ {file.name}")
        
    except SyntaxError as e:
        errors.append((file.name, f"Syntax Error: {e.msg} at line {e.lineno}"))
        print(f"✗ {file.name}: Syntax Error at line {e.lineno}")
        print(f"  {e.msg}")
        
    except Exception as e:
        errors.append((file.name, f"Error: {type(e).__name__}: {e}"))
        print(f"✗ {file.name}: {type(e).__name__}: {e}")

print("\n" + "="*60)
print(f"Results: {len(success)} OK, {len(errors)} ERRORS, {len(warnings)} WARNINGS")
print("="*60)

if errors:
    print("\nErrors found:")
    for file, error in errors:
        print(f"  {file}: {error}")
    sys.exit(1)
else:
    print("\n✅ No syntax errors found!")
    sys.exit(0)
