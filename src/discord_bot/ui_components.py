"""
UI / interaction component helpers.
"""

from __future__ import annotations

from typing import Iterable, List

import discord


def create_embed(title: str = "", description: str = "", color: discord.Color | None = None) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color or discord.Color.blurple())


def create_button(label: str, style: discord.ButtonStyle = discord.ButtonStyle.primary) -> discord.ui.Button:
    return discord.ui.Button(label=label, style=style)


def create_dropdown(options: Iterable[str]) -> discord.ui.Select:
    select_options = [discord.SelectOption(label=opt) for opt in options]
    return discord.ui.Select(placeholder="Choose an option", options=select_options)


def create_modal(title: str, fields: List[tuple[str, str]]) -> discord.ui.Modal:
    """
    fields: list of (label, placeholder)
    """
    class DynamicModal(discord.ui.Modal, title=title):
        def __init__(self):
            super().__init__()
            for label, placeholder in fields:
                self.add_item(
                    discord.ui.TextInput(
                        label=label,
                        placeholder=placeholder,
                    )
                )
    return DynamicModal()


async def handle_button_interaction(interaction: discord.Interaction):
    await interaction.response.send_message(f"Button clicked: {interaction.data}", ephemeral=True)


async def handle_dropdown_interaction(interaction: discord.Interaction):
    values = interaction.data.get("values") if interaction.data else []
    chosen = ", ".join(values or [])
    await interaction.response.send_message(f"Selected: {chosen}", ephemeral=True)


async def handle_modal_submission(interaction: discord.Interaction):
    inputs = {}
    if interaction.data and "components" in interaction.data:
        for comp in interaction.data["components"]:
            for sub in comp.get("components", []):
                name = sub.get("custom_id") or sub.get("label")
                value = sub.get("value")
                if name:
                    inputs[name] = value
    pretty = ", ".join(f"{k}: {v}" for k, v in inputs.items())
    await interaction.response.send_message(f"Modal submitted: {pretty}", ephemeral=True)
