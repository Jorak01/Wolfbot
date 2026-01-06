"""
Enhanced welcome and farewell message system with embeds, images, and buttons.
"""

from __future__ import annotations

from typing import Optional
import discord


async def create_welcome_embed(
    member: discord.Member,
    custom_message: Optional[str] = None,
    image_url: Optional[str] = None
) -> discord.Embed:
    """Create a welcome embed with custom styling."""
    embed = discord.Embed(
        title=f"Welcome to {member.guild.name}! 🎉",
        description=custom_message or f"Hey {member.mention}, welcome to the server! We're glad to have you here!",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Member Count", value=f"You're member #{member.guild.member_count}", inline=True)
    embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    if image_url:
        embed.set_image(url=image_url)
    elif member.guild.banner:
        embed.set_image(url=member.guild.banner.url)
    
    embed.set_footer(text=f"Joined at {member.joined_at.strftime('%Y-%m-%d %H:%M:%S UTC') if member.joined_at else 'Unknown'}")
    embed.timestamp = member.joined_at
    
    return embed


async def create_farewell_embed(
    member: discord.Member,
    custom_message: Optional[str] = None
) -> discord.Embed:
    """Create a farewell embed."""
    embed = discord.Embed(
        title=f"Goodbye! 👋",
        description=custom_message or f"{member.display_name} has left the server.",
        color=discord.Color.red()
    )
    
    embed.add_field(name="Time on Server", value=f"Joined <t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", inline=True)
    embed.add_field(name="Members Now", value=str(member.guild.member_count), inline=True)
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    embed.set_footer(text=f"User ID: {member.id}")
    
    return embed


class WelcomeButtons(discord.ui.View):
    """Interactive buttons for welcome messages."""
    
    def __init__(self, rules_channel: Optional[discord.TextChannel] = None, 
                 roles_channel: Optional[discord.TextChannel] = None):
        super().__init__(timeout=None)
        
        if rules_channel:
            rules_button = discord.ui.Button(
                label="📜 Read Rules",
                style=discord.ButtonStyle.primary,
                url=f"https://discord.com/channels/{rules_channel.guild.id}/{rules_channel.id}"
            )
            self.add_item(rules_button)
        
        if roles_channel:
            roles_button = discord.ui.Button(
                label="🎭 Get Roles",
                style=discord.ButtonStyle.success,
                url=f"https://discord.com/channels/{roles_channel.guild.id}/{roles_channel.id}"
            )
            self.add_item(roles_button)


async def send_welcome_message(
    channel: discord.TextChannel,
    member: discord.Member,
    custom_message: Optional[str] = None,
    image_url: Optional[str] = None,
    rules_channel: Optional[discord.TextChannel] = None,
    roles_channel: Optional[discord.TextChannel] = None
) -> discord.Message:
    """Send an enhanced welcome message with embed and buttons."""
    embed = await create_welcome_embed(member, custom_message, image_url)
    view = WelcomeButtons(rules_channel, roles_channel)
    
    return await channel.send(embed=embed, view=view)


async def send_farewell_message(
    channel: discord.TextChannel,
    member: discord.Member,
    custom_message: Optional[str] = None
) -> discord.Message:
    """Send a farewell message with embed."""
    embed = await create_farewell_embed(member, custom_message)
    return await channel.send(embed=embed)
