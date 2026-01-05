"""
Messaging and channel helpers for Discord.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

import discord


async def send_message(channel: discord.abc.Messageable, content: str) -> discord.Message:
    return await channel.send(content)


async def send_embed(channel: discord.abc.Messageable, embed: discord.Embed) -> discord.Message:
    return await channel.send(embed=embed)


async def edit_message(message: discord.Message, content: str | None = None, embed: Optional[discord.Embed] = None):
    return await message.edit(content=content, embed=embed)


async def delete_message(message: discord.Message):
    await message.delete()


async def bulk_delete(channel: discord.TextChannel, message_ids: Iterable[int]) -> List[discord.Message]:
    messages = []
    for mid in message_ids:
        try:
            msg = await channel.fetch_message(mid)
            messages.append(msg)
        except Exception:
            continue
    if not messages:
        return []
    await channel.delete_messages(messages)
    return messages


async def pin_message(message: discord.Message):
    await message.pin()


async def unpin_message(message: discord.Message):
    await message.unpin()
