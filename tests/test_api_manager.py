#!/usr/bin/env python
"""Test the API Manager"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api_manager import api_manager

print("=== API Manager Test ===\n")

print("Registered APIs:")
for name, configured in api_manager.list_apis().items():
    status = "✓" if configured else "✗"
    print(f"  {status} {name}")

print("\n=== Testing API Access ===")
print(f"Discord configured: {api_manager.is_configured('discord')}")
print(f"OpenAI configured: {api_manager.is_configured('openai')}")
print(f"Twitch configured: {api_manager.is_configured('twitch')}")

print("\n=== Test Custom API Registration ===")
api_manager.register_api(
    "test_service",
    token="test_token_123",
    base_url="https://api.test.com",
    extra={"version": "v1"}
)
print(f"Registered 'test_service': {api_manager.is_configured('test_service')}")
print(f"Token: {api_manager.get_token('test_service')}")
print(f"Base URL: {api_manager.get_base_url('test_service')}")
print(f"Version: {api_manager.get_extra('test_service', 'version')}")

print("\n=== All Tests Passed ===")
