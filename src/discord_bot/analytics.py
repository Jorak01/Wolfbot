"""
Simple in-memory + file-backed analytics and logging helpers.
"""

from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_FILE = DATA_DIR / "events.log"
STATS_FILE = DATA_DIR / "usage.json"

_USAGE: Dict[str, Any] = {"commands": {}, "events": []}


def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_usage():
    _ensure_dirs()
    if STATS_FILE.exists():
        try:
            _USAGE.update(json.loads(STATS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass


def _save_usage():
    _ensure_dirs()
    with STATS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(_USAGE, fh, indent=2, sort_keys=True)


def log_event(event_type: str, data: Dict[str, Any]):
    _ensure_dirs()
    entry = {"type": event_type, "data": data}
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    _USAGE.setdefault("events", []).append(entry)
    _save_usage()


def log_command_usage(user_id: int, command: str):
    _load_usage()
    per_cmd = _USAGE.setdefault("commands", {})
    info = per_cmd.setdefault(command, {"count": 0, "users": {}})
    info["count"] = info.get("count", 0) + 1
    info["users"][str(user_id)] = info["users"].get(str(user_id), 0) + 1
    _save_usage()


def log_error(exception: Exception):
    tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    log_event("error", {"traceback": tb})


def get_usage_stats() -> Dict[str, Any]:
    _load_usage()
    return _USAGE


def audit_log_lookup(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Return last `limit` event entries from the log file (if present).
    """
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    selected = lines[-limit:]
    events: List[Dict[str, Any]] = []
    for line in selected:
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events
