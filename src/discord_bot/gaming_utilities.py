"""
Gaming & Nerd Utilities: DnD, MTG, Warhammer, and more.
"""

from __future__ import annotations

import random
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import discord


# =============================
# Advanced Dice Rolling
# =============================

def roll_dice_detailed(expression: str) -> Dict:
    """
    Advanced dice roller with detailed results.
    Supports: 2d20, 3d6+5, 4d8-2, advantage/disadvantage
    """
    expression = expression.lower().strip()
    
    # Check for advantage/disadvantage
    advantage = "adv" in expression or "advantage" in expression
    disadvantage = "dis" in expression or "disadvantage" in expression
    expression = expression.replace("adv", "").replace("advantage", "").replace("dis", "").replace("disadvantage", "")
    
    # Parse dice expression
    match = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", expression.replace(" ", ""))
    if not match:
        raise ValueError("Invalid dice expression. Use format: 2d20, 3d6+5, etc.")
    
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    if count <= 0 or sides <= 0:
        raise ValueError("Dice count and sides must be positive")
    if count > 100:
        raise ValueError("Maximum 100 dice at once")
    
    # Roll dice
    rolls = [random.randint(1, sides) for _ in range(count)]
    
    # Handle advantage/disadvantage for d20
    if (advantage or disadvantage) and sides == 20 and count == 1:
        second_roll = random.randint(1, sides)
        rolls.append(second_roll)
        if advantage:
            result_roll = max(rolls)
            discarded = min(rolls)
        else:
            result_roll = min(rolls)
            discarded = max(rolls)
        rolls = [result_roll]
        advantage_text = "Advantage" if advantage else "Disadvantage"
    else:
        advantage_text = None
        discarded = None
    
    total = sum(rolls) + modifier
    
    return {
        "expression": f"{count}d{sides}{('+' if modifier >= 0 else '')}{modifier if modifier != 0 else ''}",
        "rolls": rolls,
        "modifier": modifier,
        "total": total,
        "advantage": advantage_text,
        "discarded": discarded,
        "critical": rolls[0] == sides if len(rolls) == 1 else None,
        "fumble": rolls[0] == 1 if len(rolls) == 1 and sides == 20 else None
    }


def roll_custom_table(table: List[str]) -> str:
    """Roll on a custom table."""
    if not table:
        raise ValueError("Table is empty")
    return random.choice(table)


# =============================
# DnD Character Stats
# =============================

@dataclass
class CharacterStats:
    """DnD 5e character stats."""
    name: str
    race: str
    char_class: str
    level: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    hp: int
    ac: int
    
    def get_modifier(self, stat: int) -> int:
        """Calculate ability modifier."""
        return (stat - 10) // 2
    
    def to_embed(self) -> discord.Embed:
        """Create character sheet embed."""
        embed = discord.Embed(
            title=f"⚔️ {self.name}",
            description=f"Level {self.level} {self.race} {self.char_class}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="STR", value=f"{self.strength} ({self.get_modifier(self.strength):+d})", inline=True)
        embed.add_field(name="DEX", value=f"{self.dexterity} ({self.get_modifier(self.dexterity):+d})", inline=True)
        embed.add_field(name="CON", value=f"{self.constitution} ({self.get_modifier(self.constitution):+d})", inline=True)
        embed.add_field(name="INT", value=f"{self.intelligence} ({self.get_modifier(self.intelligence):+d})", inline=True)
        embed.add_field(name="WIS", value=f"{self.wisdom} ({self.get_modifier(self.wisdom):+d})", inline=True)
        embed.add_field(name="CHA", value=f"{self.charisma} ({self.get_modifier(self.charisma):+d})", inline=True)
        
        embed.add_field(name="❤️ HP", value=str(self.hp), inline=True)
        embed.add_field(name="🛡️ AC", value=str(self.ac), inline=True)
        
        return embed


def generate_ability_scores(method: str = "standard") -> List[int]:
    """
    Generate ability scores.
    Methods: standard (4d6 drop lowest), point_buy, array
    """
    if method == "standard" or method == "4d6":
        scores = []
        for _ in range(6):
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            scores.append(sum(rolls[1:]))  # Drop lowest
        return sorted(scores, reverse=True)
    
    elif method == "point_buy":
        # Standard point buy array
        return [15, 14, 13, 12, 10, 8]
    
    elif method == "array":
        # Standard array
        return [15, 14, 13, 12, 10, 8]
    
    else:
        raise ValueError("Invalid method. Use: standard, point_buy, or array")


# =============================
# Loot Tables
# =============================

LOOT_TABLES = {
    "common": [
        "10 gold pieces", "A rusty dagger", "A health potion", "A worn leather bag",
        "A piece of chalk", "A tinderbox", "10 feet of rope", "A waterskin"
    ],
    "uncommon": [
        "50 gold pieces", "A +1 dagger", "2 health potions", "A bag of holding (small)",
        "Boots of striding", "A spell scroll (1st level)", "A potion of climbing",
        "Goggles of night"
    ],
    "rare": [
        "200 gold pieces", "A +1 longsword", "A ring of protection", "Cloak of protection",
        "A wand of magic missiles", "Bracers of defense", "Bag of tricks", "Belt of dwarvenkind"
    ],
    "legendary": [
        "1000 gold pieces", "A +2 weapon of your choice", "Ring of spell storing",
        "Staff of power", "Holy avenger", "Vorpal sword", "Sphere of annihilation",
        "Talisman of pure good"
    ]
}


def generate_loot(rarity: str = "common", count: int = 1) -> List[str]:
    """Generate random loot from tables."""
    rarity = rarity.lower()
    if rarity not in LOOT_TABLES:
        rarity = "common"
    
    return [random.choice(LOOT_TABLES[rarity]) for _ in range(min(count, 10))]


# =============================
# Encounter Generator
# =============================

MONSTERS_BY_CR = {
    "0": ["Rat", "Frog", "Spider", "Crab"],
    "1/4": ["Goblin", "Kobold", "Skeleton", "Zombie"],
    "1/2": ["Orc", "Hobgoblin", "Scout", "Thug"],
    "1": ["Bugbear", "Dire Wolf", "Specter", "Spy"],
    "2": ["Ogre", "Werewolf", "Ghast", "Gargoyle"],
    "3": ["Owlbear", "Hell Hound", "Manticore", "Veteran"],
    "4": ["Ettin", "Succubus", "Ghost", "Banshee"],
    "5": ["Hill Giant", "Air Elemental", "Troll", "Gladiator"],
    "10": ["Stone Golem", "Young Red Dragon", "Aboleth", "Guardian Naga"],
    "20": ["Ancient Red Dragon", "Lich", "Kraken", "Tarrasque"]
}


def generate_encounter(party_level: int, party_size: int = 4) -> Dict:
    """Generate a balanced encounter."""
    # Simplified CR calculation
    avg_cr = max(0.25, party_level / 4)
    
    # Select appropriate CR
    available_crs = ["0", "1/4", "1/2", "1", "2", "3", "4", "5", "10", "20"]
    cr_values = [0, 0.25, 0.5, 1, 2, 3, 4, 5, 10, 20]
    
    # Find closest CR
    closest_idx = min(range(len(cr_values)), key=lambda i: abs(cr_values[i] - avg_cr))
    selected_cr = available_crs[closest_idx]
    
    # Generate monsters
    monster_count = max(1, party_size // 2 + random.randint(-1, 1))
    monsters = random.choices(MONSTERS_BY_CR[selected_cr], k=monster_count)
    
    return {
        "cr": selected_cr,
        "monsters": monsters,
        "count": len(monsters),
        "difficulty": "Medium" if party_level > cr_values[closest_idx] else "Hard"
    }


# =============================
# Initiative Tracker
# =============================

class InitiativeTracker:
    """Track initiative for combat encounters."""
    
    def __init__(self):
        self.combatants: List[Tuple[str, int]] = []
        self.current_index = 0
        self.round_number = 1
    
    def add_combatant(self, name: str, initiative: int):
        """Add a combatant to initiative."""
        self.combatants.append((name, initiative))
        self.combatants.sort(key=lambda x: x[1], reverse=True)
    
    def remove_combatant(self, name: str) -> bool:
        """Remove a combatant."""
        for i, (n, _) in enumerate(self.combatants):
            if n.lower() == name.lower():
                self.combatants.pop(i)
                return True
        return False
    
    def next_turn(self) -> Optional[Tuple[str, int]]:
        """Advance to next combatant."""
        if not self.combatants:
            return None
        
        self.current_index = (self.current_index + 1) % len(self.combatants)
        if self.current_index == 0:
            self.round_number += 1
        
        return self.combatants[self.current_index]
    
    def get_current(self) -> Optional[Tuple[str, int]]:
        """Get current combatant."""
        if not self.combatants:
            return None
        return self.combatants[self.current_index]
    
    def get_order(self) -> List[Tuple[str, int, bool]]:
        """Get full initiative order with current turn marked."""
        return [
            (name, init, i == self.current_index)
            for i, (name, init) in enumerate(self.combatants)
        ]
    
    def clear(self):
        """Clear initiative tracker."""
        self.combatants = []
        self.current_index = 0
        self.round_number = 1


# Global initiative trackers per guild
_initiative_trackers: Dict[int, InitiativeTracker] = {}


def get_initiative_tracker(guild_id: int) -> InitiativeTracker:
    """Get or create initiative tracker for guild."""
    if guild_id not in _initiative_trackers:
        _initiative_trackers[guild_id] = InitiativeTracker()
    return _initiative_trackers[guild_id]


# =============================
# Random Generators
# =============================

FANTASY_FIRST_NAMES = [
    "Aldric", "Bren", "Cassian", "Draven", "Elara", "Fynn", "Gwendolyn", "Hadrian",
    "Isolde", "Jareth", "Kaelen", "Lyra", "Magnus", "Nyx", "Orion", "Phoebe",
    "Quillon", "Raven", "Seraphina", "Theron", "Ulric", "Vesper", "Wren", "Zephyr"
]

FANTASY_LAST_NAMES = [
    "Ironforge", "Stormwind", "Darkblade", "Moonwhisper", "Fireheart", "Frostborn",
    "Shadowstep", "Brightwood", "Thornspell", "Silvermane", "Goldleaf", "Ashborne",
    "Ravenclaw", "Nightshade", "Dawnbringer", "Starfall", "Windrunner", "Stonefist"
]

NPC_PERSONALITIES = [
    "Cheerful and optimistic", "Grumpy and pessimistic", "Nervous and fidgety",
    "Arrogant and boastful", "Shy and timid", "Wise and thoughtful", "Cunning and sly",
    "Brave and heroic", "Cowardly and fearful", "Friendly and helpful", "Suspicious and paranoid",
    "Calm and collected", "Hot-tempered and aggressive", "Mysterious and secretive",
    "Jovial and loud", "Melancholy and sad"
]

NPC_QUIRKS = [
    "Always adjusts their hat", "Speaks in rhymes", "Has a pet rat on their shoulder",
    "Constantly eating something", "Refers to themselves in third person",
    "Laughs at inappropriate times", "Collects unusual objects", "Has a distinctive accent",
    "Never makes eye contact", "Always carries a lucky charm", "Tells terrible jokes",
    "Has an unusual phobia", "Hums while thinking", "Gestures wildly when talking"
]

QUEST_HOOKS = [
    "A mysterious stranger offers gold for a dangerous task",
    "Local children have gone missing near the old ruins",
    "A plague is spreading through the village",
    "Bandits have been raiding caravans on the trade road",
    "An ancient artifact has been stolen from the museum",
    "Strange lights have been seen in the forest at night",
    "A noble's daughter has been kidnapped by cultists",
    "The town well has been poisoned",
    "A dragon has been spotted near the mountain village",
    "Dead are rising from the cemetery",
    "A wizard seeks brave adventurers for an expedition",
    "Pirates have blockaded the harbor",
    "A mysterious portal has appeared in the town square",
    "The king's crown has been stolen on coronation day",
    "A beast is terrorizing the countryside"
]


def generate_npc() -> Dict:
    """Generate a random NPC."""
    return {
        "name": f"{random.choice(FANTASY_FIRST_NAMES)} {random.choice(FANTASY_LAST_NAMES)}",
        "personality": random.choice(NPC_PERSONALITIES),
        "quirk": random.choice(NPC_QUIRKS)
    }


def generate_quest_hook() -> str:
    """Generate a random quest hook."""
    return random.choice(QUEST_HOOKS)


# =============================
# MTG Deck Importer (Simplified)
# =============================

async def parse_decklist(decklist: str) -> Dict:
    """
    Parse MTG decklist from text format.
    Supports formats like:
    4 Lightning Bolt
    2 Counterspell
    """
    lines = decklist.strip().split('\n')
    cards = []
    total = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        
        # Parse "4 Card Name" or "4x Card Name"
        match = re.match(r'(\d+)x?\s+(.+)', line)
        if match:
            count = int(match.group(1))
            name = match.group(2).strip()
            cards.append({"count": count, "name": name})
            total += count
    
    return {
        "cards": cards,
        "total_cards": total,
        "valid": 60 <= total <= 100  # Rough validation
    }


def create_decklist_embed(deck_data: Dict, deck_name: str = "MTG Deck") -> discord.Embed:
    """Create embed for MTG decklist."""
    embed = discord.Embed(
        title=f"🃏 {deck_name}",
        description=f"Total Cards: {deck_data['total_cards']}",
        color=discord.Color.purple()
    )
    
    # Group cards
    if deck_data["cards"]:
        card_list = "\n".join([f"{c['count']}x {c['name']}" for c in deck_data["cards"][:25]])
        if len(deck_data["cards"]) > 25:
            card_list += f"\n... and {len(deck_data['cards']) - 25} more cards"
        embed.add_field(name="Decklist", value=card_list, inline=False)
    
    validity = "✅ Valid" if deck_data["valid"] else "❌ Invalid card count"
    embed.add_field(name="Status", value=validity, inline=False)
    
    return embed
