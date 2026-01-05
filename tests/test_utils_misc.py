import pytest

from src.discord_bot import utils_misc


def test_parse_duration_basic():
    assert utils_misc.parse_duration("1h30m") == 5400
    assert utils_misc.parse_duration("45m") == 2700
    assert utils_misc.parse_duration("10s") == 10


def test_parse_duration_invalid():
    with pytest.raises(ValueError):
        utils_misc.parse_duration("abc")


def test_truncate_text():
    assert utils_misc.truncate_text("hello", 10) == "hello"
    assert utils_misc.truncate_text("hello world", 5) == "he..."


def test_chunk_message():
    chunks = utils_misc.chunk_message("a" * 4000, limit=1900)
    assert len(chunks) == 3
    assert all(len(chunk) <= 1900 for chunk in chunks)


def test_validate_url():
    assert utils_misc.validate_url("https://example.com/path")
    assert not utils_misc.validate_url("not-a-url")
