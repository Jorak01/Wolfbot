"""
Slash Commands Module for Wolfbot
Provides modern Discord slash command (/) implementations
"""

import discord
from discord import app_commands
from typing import Optional, Literal
import datetime as dt

class SlashCommands:
    """Container for all slash command definitions"""
    
    def __init__(self, bot, integrations: dict):
        self.bot = bot
        self.tree = bot.tree
        self.twitch = integrations.get('twitch')
        self.spotify = integrations.get('spotify')
        
    async def setup_commands(self):
        """Setup all slash commands"""
        # This will be called after bot is ready
        pass


def create_slash_commands(bot, integrations: dict):
    """
    Factory function to create and register all slash commands
    
    Args:
        bot: The Discord bot instance
        integrations: Dict containing twitch, spotify, etc.
    """
    tree = bot.tree
    twitch = integrations.get('twitch')
    spotify = integrations.get('spotify')
    
    # Import required modules
    from discord_bot import (
        analytics, command_handler, leveling_system, community_features,
        warning_system, automod, logging_system, gaming_utilities, utils_misc
    )
    from discord_bot.security import is_admin, is_moderator
    from discord_bot.moderation import (
        ban_user as mod_ban_user,
        kick_user as mod_kick_user,
        mute_user as mod_mute_user,
        purge_messages
    )
    from integrations import ai_integration, external_apis
    import integration
    
    # Helper function for mod checks
    def is_mod_or_admin(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        return is_admin(interaction.user) or is_moderator(interaction.user)
    
    # =============================================================================
    # Core Bot Commands
    # =============================================================================
    
    @tree.command(name="status", description="Check the bot status")
    async def slash_status(interaction: discord.Interaction):
        message = await integration.get_status()
        await interaction.response.send_message(message)
    
    @tree.command(name="health", description="Check integration health status")
    async def slash_health(interaction: discord.Interaction):
        parts = []
        if twitch:
            from discord_bot import lifecycle
            status = await lifecycle.health_check(bot, twitch)
            parts.append(status)
        else:
            parts.append("Twitch: Not configured")
        
        if spotify:
            spotify_status = await spotify.health_check()
            parts.append(spotify_status)
        else:
            parts.append("Spotify: Not configured")
        
        combined = "\n".join(parts)
        await interaction.response.send_message(combined[:1990])
    
    # =============================================================================
    # Moderation Commands
    # =============================================================================
    
    @tree.command(name="warn", description="Warn a user with escalation")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for the warning"
    )
    async def slash_warn(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        if not is_mod_or_admin(interaction):
            await interaction.response.send_message("❌ You need moderator permissions.", ephemeral=True)
            return
        
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        count, action, escalation_msg = await warning_system.warn_user_with_escalation(
            member, interaction.user, reason
        )
        
        response = f"⚠️ {member.mention} has been warned. Total warnings: {count}"
        if escalation_msg:
            response += f"\n{escalation_msg}"
        
        await interaction.response.send_message(response)
    
    @tree.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(member="The member to check warnings for")
    async def slash_warnings(interaction: discord.Interaction, member: discord.Member):
        if not is_mod_or_admin(interaction):
            await interaction.response.send_message("❌ You need moderator permissions.", ephemeral=True)
            return
        
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        warns = await warning_system.get_user_warnings(interaction.guild.id, member.id)
        embed = await warning_system.format_warnings_embed(member, warns)
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for the kick"
    )
    async def slash_kick(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        if not is_mod_or_admin(interaction):
            await interaction.response.send_message("❌ You need moderator permissions.", ephemeral=True)
            return
        
        msg = await mod_kick_user(member, reason=reason)
        await interaction.response.send_message(msg)
    
    @tree.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban"
    )
    async def slash_ban(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        if not is_mod_or_admin(interaction):
            await interaction.response.send_message("❌ You need moderator permissions.", ephemeral=True)
            return
        
        msg = await mod_ban_user(member, reason=reason)
        await interaction.response.send_message(msg)
    
    @tree.command(name="mute", description="Mute (timeout) a user")
    @app_commands.describe(
        member="The member to mute",
        duration="Duration (e.g., 10m, 1h, 1d)"
    )
    async def slash_mute(
        interaction: discord.Interaction,
        member: discord.Member,
        duration: str
    ):
        if not is_mod_or_admin(interaction):
            await interaction.response.send_message("❌ You need moderator permissions.", ephemeral=True)
            return
        
        seconds = utils_misc.parse_duration(duration)
        msg = await mod_mute_user(member, seconds, reason=f"Muted by {interaction.user}")
        await interaction.response.send_message(msg)
    
    @tree.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(amount="Number of messages to delete (default: 10)")
    async def slash_purge(interaction: discord.Interaction, amount: int = 10):
        if not is_mod_or_admin(interaction):
            await interaction.response.send_message("❌ You need moderator permissions.", ephemeral=True)
            return
        
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("❌ This command can only be used in a text channel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        msg = await purge_messages(interaction.channel, amount, reason=f"Purge by {interaction.user}")
        await interaction.followup.send(msg, ephemeral=True)
    
    # =============================================================================
    # Leveling & Community Commands
    # =============================================================================
    
    @tree.command(name="rank", description="Check your or another user's rank and XP")
    @app_commands.describe(member="The member to check (leave empty for yourself)")
    async def slash_rank(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        target = member if member else interaction.user
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
            return
        
        stats = await leveling_system.get_user_stats(interaction.guild.id, target.id)
        if not stats:
            await interaction.response.send_message(f"{target.mention} hasn't earned any XP yet!")
            return
        
        rank = await leveling_system.get_user_rank(interaction.guild.id, target.id)
        embed = await leveling_system.create_rank_card_embed(target, stats, rank)
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="leaderboard", description="Show the XP leaderboard")
    async def slash_leaderboard(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        lb = await leveling_system.get_leaderboard(interaction.guild.id, limit=10)
        embed = await leveling_system.create_leaderboard_embed(interaction.guild, lb)
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="karma", description="Check karma points")
    @app_commands.describe(member="The member to check (leave empty for yourself)")
    async def slash_karma(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        target = member if member else interaction.user
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
            return
        
        karma = await community_features.get_karma(interaction.guild.id, target.id)
        await interaction.response.send_message(f"{target.mention} has **{karma}** karma points! ⭐")
    
    @tree.command(name="givekarma", description="Give karma to another user")
    @app_commands.describe(
        member="The member to give karma to",
        reason="Reason for giving karma"
    )
    async def slash_givekarma(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Being awesome!"
    ):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        success, message = await community_features.give_karma(
            interaction.guild.id, interaction.user.id, member.id, reason=reason
        )
        
        if success:
            await interaction.response.send_message(f"✅ {interaction.user.mention} → {member.mention}: +1 karma! {message}")
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    # =============================================================================
    # Gaming Utilities Commands
    # =============================================================================
    
    @tree.command(name="roll", description="Roll dice (e.g., 2d6+1)")
    @app_commands.describe(expression="Dice expression (e.g., 2d6+1, 1d20, 3d8)")
    async def slash_roll(interaction: discord.Interaction, expression: str):
        from discord_bot.games import roll_dice
        try:
            total = roll_dice(expression)
            await interaction.response.send_message(f"🎲 Result: **{total}**")
        except Exception as exc:
            await interaction.response.send_message(f"❌ Invalid dice expression: {exc}", ephemeral=True)
    
    @tree.command(name="coinflip", description="Flip a coin")
    async def slash_coinflip(interaction: discord.Interaction):
        from discord_bot.games import coin_flip
        result = coin_flip()
        await interaction.response.send_message(f"🪙 Flipped: **{result}**")
    
    @tree.command(name="droll", description="Advanced D&D dice roller with advantage/disadvantage")
    @app_commands.describe(expression="Dice expression (e.g., 1d20 advantage, 2d6+5)")
    async def slash_droll(interaction: discord.Interaction, expression: str):
        try:
            result = gaming_utilities.roll_dice_detailed(expression)
        except Exception as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=result["expression"],
            color=discord.Color.blue()
        )
        
        rolls_text = ", ".join(str(r) for r in result["rolls"])
        embed.add_field(name="Rolls", value=rolls_text, inline=False)
        
        if result.get("advantage"):
            embed.add_field(
                name=result["advantage"],
                value=f"Kept: {result['rolls'][0]}, Discarded: {result['discarded']}",
                inline=False
            )
        
        if result["modifier"] != 0:
            embed.add_field(name="Modifier", value=f"{result['modifier']:+d}", inline=True)
        
        embed.add_field(name="**Total**", value=f"**{result['total']}**", inline=True)
        
        if result.get("critical"):
            embed.add_field(name="✨", value="**CRITICAL!**", inline=True)
        elif result.get("fumble"):
            embed.add_field(name="💀", value="**FUMBLE!**", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    # =============================================================================
    # AI Chatbot Commands
    # =============================================================================
    
    @tree.command(name="ai", description="Chat with the AI bot")
    @app_commands.describe(message="Your message to the AI")
    async def slash_ai(interaction: discord.Interaction, message: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        if not interaction.channel:
            await interaction.response.send_message("❌ This command can only be used in a channel.", ephemeral=True)
            return
        
        # Store IDs before any async calls to maintain type narrowing
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        user_id = interaction.user.id
        display_name = interaction.user.display_name
        
        # Check cooldown
        settings = await ai_integration.AISettings.get_settings(guild_id)
        can_use, remaining = await ai_integration.ai_chat.check_cooldown(
            user_id, settings["cooldown_seconds"]
        )
        
        if not can_use:
            await interaction.response.send_message(
                f"⏱️ Please wait {remaining:.1f} more seconds before using AI chat again.",
                ephemeral=True
            )
            return
        
        # Defer response for longer processing
        await interaction.response.defer()
        
        response = await ai_integration.ai_chat.generate_response(
            message, guild_id, channel_id,
            user_id, display_name
        )
        
        # Set cooldown
        ai_integration.ai_chat.set_cooldown(user_id)
        
        await interaction.followup.send(response[:2000])
    
    @tree.command(name="remember", description="Store a memory for the AI")
    @app_commands.describe(
        key="Memory key (e.g., favorite color)",
        value="Memory value (e.g., blue)"
    )
    async def slash_remember(interaction: discord.Interaction, key: str, value: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        await ai_integration.AIMemoryManager.store_user_memory(
            interaction.guild.id, interaction.user.id, key, value
        )
        await interaction.response.send_message(f"✅ Remembered: {key} = {value}")
    
    @tree.command(name="memories", description="List AI memories about you or another user")
    @app_commands.describe(member="The member to check memories for (leave empty for yourself)")
    async def slash_memories(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        target = member if member else interaction.user
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
            return
        
        memories = await ai_integration.AIMemoryManager.get_user_memories(
            interaction.guild.id, target.id
        )
        
        if not memories:
            await interaction.response.send_message(f"No memories stored for {target.mention}")
            return
        
        embed = discord.Embed(
            title=f"🧠 Memories for {target.display_name}",
            color=discord.Color.blue()
        )
        
        for mem in memories[:10]:
            embed.add_field(name=mem["key"], value=mem["value"], inline=False)
        
        if len(memories) > 10:
            embed.set_footer(text=f"Showing 10 of {len(memories)} memories")
        
        await interaction.response.send_message(embed=embed)
    
    # =============================================================================
    # External API Commands
    # =============================================================================
    
    @tree.command(name="mtgcard", description="Search for a Magic: The Gathering card")
    @app_commands.describe(card_name="Name of the card to search for")
    async def slash_mtgcard(interaction: discord.Interaction, card_name: str):
        await interaction.response.defer()
        
        card = await external_apis.ScryfallAPI.get_card_by_name(card_name)
        
        if not card:
            await interaction.followup.send(f"❌ Card '{card_name}' not found.")
            return
        
        embed = discord.Embed(
            title=card.get("name", "Unknown"),
            description=card.get("type_line", ""),
            color=discord.Color.purple(),
            url=card.get("scryfall_uri", "")
        )
        
        if card.get("mana_cost"):
            embed.add_field(name="Mana Cost", value=card["mana_cost"], inline=True)
        
        if card.get("oracle_text"):
            text = card["oracle_text"][:1000]
            embed.add_field(name="Text", value=text, inline=False)
        
        if card.get("power") and card.get("toughness"):
            embed.add_field(name="P/T", value=f"{card['power']}/{card['toughness']}", inline=True)
        
        if card.get("image_uris", {}).get("normal"):
            embed.set_image(url=card["image_uris"]["normal"])
        
        await interaction.followup.send(embed=embed)
    
    @tree.command(name="dndspell", description="Search for a D&D 5e spell")
    @app_commands.describe(spell_name="Name of the spell to search for")
    async def slash_dndspell(interaction: discord.Interaction, spell_name: str):
        await interaction.response.defer()
        
        spells = await external_apis.Open5eAPI.search_spells(spell_name)
        
        if not spells:
            await interaction.followup.send(f"❌ No spells found for '{spell_name}'")
            return
        
        spell = spells[0]
        
        embed = discord.Embed(
            title=f"📜 {spell.get('name', 'Unknown')}",
            description=spell.get('desc', 'No description')[:2000],
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Level", value=f"Level {spell.get('level', '?')}", inline=True)
        embed.add_field(name="School", value=spell.get('school', 'Unknown'), inline=True)
        embed.add_field(name="Casting Time", value=spell.get('casting_time', 'Unknown'), inline=True)
        embed.add_field(name="Range", value=spell.get('range', 'Unknown'), inline=True)
        embed.add_field(name="Duration", value=spell.get('duration', 'Unknown'), inline=True)
        
        if spell.get('components'):
            embed.add_field(name="Components", value=spell['components'], inline=True)
        
        await interaction.followup.send(embed=embed)
    
    # =============================================================================
    # Spotify Commands
    # =============================================================================
    
    @tree.command(name="nowplaying", description="Show what's currently playing on Spotify")
    async def slash_nowplaying(interaction: discord.Interaction):
        if not spotify:
            await interaction.response.send_message("❌ Spotify integration is not configured.", ephemeral=True)
            return
        
        track = await spotify.get_current_track()
        if not track:
            await interaction.response.send_message("Nothing is playing on Spotify right now.")
            return
        
        embed = spotify.create_now_playing_embed(track)
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="play", description="Play a song from Spotify")
    @app_commands.describe(query="Song name or search query")
    async def slash_play(interaction: discord.Interaction, query: str):
        if not spotify:
            await interaction.response.send_message("❌ Spotify integration is not configured.", ephemeral=True)
            return
        
        if not isinstance(interaction.user, discord.Member) or not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You need to be in a voice channel.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Auto-join if not connected
        if not spotify.voice_client or not spotify.voice_client.is_connected():
            channel = interaction.user.voice.channel
            if isinstance(channel, discord.VoiceChannel):
                await spotify.join_voice(channel)
        
        message = await spotify.play_track(query, requester=interaction.user.display_name)
        await interaction.followup.send(message)
    
    @tree.command(name="queue", description="Show the music queue")
    async def slash_queue(interaction: discord.Interaction):
        if not spotify:
            await interaction.response.send_message("❌ Spotify integration is not configured.", ephemeral=True)
            return
        
        embed = spotify.create_queue_embed()
        await interaction.response.send_message(embed=embed)
    
    @tree.command(name="skip", description="Skip the current track")
    async def slash_skip(interaction: discord.Interaction):
        if not spotify:
            await interaction.response.send_message("❌ Spotify integration is not configured.", ephemeral=True)
            return
        
        message = await spotify.skip()
        await interaction.response.send_message(message)
    
    # =============================================================================
    # Server Stats & Info Commands
    # =============================================================================
    
    @tree.command(name="serverstats", description="Show server statistics dashboard")
    async def slash_serverstats(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        stats = await community_features.get_server_stats(interaction.guild.id, days=7)
        embed = await community_features.create_stats_embed(interaction.guild, stats)
        await interaction.followup.send(embed=embed)
    
    print("✅ Slash commands registered")
