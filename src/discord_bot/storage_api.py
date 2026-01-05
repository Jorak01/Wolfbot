"""
Storage and external API helpers.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "db.sqlite3"

_CACHE: Dict[str, tuple[Any, float | None]] = {}


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def database_connect() -> sqlite3.Connection:
    """
    Return a sqlite connection (file stored under data/).
    """
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    return conn


def database_query(query: str, params: tuple[Any, ...] | None = None) -> list[tuple]:
    """
    Run a simple read-only query and return rows.
    """
    params = params or ()
    with database_connect() as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()
    return rows


def cache_get(key: str) -> Any:
    """
    Return cached value if not expired; otherwise None.
    """
    entry = _CACHE.get(key)
    if not entry:
        return None
    value, expires = entry
    if expires is not None and time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return value


def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    expires = time.time() + ttl if ttl else None
    _CACHE[key] = (value, expires)


def fetch_api_json(url: str, *, timeout: float = 10.0) -> dict[str, Any]:
    """
    Fetch JSON from an HTTP endpoint (GET).
    """
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def retry_request(
    func: Callable[[], Any],
    *,
    retries: int = 3,
    delay_seconds: float = 1.0,
) -> Any:
    """
    Run a callable with basic retry/backoff.
    """
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if attempt == retries - 1:
                break
            time.sleep(delay_seconds * (attempt + 1))
    if last_error:
        raise last_error
