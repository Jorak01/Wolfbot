import pytest

from src.discord_bot import games


def test_coin_flip():
    assert games.coin_flip() in {"heads", "tails"}


def test_random_choice():
    assert games.random_choice(["a", "b"]) in {"a", "b"}


def test_roll_dice_valid():
    value = games.roll_dice("2d6+1")
    assert 3 <= value <= 13


def test_roll_dice_invalid():
    with pytest.raises(ValueError):
        games.roll_dice("nope")


def test_rps_game():
    result = games.rps_game("rock")
    assert "Result:" in result
