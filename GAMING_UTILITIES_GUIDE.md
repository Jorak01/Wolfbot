# Gaming & Nerd Utilities Guide

This guide covers all gaming-related commands for D&D, MTG, and other tabletop RPG features in Wolfbot.

## Table of Contents
- [Dice Rolling](#dice-rolling)
- [D&D Character Tools](#dd-character-tools)
- [Combat Tools](#combat-tools)
- [Random Generators](#random-generators)
- [MTG Tools](#mtg-tools)
- [D&D 5e API Integration](#dd-5e-api-integration)
- [External Integrations](#external-integrations)

---

## Dice Rolling

### Advanced Dice Roller
**Command:** `!droll <expression>` (aliases: `!dr`, `!diceroll`)

Roll dice with full support for modifiers, advantage, and disadvantage.

**Examples:**
```
!droll 2d20              # Roll 2 twenty-sided dice
!droll 3d6+5            # Roll 3d6 and add 5
!droll 4d8-2            # Roll 4d8 and subtract 2
!droll 1d20 advantage   # Roll with advantage (keeps higher)
!droll 1d20 disadvantage # Roll with disadvantage (keeps lower)
```

**Features:**
- Supports standard dice notation (XdY+Z)
- Advantage/disadvantage for d20 rolls
- Shows all individual rolls
- Highlights critical hits (natural 20)
- Highlights fumbles (natural 1 on d20)
- Maximum 100 dice per roll

---

## D&D Character Tools

### Ability Score Generation
**Command:** `!stats [method]` (aliases: `!abilities`, `!abilityscores`)

Generate ability scores for your D&D character.

**Methods:**
- `standard` - 4d6 drop lowest (default)
- `point_buy` - Point buy array
- `array` - Standard array

**Examples:**
```
!stats standard    # Roll 4d6, drop lowest for each stat
!stats point_buy   # Use point buy system
!stats array       # Use standard array
```

**Output:**
- 6 ability scores
- Total sum
- Average score
- Instructions for assigning to STR, DEX, CON, INT, WIS, CHA

---

## Combat Tools

### Encounter Generator
**Command:** `!encounter <party_level> [party_size]` (alias: `!generateencounter`)

Generate a balanced combat encounter based on party level and size.

**Examples:**
```
!encounter 5 4     # Level 5 party of 4 players
!encounter 10      # Level 10 party (default 4 players)
```

**Output:**
- Challenge Rating
- Difficulty estimate
- Number of monsters
- List of monsters for the encounter

**Valid Values:**
- Party level: 1-20
- Party size: 1-10 (default: 4)

### Initiative Tracker
**Command:** `!initiative <action> [name] [value]` (alias: `!init`)

Track turn order during combat encounters.

**Actions:**
- `add <name> <initiative>` - Add a combatant
- `remove <name>` - Remove a combatant
- `next` - Advance to next turn
- `show` - Display current turn order
- `clear` - Clear all combatants

**Examples:**
```
!initiative add Goblin 15        # Add Goblin with initiative 15
!initiative add Fighter 18       # Add Fighter with initiative 18
!initiative show                 # View turn order
!initiative next                 # Advance to next turn
!initiative remove Goblin        # Remove Goblin
!initiative clear                # Start fresh
```

**Features:**
- Automatic turn tracking
- Round counter
- Highlights current turn
- Per-server tracking (each server has its own tracker)

### Loot Generator
**Command:** `!loot [rarity] [count]` (aliases: `!treasure`, `!generateloot`)

Generate random treasure and items from loot tables.

**Rarities:**
- `common` (default) - Basic items, small gold amounts
- `uncommon` - Better items, modest rewards
- `rare` - Valuable items, significant rewards
- `legendary` - Epic items, massive rewards

**Examples:**
```
!loot                  # 1 common item
!loot uncommon         # 1 uncommon item
!loot rare 3           # 3 rare items
!loot legendary 5      # 5 legendary items
```

**Limits:**
- Count: 1-10 items per command

---

## Random Generators

### NPC Generator
**Command:** `!npc` (aliases: `!generatenpc`, `!randomnpc`)

Generate a random NPC with personality traits and quirks.

**Example:**
```
!npc
```

**Output:**
- Fantasy name (first + last)
- Personality trait
- Distinctive quirk

**Sample NPCs:**
- "Elara Moonwhisper - Cheerful and optimistic, Always adjusts their hat"
- "Draven Ironforge - Grumpy and pessimistic, Speaks in rhymes"

### Quest Hook Generator
**Command:** `!quest` (aliases: `!questhook`, `!questidea`)

Generate a random quest hook or adventure idea.

**Example:**
```
!quest
```

**Sample Hooks:**
- "A mysterious stranger offers gold for a dangerous task"
- "Local children have gone missing near the old ruins"
- "Dead are rising from the cemetery"

### Fantasy Name Generator
**Command:** `!name` (aliases: `!randomname`, `!fantasyname`)

Generate a random fantasy character name.

**Example:**
```
!name
```

**Output:**
Random combination of fantasy first and last names like:
- "Aldric Stormwind"
- "Seraphina Nightshade"
- "Magnus Fireheart"

---

## MTG Tools

### Decklist Parser
**Command:** `!deck <decklist>` (aliases: `!decklist`, `!mtgdeck`)

Parse and validate Magic: The Gathering decklists.

**Format:**
```
!deck <quantity> <card name>
<quantity> <card name>
...
```

**Examples:**
```
!deck 4 Lightning Bolt
2 Counterspell
20 Island
20 Mountain
```

Or with 'x' notation:
```
!deck 4x Lightning Bolt
2x Counterspell
```

**Output:**
- Formatted decklist
- Total card count
- Validation (60-100 cards)

**Features:**
- Supports standard text format
- Counts total cards
- Basic deck validation
- Displays up to 25 cards (shows count if more)

### MTG Card Lookup
**Command:** `!mtgcard <card_name>` (aliases: `!card`, `!mtg`)

Look up a Magic: The Gathering card from the Scryfall database.

**Examples:**
```
!mtgcard Lightning Bolt
!card Black Lotus
!mtg Counterspell
```

**Output:**
- Card name and mana cost
- Type line
- Oracle text
- Power/Toughness (for creatures)
- Card image
- Set information
- Scryfall link

**Features:**
- Fuzzy name matching
- Supports double-faced cards
- Shows latest printing
- High-quality card images
- No API key required

### Random MTG Card
**Command:** `!randomcard` (aliases: `!randommtg`)

Get a random Magic: The Gathering card from Scryfall.

**Example:**
```
!randomcard
```

**Output:**
- Same format as card lookup
- Truly random from entire database
- Great for challenge decks or inspiration

---

## D&D 5e API Integration

Powered by the Open5e API for official D&D 5e SRD content.

### Spell Lookup
**Command:** `!dndspell <spell_name>` (aliases: `!spell`, `!5espell`)

Look up a D&D 5th edition spell with full details.

**Examples:**
```
!dndspell Fireball
!spell Cure Wounds
!5espell Magic Missile
```

**Spell Information Includes:**
- Spell name and level
- School of magic
- Casting time
- Range and duration
- Components (V, S, M)
- Material components (if any)
- Full description
- At higher levels (if applicable)
- Classes that can cast it
- Concentration requirement
- Ritual casting availability

**Features:**
- Fuzzy name matching
- Complete SRD spell list
- Formatted for readability
- No API key required

### Monster Lookup
**Command:** `!dndmonster <monster_name>` (aliases: `!monster`, `!5emonster`)

Look up a D&D 5th edition monster stat block.

**Examples:**
```
!dndmonster Dragon
!monster Goblin
!5emonster Beholder
```

**Monster Stat Block Includes:**
- Monster name, size, and type
- Armor Class and Hit Points
- Speed and ability scores
- Saving throws and skills
- Damage resistances/immunities
- Senses and languages
- Challenge Rating (CR) and XP
- Special abilities
- Actions
- Legendary actions (if any)

**Features:**
- Complete SRD monster list
- Formatted stat blocks
- Search by partial name
- No API key required

---

## External Integrations

### GitHub Repository Info
**Command:** `!github <owner> <repo>` (aliases: `!repo`, `!ghrepo`)

Get information about a GitHub repository.

**Examples:**
```
!github discord discordpy
!repo python cpython
!ghrepo tensorflow tensorflow
```

**Repository Info Includes:**
- Repository name and description
- Star count and fork count
- Watchers and open issues
- Programming language
- Creation date and last update
- Default branch and license
- Repository URL

**Features:**
- Real-time data from GitHub API
- Support for all public repositories
- Optional GitHub token for higher rate limits

---

## Tips & Tricks

### For DMs
1. **Prep encounters quickly:** Use `!encounter` to generate balanced fights on the fly
2. **Track initiative:** Keep combat organized with `!initiative`
3. **Reward players:** Use `!loot` to generate treasure rewards
4. **Populate worlds:** Generate NPCs with `!npc` and quests with `!quest`

### For Players
1. **Roll characters:** Use `!stats` to generate ability scores
2. **Make attack rolls:** Use `!droll 1d20+5` for attacks with modifiers
3. **Check advantage:** Use `!droll 1d20 advantage` when you have advantage
4. **Track turns:** DM can use `!initiative` to keep combat flowing

### Best Practices
- **Initiative Tracker:** Clear it between encounters with `!initiative clear`
- **Dice Rolling:** Be specific with modifiers (e.g., `!droll 1d20+5` not `!droll d20+5`)
- **Loot Generation:** Generate loot appropriate to encounter difficulty
- **NPC Names:** Use `!name` to quickly name throwaway NPCs

---

## Command Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `!droll` | Advanced dice roller | `!droll 2d20+5` |
| `!stats` | Generate ability scores | `!stats standard` |
| `!encounter` | Generate combat encounter | `!encounter 5 4` |
| `!initiative` | Track initiative | `!initiative add Goblin 15` |
| `!loot` | Generate treasure | `!loot rare 3` |
| `!npc` | Random NPC | `!npc` |
| `!quest` | Quest hook | `!quest` |
| `!name` | Fantasy name | `!name` |
| `!deck` | Parse MTG deck | `!deck 4 Lightning Bolt` |
| `!mtgcard` | MTG card lookup | `!mtgcard Lightning Bolt` |
| `!randomcard` | Random MTG card | `!randomcard` |
| `!dndspell` | D&D spell lookup | `!dndspell Fireball` |
| `!dndmonster` | D&D monster lookup | `!dndmonster Goblin` |
| `!github` | GitHub repo info | `!github discord discordpy` |

---

## 🔌 API Sources & Setup

### Scryfall API (MTG Cards)
- **Website**: https://scryfall.com/
- **No API key required** - Free to use
- **Features**: Complete MTG card database, images, pricing data
- **Documentation**: https://scryfall.com/docs/api

### Open5e API (D&D 5e Content)
- **Website**: https://open5e.com/
- **No API key required** - Free SRD content
- **Features**: Spells, monsters, classes, equipment from official D&D 5e SRD
- **Documentation**: https://api.open5e.com/

### GitHub API
- **Website**: https://api.github.com/
- **Optional token** in `.env` for higher rate limits
- **Features**: Repository information, releases, contributors
- **Rate Limit**: 60 requests/hour (5000 with token)
- **Setup**: Add `GITHUB_TOKEN=your_token` to `.env` file

---

## Future Enhancements

Planned features for future updates:
- [ ] Warhammer 40K roster validation
- [ ] Expanded loot tables with magic item properties
- [ ] MTG card price tracking and alerts
- [ ] MTG deck legality checker by format
- [ ] Custom encounter templates
- [ ] Character sheet storage and management
- [ ] D&D equipment and magic item lookups
- [ ] D&D class and race information
- [ ] Custom loot table creation

---

## Support

If you encounter issues or have suggestions for gaming utilities:
1. Check that your command syntax matches the examples
2. Verify you're using valid parameters (e.g., level 1-20)
3. Report bugs using `/reportbug` command

**Common Issues:**
- **"Invalid dice expression"** - Check your syntax (e.g., `2d20` not `2D20`)
- **"Guild only command"** - Initiative tracker requires a server context
- **Initiative not showing** - Use `!initiative show` to view the tracker

---

*This guide covers all gaming utility features in Wolfbot. For other features, see:*
- *[ADMIN_MODERATION_GUIDE.md](ADMIN_MODERATION_GUIDE.md) - Admin and moderation features*
- *[SETUP_GUIDE.md](SETUP_GUIDE.md) - Bot setup and configuration*
- *[MUSIC_PLAYBACK_GUIDE.md](MUSIC_PLAYBACK_GUIDE.md) - Music commands*
