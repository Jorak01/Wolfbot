"""
Lightweight JSON-backed configuration store for guild/user settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DEFAULT_CONFIG_PATH = DATA_DIR / "config.json"
CURRENT_VERSION = 1


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Load the config file or return defaults if missing/broken.
    """
    _ensure_data_dir()
    if not path.exists():
        return {"version": CURRENT_VERSION, "guilds": {}, "users": {}}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {"version": CURRENT_VERSION, "guilds": {}, "users": {}}
    if "version" not in data:
        data["version"] = CURRENT_VERSION
    data.setdefault("guilds", {})
    data.setdefault("users", {})
    return data


def save_config(config: Dict[str, Any], path: Path = DEFAULT_CONFIG_PATH) -> None:
    """
    Persist the config atomically.
    """
    _ensure_data_dir()
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, sort_keys=True)
    temp.replace(path)


def get_guild_config(guild_id: int, *, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = config or load_config()
    guilds = cfg.setdefault("guilds", {})
    return guilds.setdefault(str(guild_id), {})


def set_guild_config(guild_id: int, key: str, value: Any, *, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = config or load_config()
    guild_cfg = get_guild_config(guild_id, config=cfg)
    guild_cfg[key] = value
    save_config(cfg)
    return guild_cfg


def get_user_config(user_id: int, *, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = config or load_config()
    users = cfg.setdefault("users", {})
    return users.setdefault(str(user_id), {})


def set_user_config(user_id: int, key: str, value: Any, *, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = config or load_config()
    user_cfg = get_user_config(user_id, config=cfg)
    user_cfg[key] = value
    save_config(cfg)
    return user_cfg


def migrate_config(target_version: int = CURRENT_VERSION, *, path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Simple version bump migration. Extend with real steps if schema changes.
    """
    cfg = load_config(path)
    current = int(cfg.get("version", 0))
    if current >= target_version:
        return cfg
    cfg["version"] = target_version
    save_config(cfg, path=path)
    return cfg
