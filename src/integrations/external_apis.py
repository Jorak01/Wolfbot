"""
External API Integration Hub - Connects to various third-party services.
Includes AI providers, gaming APIs, economy services, and more.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import json

# =============================
# API Configuration
# =============================

@dataclass
class APIConfig:
    """Configuration for external API connections."""
    # AI Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Gaming APIs
    dnd_beyond_token: Optional[str] = None
    scryfall_enabled: bool = True  # No key needed
    
    # Media Generation
    stability_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    # Economy/Payments
    stripe_api_key: Optional[str] = None
    patreon_token: Optional[str] = None
    
    # Productivity
    github_token: Optional[str] = None
    notion_token: Optional[str] = None
    
    # Security
    perspective_api_key: Optional[str] = None
    virustotal_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Load configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            dnd_beyond_token=os.getenv('DND_BEYOND_TOKEN'),
            stability_api_key=os.getenv('STABILITY_API_KEY'),
            elevenlabs_api_key=os.getenv('ELEVENLABS_API_KEY'),
            stripe_api_key=os.getenv('STRIPE_API_KEY'),
            patreon_token=os.getenv('PATREON_TOKEN'),
            github_token=os.getenv('GITHUB_TOKEN'),
            notion_token=os.getenv('NOTION_TOKEN'),
            perspective_api_key=os.getenv('PERSPECTIVE_API_KEY'),
            virustotal_api_key=os.getenv('VIRUSTOTAL_API_KEY'),
        )


# Global API configuration
api_config = APIConfig.from_env()


# =============================
# AI Provider Integrations
# =============================

class OpenAIProvider:
    """OpenAI API integration for GPT models."""
    
    BASE_URL = "https://api.openai.com/v1"
    
    @staticmethod
    async def chat_completion(
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Optional[str]:
        """Generate chat completion using OpenAI."""
        if not api_config.openai_api_key:
            return None
        
        headers = {
            "Authorization": f"Bearer {api_config.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OpenAIProvider.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    return None
        except Exception:
            return None


class AnthropicProvider:
    """Anthropic Claude API integration."""
    
    BASE_URL = "https://api.anthropic.com/v1"
    
    @staticmethod
    async def chat_completion(
        messages: List[Dict[str, str]],
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 500
    ) -> Optional[str]:
        """Generate chat completion using Claude."""
        if not api_config.anthropic_api_key:
            return None
        
        headers = {
            "x-api-key": api_config.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # Convert messages to Claude format
        system_message = ""
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append(msg)
        
        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{AnthropicProvider.BASE_URL}/messages",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["content"][0]["text"]
                    return None
        except Exception:
            return None


class GoogleGeminiProvider:
    """Google Gemini API integration."""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    @staticmethod
    async def chat_completion(
        messages: List[Dict[str, str]],
        model: str = "gemini-pro",
        temperature: float = 0.7
    ) -> Optional[str]:
        """Generate chat completion using Gemini."""
        if not api_config.google_api_key:
            return None
        
        # Convert to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 500
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{GoogleGeminiProvider.BASE_URL}/models/{model}:generateContent?key={api_config.google_api_key}",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    return None
        except Exception:
            return None


# =============================
# Gaming API Integrations
# =============================

class ScryfallAPI:
    """Scryfall MTG card database API."""
    
    BASE_URL = "https://api.scryfall.com"
    
    @staticmethod
    async def search_card(query: str, limit: int = 5) -> List[Dict]:
        """Search for MTG cards."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ScryfallAPI.BASE_URL}/cards/search",
                    params={"q": query, "order": "name"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])[:limit]
                    return []
        except Exception:
            return []
    
    @staticmethod
    async def get_card_by_name(name: str) -> Optional[Dict]:
        """Get a specific card by exact name."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ScryfallAPI.BASE_URL}/cards/named",
                    params={"exact": name}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception:
            return None
    
    @staticmethod
    async def get_random_card() -> Optional[Dict]:
        """Get a random MTG card."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{ScryfallAPI.BASE_URL}/cards/random") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception:
            return None


class Open5eAPI:
    """Open5e D&D 5e API."""
    
    BASE_URL = "https://api.open5e.com"
    
    @staticmethod
    async def search_spells(query: str = "", level: Optional[int] = None) -> List[Dict]:
        """Search for D&D spells."""
        params = {}
        if query:
            params["search"] = query
        if level is not None:
            params["level"] = level
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{Open5eAPI.BASE_URL}/spells",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    return []
        except Exception:
            return []
    
    @staticmethod
    async def search_monsters(query: str = "", cr: Optional[str] = None) -> List[Dict]:
        """Search for D&D monsters."""
        params = {}
        if query:
            params["search"] = query
        if cr:
            params["challenge_rating"] = cr
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{Open5eAPI.BASE_URL}/monsters",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    return []
        except Exception:
            return []


# =============================
# Security API Integrations
# =============================

class PerspectiveAPI:
    """Google Perspective API for toxicity detection."""
    
    BASE_URL = "https://commentanalyzer.googleapis.com/v1alpha1"
    
    @staticmethod
    async def analyze_toxicity(text: str) -> Optional[Dict[str, float]]:
        """Analyze text for toxicity, threats, etc."""
        if not api_config.perspective_api_key:
            return None
        
        payload = {
            "comment": {"text": text},
            "requestedAttributes": {
                "TOXICITY": {},
                "SEVERE_TOXICITY": {},
                "IDENTITY_ATTACK": {},
                "INSULT": {},
                "PROFANITY": {},
                "THREAT": {}
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{PerspectiveAPI.BASE_URL}/comments:analyze?key={api_config.perspective_api_key}",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        scores = {}
                        for attr, result in data.get("attributeScores", {}).items():
                            scores[attr.lower()] = result["summaryScore"]["value"]
                        return scores
                    return None
        except Exception:
            return None


class VirusTotalAPI:
    """VirusTotal API for URL/file scanning."""
    
    BASE_URL = "https://www.virustotal.com/api/v3"
    
    @staticmethod
    async def scan_url(url: str) -> Optional[Dict]:
        """Scan a URL for malware/phishing."""
        if not api_config.virustotal_api_key:
            return None
        
        headers = {
            "x-apikey": api_config.virustotal_api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Submit URL for scanning
                async with session.post(
                    f"{VirusTotalAPI.BASE_URL}/urls",
                    headers=headers,
                    data={"url": url}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        analysis_id = data["data"]["id"]
                        
                        # Get analysis results
                        async with session.get(
                            f"{VirusTotalAPI.BASE_URL}/analyses/{analysis_id}",
                            headers=headers
                        ) as analysis_response:
                            if analysis_response.status == 200:
                                return await analysis_response.json()
                    return None
        except Exception:
            return None


# =============================
# GitHub API Integration
# =============================

class GitHubAPI:
    """GitHub API for repository information."""
    
    BASE_URL = "https://api.github.com"
    
    @staticmethod
    async def get_repo_info(owner: str, repo: str) -> Optional[Dict]:
        """Get repository information."""
        headers = {}
        if api_config.github_token:
            headers["Authorization"] = f"token {api_config.github_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GitHubAPI.BASE_URL}/repos/{owner}/{repo}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception:
            return None
    
    @staticmethod
    async def get_latest_release(owner: str, repo: str) -> Optional[Dict]:
        """Get latest release information."""
        headers = {}
        if api_config.github_token:
            headers["Authorization"] = f"token {api_config.github_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GitHubAPI.BASE_URL}/repos/{owner}/{repo}/releases/latest",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception:
            return None


# =============================
# Unified AI Provider Interface
# =============================

class UnifiedAIProvider:
    """Unified interface for multiple AI providers."""
    
    @staticmethod
    async def generate_response(
        messages: List[Dict[str, str]],
        provider: str = "auto",
        **kwargs
    ) -> Optional[str]:
        """
        Generate AI response using specified or available provider.
        Provider options: 'openai', 'anthropic', 'google', 'auto'
        """
        if provider == "auto":
            # Try providers in order of preference
            if api_config.openai_api_key:
                provider = "openai"
            elif api_config.anthropic_api_key:
                provider = "anthropic"
            elif api_config.google_api_key:
                provider = "google"
            else:
                return None
        
        if provider == "openai":
            return await OpenAIProvider.chat_completion(messages, **kwargs)
        elif provider == "anthropic":
            return await AnthropicProvider.chat_completion(messages, **kwargs)
        elif provider == "google":
            return await GoogleGeminiProvider.chat_completion(messages, **kwargs)
        
        return None
    
    @staticmethod
    def is_available() -> bool:
        """Check if any AI provider is configured."""
        return any([
            api_config.openai_api_key,
            api_config.anthropic_api_key,
            api_config.google_api_key
        ])
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of configured providers."""
        providers = []
        if api_config.openai_api_key:
            providers.append("openai")
        if api_config.anthropic_api_key:
            providers.append("anthropic")
        if api_config.google_api_key:
            providers.append("google")
        return providers


# =============================
# API Status Checker
# =============================

class APIStatusChecker:
    """Check status and availability of all integrated APIs."""
    
    @staticmethod
    async def check_all() -> Dict[str, Any]:
        """Check status of all configured APIs."""
        status = {
            "ai_providers": {
                "openai": bool(api_config.openai_api_key),
                "anthropic": bool(api_config.anthropic_api_key),
                "google": bool(api_config.google_api_key),
            },
            "gaming": {
                "scryfall": True,  # No key needed
                "open5e": True,  # No key needed
                "dnd_beyond": bool(api_config.dnd_beyond_token),
            },
            "security": {
                "perspective": bool(api_config.perspective_api_key),
                "virustotal": bool(api_config.virustotal_api_key),
            },
            "productivity": {
                "github": bool(api_config.github_token),
                "notion": bool(api_config.notion_token),
            },
            "media": {
                "stability": bool(api_config.stability_api_key),
                "elevenlabs": bool(api_config.elevenlabs_api_key),
            }
        }
        return status
    
    @staticmethod
    def format_status_message(status: Dict) -> str:
        """Format status check into readable message."""
        lines = ["**API Status:**\n"]
        
        for category, apis in status.items():
            lines.append(f"\n**{category.replace('_', ' ').title()}:**")
            for api_name, available in apis.items():
                emoji = "✅" if available else "❌"
                lines.append(f"{emoji} {api_name.title()}")
        
        return "\n".join(lines)
