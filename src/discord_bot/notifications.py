"""
Notifications and alerts utilities.
"""

from __future__ import annotations

import discord


async def send_announcement(channel: discord.abc.Messageable, content: str):
    return await channel.send(content)


def mention_role(role_id: int) -> str:
    return f"<@&{role_id}>"


async def notify_user(bot: discord.Client, user_id: int, content: str):
    user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    if not user:
        return None
    try:
        return await user.send(content)
    except Exception:
        return None


async def react_to_message(message: discord.Message, emoji: str):
    await message.add_reaction(emoji)
