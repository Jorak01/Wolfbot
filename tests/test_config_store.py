from pathlib import Path

from src.discord_bot import config_store


def test_load_save_config(tmp_path: Path):
    path = tmp_path / "config.json"
    cfg = config_store.load_config(path)
    assert cfg["version"] == config_store.CURRENT_VERSION
    cfg["guilds"]["123"] = {"key": "value"}
    config_store.save_config(cfg, path)
    loaded = config_store.load_config(path)
    assert loaded["guilds"]["123"]["key"] == "value"


def test_migrate_config(tmp_path: Path):
    path = tmp_path / "config.json"
    cfg = {"version": 0, "guilds": {}, "users": {}}
    config_store.save_config(cfg, path)
    migrated = config_store.migrate_config(2, path=path)
    assert migrated["version"] == 2
