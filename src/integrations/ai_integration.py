"""
AI Chatbot Integration - Context-aware conversational AI with memory and safety features.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import discord

from discord_bot.storage_api import database_connect

# =============================
# Database Initialization
# =============================

def init_ai_database():
    """Initialize AI-related database tables."""
    conn = database_connect()
    cursor = conn.cursor()
    
    # User memory profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT NOT NULL,
            memory_type TEXT DEFAULT 'fact',
            created_at TEXT NOT NULL,
            UNIQUE(guild_id, user_id, memory_key)
        )
    """)
    
    # Server-wide lore memory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_lore_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            lore_key TEXT NOT NULL,
            lore_value TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(guild_id, lore_key)
        )
    """)
    
    # Conversation history (channel-based context)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    # AI personalities/personas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            persona_name TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            personality_traits TEXT,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(guild_id, persona_name)
        )
    """)
    
    # AI settings per guild
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_guild_settings (
            guild_id INTEGER PRIMARY KEY,
            active_persona TEXT DEFAULT 'default',
            language TEXT DEFAULT 'en',
            nsfw_filter INTEGER DEFAULT 1,
            cooldown_seconds INTEGER DEFAULT 3,
            max_context_messages INTEGER DEFAULT 10,
            allow_roleplay INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()


# Initialize database on import
init_ai_database()


# =============================
# AI Safety & Filtering
# =============================

class AIContentFilter:
    """Content filtering and safety checks for AI responses."""
    
    # Blocked patterns for NSFW and harmful content
    NSFW_PATTERNS = [
        r'\b(sex|porn|xxx|nsfw|nude|naked)\b',
        r'\b(sexual|erotic|explicit)\b',
    ]
    
    HATE_PATTERNS = [
        r'\b(kill yourself|kys)\b',
        r'\b(racial slurs|offensive terms)\b',
    ]
    
    @staticmethod
    def check_nsfw(text: str) -> Tuple[bool, str]:
        """Check if text contains NSFW content."""
        text_lower = text.lower()
        for pattern in AIContentFilter.NSFW_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, "NSFW content detected"
        return False, ""
    
    @staticmethod
    def check_hate(text: str) -> Tuple[bool, str]:
        """Check if text contains hate speech or harassment."""
        text_lower = text.lower()
        for pattern in AIContentFilter.HATE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, "Harmful content detected"
        return False, ""
    
    @staticmethod
    def check_prompt_injection(text: str) -> Tuple[bool, str]:
        """Check for prompt injection attempts."""
        injection_patterns = [
            r'ignore (previous|all) (instructions|prompts)',
            r'you are now',
            r'system:',
            r'<\|endoftext\|>',
        ]
        
        text_lower = text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, "Prompt injection detected"
        return False, ""
    
    @staticmethod
    async def filter_content(text: str, enable_nsfw_filter: bool = True) -> Tuple[bool, str]:
        """Run all safety checks on content."""
        # Check for prompt injection
        is_injection, reason = AIContentFilter.check_prompt_injection(text)
        if is_injection:
            return False, reason
        
        # Check for hate speech
        is_hate, reason = AIContentFilter.check_hate(text)
        if is_hate:
            return False, reason
        
        # Check for NSFW (if enabled)
        if enable_nsfw_filter:
            is_nsfw, reason = AIContentFilter.check_nsfw(text)
            if is_nsfw:
                return False, reason
        
        return True, ""


# =============================
# Personality Presets
# =============================

PERSONALITY_PRESETS = {
    "default": {
        "name": "Default Assistant",
        "system_prompt": "You are a helpful Discord bot assistant. Be friendly, concise, and helpful.",
        "traits": ["helpful", "friendly", "concise"]
    },
    "serious": {
        "name": "Serious Advisor",
        "system_prompt": "You are a professional and serious advisor. Provide thoughtful, well-reasoned responses.",
        "traits": ["professional", "thoughtful", "analytical"]
    },
    "casual": {
        "name": "Casual Friend",
        "system_prompt": "You are a casual, friendly companion. Use relaxed language and be supportive.",
        "traits": ["casual", "friendly", "supportive", "humorous"]
    },
    "lorekeeper": {
        "name": "Lore Keeper",
        "system_prompt": "You are a mystical lore keeper with knowledge of ancient tales and histories. Speak with wisdom and gravitas.",
        "traits": ["wise", "mystical", "knowledgeable", "eloquent"]
    },
    "dungeon_master": {
        "name": "Dungeon Master",
        "system_prompt": "You are an experienced Dungeon Master for D&D. Describe scenes vividly, guide adventures, and respond to player actions.",
        "traits": ["creative", "descriptive", "engaging", "fair"]
    }
}


# =============================
# Memory Management
# =============================

class AIMemoryManager:
    """Manage user and server-wide AI memory."""
    
    @staticmethod
    async def store_user_memory(guild_id: int, user_id: int, key: str, value: str, memory_type: str = "fact"):
        """Store a memory about a user."""
        conn = database_connect()
        cursor = conn.cursor()
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ai_user_memory (guild_id, user_id, memory_key, memory_value, memory_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guild_id, user_id, key, value, memory_type, timestamp))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    async def get_user_memories(guild_id: int, user_id: int, limit: int = 20) -> List[Dict]:
        """Retrieve memories about a user."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_key, memory_value, memory_type, created_at
            FROM ai_user_memory
            WHERE guild_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (guild_id, user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "key": row[0],
                "value": row[1],
                "type": row[2],
                "created_at": row[3]
            }
            for row in rows
        ]
    
    @staticmethod
    async def forget_user_memory(guild_id: int, user_id: int, key: str) -> bool:
        """Remove a specific memory about a user."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM ai_user_memory
            WHERE guild_id = ? AND user_id = ? AND memory_key = ?
        """, (guild_id, user_id, key))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    @staticmethod
    async def clear_user_memories(guild_id: int, user_id: int) -> int:
        """Clear all memories about a user."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM ai_user_memory
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    @staticmethod
    async def store_lore(guild_id: int, key: str, value: str, tags: Optional[List[str]] = None):
        """Store server-wide lore."""
        conn = database_connect()
        cursor = conn.cursor()
        
        timestamp = datetime.now(timezone.utc).isoformat()
        tags_str = json.dumps(tags or [])
        
        cursor.execute("""
            INSERT OR REPLACE INTO ai_lore_memory (guild_id, lore_key, lore_value, tags, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (guild_id, key, value, tags_str, timestamp))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    async def get_lore(guild_id: int, key: Optional[str] = None, tag: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Retrieve server-wide lore."""
        conn = database_connect()
        cursor = conn.cursor()
        
        if key:
            cursor.execute("""
                SELECT lore_key, lore_value, tags, created_at
                FROM ai_lore_memory
                WHERE guild_id = ? AND lore_key = ?
            """, (guild_id, key))
        elif tag:
            # Search by tag (JSON contains)
            cursor.execute("""
                SELECT lore_key, lore_value, tags, created_at
                FROM ai_lore_memory
                WHERE guild_id = ? AND tags LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (guild_id, f'%"{tag}"%', limit))
        else:
            cursor.execute("""
                SELECT lore_key, lore_value, tags, created_at
                FROM ai_lore_memory
                WHERE guild_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (guild_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "key": row[0],
                "value": row[1],
                "tags": json.loads(row[2]),
                "created_at": row[3]
            }
            for row in rows
        ]
    
    @staticmethod
    async def forget_lore(guild_id: int, key: str) -> bool:
        """Remove server-wide lore."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM ai_lore_memory
            WHERE guild_id = ? AND lore_key = ?
        """, (guild_id, key))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted


# =============================
# Conversation Context
# =============================

class ConversationContext:
    """Manage conversation history and context."""
    
    @staticmethod
    async def store_conversation(guild_id: int, channel_id: int, user_id: int, message: str, response: str):
        """Store a conversation exchange."""
        conn = database_connect()
        cursor = conn.cursor()
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT INTO ai_conversation_history (guild_id, channel_id, user_id, message, response, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guild_id, channel_id, user_id, message, response, timestamp))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    async def get_conversation_history(guild_id: int, channel_id: int, limit: int = 10) -> List[Dict]:
        """Retrieve recent conversation history for a channel."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, message, response, timestamp
            FROM ai_conversation_history
            WHERE guild_id = ? AND channel_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (guild_id, channel_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Return in chronological order (oldest first)
        return [
            {
                "user_id": row[0],
                "message": row[1],
                "response": row[2],
                "timestamp": row[3]
            }
            for row in reversed(rows)
        ]
    
    @staticmethod
    async def clear_channel_history(guild_id: int, channel_id: int) -> int:
        """Clear conversation history for a channel."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM ai_conversation_history
            WHERE guild_id = ? AND channel_id = ?
        """, (guild_id, channel_id))
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    @staticmethod
    async def summarize_conversation(history: List[Dict]) -> str:
        """Create a summary of conversation history."""
        if not history:
            return "No conversation history."
        
        summary = f"Conversation with {len(history)} exchanges:\n"
        for i, exchange in enumerate(history[-5:], 1):  # Last 5 exchanges
            summary += f"{i}. User: {exchange['message'][:50]}...\n"
        
        return summary


# =============================
# AI Guild Settings
# =============================

class AISettings:
    """Manage AI settings per guild."""
    
    @staticmethod
    async def get_settings(guild_id: int) -> Dict:
        """Get AI settings for a guild."""
        conn = database_connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT active_persona, language, nsfw_filter, cooldown_seconds, max_context_messages, allow_roleplay
            FROM ai_guild_settings
            WHERE guild_id = ?
        """, (guild_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # Return defaults
            return {
                "active_persona": "default",
                "language": "en",
                "nsfw_filter": True,
                "cooldown_seconds": 3,
                "max_context_messages": 10,
                "allow_roleplay": True
            }
        
        return {
            "active_persona": row[0],
            "language": row[1],
            "nsfw_filter": bool(row[2]),
            "cooldown_seconds": row[3],
            "max_context_messages": row[4],
            "allow_roleplay": bool(row[5])
        }
    
    @staticmethod
    async def update_setting(guild_id: int, key: str, value):
        """Update a specific AI setting."""
        conn = database_connect()
        cursor = conn.cursor()
        
        # Ensure guild has a row
        cursor.execute("""
            INSERT OR IGNORE INTO ai_guild_settings (guild_id)
            VALUES (?)
        """, (guild_id,))
        
        # Update the specific setting
        if key in ["active_persona", "language"]:
            cursor.execute(f"""
                UPDATE ai_guild_settings
                SET {key} = ?
                WHERE guild_id = ?
            """, (value, guild_id))
        elif key in ["nsfw_filter", "allow_roleplay"]:
            cursor.execute(f"""
                UPDATE ai_guild_settings
                SET {key} = ?
                WHERE guild_id = ?
            """, (1 if value else 0, guild_id))
        elif key in ["cooldown_seconds", "max_context_messages"]:
            cursor.execute(f"""
                UPDATE ai_guild_settings
                SET {key} = ?
                WHERE guild_id = ?
            """, (int(value), guild_id))
        
        conn.commit()
        conn.close()


# =============================
# AI Chat Interface
# =============================

class AIChatInterface:
    """Main interface for AI chat interactions."""
    
    def __init__(self):
        self.cooldowns: Dict[int, datetime] = {}
    
    async def check_cooldown(self, user_id: int, cooldown_seconds: int) -> Tuple[bool, float]:
        """Check if user is on cooldown."""
        if user_id in self.cooldowns:
            time_since = (datetime.now(timezone.utc) - self.cooldowns[user_id]).total_seconds()
            if time_since < cooldown_seconds:
                return False, cooldown_seconds - time_since
        return True, 0.0
    
    def set_cooldown(self, user_id: int):
        """Set cooldown for user."""
        self.cooldowns[user_id] = datetime.now(timezone.utc)
    
    async def generate_response(
        self,
        message: str,
        guild_id: int,
        channel_id: int,
        user_id: int,
        user_name: str
    ) -> str:
        """Generate AI response with context and memory."""
        # Get guild settings
        settings = await AISettings.get_settings(guild_id)
        
        # Safety checks
        is_safe, reason = await AIContentFilter.filter_content(message, settings["nsfw_filter"])
        if not is_safe:
            return f"⚠️ Message blocked: {reason}"
        
        # Get conversation context
        history = await ConversationContext.get_conversation_history(
            guild_id, channel_id, settings["max_context_messages"]
        )
        
        # Get user memories
        user_memories = await AIMemoryManager.get_user_memories(guild_id, user_id, limit=5)
        
        # Get server lore
        server_lore = await AIMemoryManager.get_lore(guild_id, limit=5)
        
        # Build context
        context = self._build_context(
            message, history, user_memories, server_lore, settings, user_name
        )
        
        # Generate response (placeholder - integrate with actual AI API)
        response = await self._call_ai_api(context, settings)
        
        # Store conversation
        await ConversationContext.store_conversation(
            guild_id, channel_id, user_id, message, response
        )
        
        return response
    
    def _build_context(
        self,
        message: str,
        history: List[Dict],
        user_memories: List[Dict],
        server_lore: List[Dict],
        settings: Dict,
        user_name: str
    ) -> str:
        """Build context string for AI."""
        # Get active personality
        persona = PERSONALITY_PRESETS.get(settings["active_persona"], PERSONALITY_PRESETS["default"])
        
        context_parts = [
            f"System: {persona['system_prompt']}",
            f"User: {user_name}",
        ]
        
        # Add user memories
        if user_memories:
            context_parts.append("\nUser Memories:")
            for mem in user_memories[:3]:
                context_parts.append(f"- {mem['key']}: {mem['value']}")
        
        # Add server lore
        if server_lore:
            context_parts.append("\nServer Lore:")
            for lore in server_lore[:3]:
                context_parts.append(f"- {lore['key']}: {lore['value']}")
        
        # Add conversation history
        if history:
            context_parts.append("\nRecent Conversation:")
            for exchange in history[-5:]:
                context_parts.append(f"User: {exchange['message']}")
                context_parts.append(f"Assistant: {exchange['response']}")
        
        context_parts.append(f"\nCurrent Message: {message}")
        
        return "\n".join(context_parts)
    
    async def _call_ai_api(self, context: str, settings: Dict) -> str:
        """
        Call AI API to generate response.
        Uses external_apis for real AI providers or falls back to placeholder.
        """
        try:
            # Try to import and use external API providers
            from integrations.external_apis import UnifiedAIProvider
            
            if UnifiedAIProvider.is_available():
                # Convert context to messages format
                messages = [
                    {"role": "system", "content": context}
                ]
                
                response = await UnifiedAIProvider.generate_response(messages, provider="auto")
                if response:
                    return response
        except Exception:
            pass
        
        # Fallback to placeholder responses
        responses = [
            "I understand. Let me help with that.",
            "That's an interesting point. Here's what I think...",
            "Based on what we've discussed, I'd suggest...",
            "I remember you mentioned something similar before.",
            "Let me think about that for a moment...",
        ]
        
        import random
        base_response = random.choice(responses)
        
        return f"{base_response}\n\n*Note: Configure AI API keys (OpenAI, Anthropic, or Google Gemini) in .env for real AI responses.*"


# Global AI chat interface
ai_chat = AIChatInterface()


# =============================
# Persona Management
# =============================

async def create_persona(guild_id: int, name: str, system_prompt: str, traits: List[str], creator_id: int) -> bool:
    """Create a custom AI persona."""
    conn = database_connect()
    cursor = conn.cursor()
    
    timestamp = datetime.now(timezone.utc).isoformat()
    traits_str = json.dumps(traits)
    
    try:
        cursor.execute("""
            INSERT INTO ai_personas (guild_id, persona_name, system_prompt, personality_traits, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guild_id, name, system_prompt, traits_str, creator_id, timestamp))
        
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


async def get_personas(guild_id: int) -> List[Dict]:
    """Get all personas for a guild."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT persona_name, system_prompt, personality_traits, created_at
        FROM ai_personas
        WHERE guild_id = ?
    """, (guild_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Include built-in personas
    personas = [
        {
            "name": name,
            "prompt": preset["system_prompt"],
            "traits": preset["traits"],
            "builtin": True
        }
        for name, preset in PERSONALITY_PRESETS.items()
    ]
    
    # Add custom personas
    for row in rows:
        personas.append({
            "name": row[0],
            "prompt": row[1],
            "traits": json.loads(row[2]),
            "builtin": False
        })
    
    return personas


async def delete_persona(guild_id: int, name: str) -> bool:
    """Delete a custom persona."""
    conn = database_connect()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM ai_personas
        WHERE guild_id = ? AND persona_name = ?
    """, (guild_id, name))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted
