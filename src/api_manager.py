"""
Centralized API Management System
===================================
Single source of truth for all API tokens, configurations, and clients.

Usage:
    from api_manager import api_manager
    
    # Get tokens
    token = api_manager.get_token("openai")
    
    # Get API configurations
    config = api_manager.get_api_config("twitch")
    
    # Get initialized clients
    client = api_manager.get_client("openai")
    
    # Register custom APIs
    api_manager.register_api("my_service", token="abc123", base_url="https://api.example.com")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class APIConfig:
    """Configuration for a single API service."""
    name: str
    token: Optional[str] = None
    api_key: Optional[str] = None  # Alternative to token
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    base_url: Optional[str] = None
    timeout: float = 10.0
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def auth_token(self) -> Optional[str]:
        """Get the primary authentication token (token or api_key)."""
        return self.token or self.api_key
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key, self.extra.get(key, default))


class APIManager:
    """
    Centralized manager for all API configurations and tokens.
    """
    
    def __init__(self):
        self._apis: Dict[str, APIConfig] = {}
        self._clients: Dict[str, Any] = {}
        self._load_default_apis()
    
    @staticmethod
    def _safe_int(value: str, default: int = 0) -> int:
        """Safely convert string to int, returning default if conversion fails."""
        try:
            # Check if value looks like a placeholder
            if not value or any(char.isalpha() for char in value.replace("_", "")):
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _load_default_apis(self):
        """Load all APIs from environment variables."""
        
        # Discord Bot
        self.register_api(
            "discord",
            token=os.getenv("DISCORD_TOKEN", ""),
            extra={
                "required": True,
                "description": "Discord Bot Token"
            }
        )
        
        # OpenAI / ChatGPT
        self.register_api(
            "openai",
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", "").rstrip("/"),
            extra={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "image_model": os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3"),
                "description": "OpenAI API for ChatGPT and DALL-E"
            }
        )
        
        # Twitch
        self.register_api(
            "twitch",
            client_id=os.getenv("TWITCH_CLIENT_ID", ""),
            client_secret=os.getenv("TWITCH_CLIENT_SECRET", ""),
            token=os.getenv("TWITCH_ACCESS_TOKEN", ""),
            extra={
                "refresh_token": os.getenv("TWITCH_REFRESH_TOKEN", ""),
                "broadcaster_id": os.getenv("TWITCH_BROADCASTER_ID", ""),
                "channel_name": os.getenv("TWITCH_CHANNEL_NAME", ""),
                "guild_id": self._safe_int(os.getenv("TWITCH_GUILD_ID", "0"), 0),
                "live_role_id": self._safe_int(os.getenv("TWITCH_LIVE_ROLE_ID", "0"), 0),
                "announce_channel_id": self._safe_int(os.getenv("TWITCH_ANNOUNCE_CHANNEL_ID", "0"), 0),
                "clips_channel_id": self._safe_int(os.getenv("TWITCH_CLIPS_CHANNEL_ID", "0"), 0),
                "reminder_channel_id": self._safe_int(os.getenv("TWITCH_REMINDER_CHANNEL_ID", "0"), 0),
                "event_log_channel_id": self._safe_int(os.getenv("TWITCH_EVENT_LOG_CHANNEL_ID", "0"), 0),
                "monitor_interval": self._safe_int(os.getenv("TWITCH_MONITOR_INTERVAL", "60"), 60),
                "chat_enabled": os.getenv("TWITCH_CHAT_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
                "description": "Twitch API and Integration Settings"
            }
        )
        
        # Generic API (for custom endpoints)
        self.register_api(
            "generic",
            api_key=os.getenv("API_KEY", ""),
            base_url=os.getenv("API_BASE_URL", "").rstrip("/"),
            timeout=float(os.getenv("API_TIMEOUT", "10.0")),
            extra={
                "description": "Generic API endpoint"
            }
        )
        
        # Parse additional tokens from API_TOKENS environment variable
        # Format: "service1=token1;service2=token2"
        api_tokens_raw = os.getenv("API_TOKENS", "")
        if api_tokens_raw:
            for chunk in api_tokens_raw.split(";"):
                if not chunk.strip() or "=" not in chunk:
                    continue
                name, token = chunk.split("=", 1)
                name, token = name.strip(), token.strip()
                if name and token:
                    # Only register if not already registered
                    if name not in self._apis:
                        self.register_api(name, token=token)
    
    def register_api(
        self,
        name: str,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        extra: Optional[Dict[str, Any]] = None
    ) -> APIConfig:
        """
        Register a new API or update existing one.
        
        Args:
            name: Unique identifier for the API
            token: Authentication token
            api_key: Alternative authentication key
            client_id: OAuth client ID
            client_secret: OAuth client secret
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            extra: Additional configuration data
            
        Returns:
            The registered APIConfig
        """
        config = APIConfig(
            name=name,
            token=token,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            timeout=timeout,
            extra=extra or {}
        )
        self._apis[name] = config
        return config
    
    def get_api_config(self, name: str) -> Optional[APIConfig]:
        """Get the configuration for an API by name."""
        return self._apis.get(name)
    
    def get_token(self, name: str, fallback: Optional[str] = None) -> Optional[str]:
        """
        Get an authentication token by API name.
        
        Args:
            name: API name
            fallback: Optional fallback value if not found
            
        Returns:
            The token string or None
        """
        config = self._apis.get(name)
        if config and config.auth_token:
            return config.auth_token
        return fallback
    
    def get_client_id(self, name: str) -> Optional[str]:
        """Get OAuth client ID for an API."""
        config = self._apis.get(name)
        return config.client_id if config else None
    
    def get_client_secret(self, name: str) -> Optional[str]:
        """Get OAuth client secret for an API."""
        config = self._apis.get(name)
        return config.client_secret if config else None
    
    def get_base_url(self, name: str) -> Optional[str]:
        """Get base URL for an API."""
        config = self._apis.get(name)
        return config.base_url if config else None
    
    def get_extra(self, name: str, key: str, default: Any = None) -> Any:
        """Get extra configuration value for an API."""
        config = self._apis.get(name)
        if not config:
            return default
        return config.extra.get(key, default)
    
    def register_client(self, name: str, client: Any):
        """Register an initialized API client."""
        self._clients[name] = client
    
    def get_client(self, name: str) -> Optional[Any]:
        """Get a registered API client."""
        return self._clients.get(name)
    
    def is_configured(self, name: str) -> bool:
        """Check if an API is configured (has at least a token/key)."""
        config = self._apis.get(name)
        if not config:
            return False
        return bool(config.auth_token or config.client_id)
    
    def list_apis(self) -> Dict[str, bool]:
        """List all registered APIs and their configuration status."""
        return {name: self.is_configured(name) for name in self._apis.keys()}
    
    def get_all_configs(self) -> Dict[str, APIConfig]:
        """Get all API configurations."""
        return dict(self._apis)
    
    def require_token(self, name: str) -> str:
        """
        Get a token or raise an error if not configured.
        
        Args:
            name: API name
            
        Returns:
            The token string
            
        Raises:
            RuntimeError: If the token is not configured
        """
        token = self.get_token(name)
        if not token:
            raise RuntimeError(f"{name} token is not configured")
        return token


# Global singleton instance
api_manager = APIManager()


# Convenience functions for backward compatibility
def get_token(name: str, fallback: Optional[str] = None) -> Optional[str]:
    """Get an API token by name."""
    return api_manager.get_token(name, fallback)


def get_api_config(name: str) -> Optional[APIConfig]:
    """Get API configuration by name."""
    return api_manager.get_api_config(name)


def require_token(name: str = "discord") -> str:
    """Get a required token or raise error."""
    return api_manager.require_token(name)


def is_api_configured(name: str) -> bool:
    """Check if an API is configured."""
    return api_manager.is_configured(name)
