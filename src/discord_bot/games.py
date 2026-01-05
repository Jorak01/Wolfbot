"""
Lightweight games and fun utilities.
"""

from __future__ import annotations

import random
import re
from typing import Iterable, List


def roll_dice(expression: str) -> int:
    """
    Parse expressions like '2d6+3' or '1d20'. Returns the total.
    """
    match = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", expression.replace(" ", ""))
    if not match:
        raise ValueError("Invalid dice expression")
    count = int(match.group(1))
    sides = int(match.group(2))
    mod = int(match.group(3)) if match.group(3) else 0
    if count <= 0 or sides <= 0:
        raise ValueError("Dice count and sides must be positive")
    rolls = [random.randint(1, sides) for _ in range(count)]
    return sum(rolls) + mod


def random_choice(options: Iterable[str]) -> str:
    opts = list(options)
    if not opts:
        raise ValueError("No options provided")
    return random.choice(opts)


def coin_flip() -> str:
    return random.choice(["heads", "tails"])


def rps_game(user_choice: str) -> str:
    choices = ["rock", "paper", "scissors"]
    user = user_choice.lower()
    if user not in choices:
        raise ValueError("Invalid choice")
    bot = random.choice(choices)
    outcome = "draw"
    if (user == "rock" and bot == "scissors") or (user == "paper" and bot == "rock") or (user == "scissors" and bot == "paper"):
        outcome = "win"
    elif user != bot:
        outcome = "lose"
    return f"You chose {user}, I chose {bot}. Result: {outcome}."


def poll_creator(question: str, options: List[str]) -> str:
    if not question or not options:
        raise ValueError("Question and options are required")
    formatted = [f"{idx+1}. {opt}" for idx, opt in enumerate(options)]
    return f"{question}\n" + "\n".join(formatted)
