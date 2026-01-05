import discord
from discord.ext import commands

from .config import require_token
from . import integration

intents = discord.Intents.default()
intents.message_content = True  # Enable for prefix commands
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")


@bot.command(name="status")
async def status(ctx: commands.Context):
    """Return the current status from the integration layer."""
    message = await integration.get_status()
    await ctx.send(message)


def main():
    bot.run(require_token())


if __name__ == "__main__":
    main()
