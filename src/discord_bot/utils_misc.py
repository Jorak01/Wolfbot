"""
Miscellaneous utility functions.
"""

from __future__ import annotations

import re
import textwrap
import time
import uuid
from typing import List


def parse_duration(expr: str) -> int:
    """
    Parse duration strings like '1h30m', '45m', '10s' into seconds.
    """
    expr = expr.strip().lower()
    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    match = re.fullmatch(pattern, expr)
    if not match:
        raise ValueError("Invalid duration expression")
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_time(timestamp: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def sanitize_input(text: str) -> str:
    return text.strip()


def truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3] + "..."


def chunk_message(text: str, limit: int = 1900) -> List[str]:
    if len(text) <= limit:
        return [text]
    return textwrap.wrap(text, width=limit, break_long_words=True, break_on_hyphens=False)


def validate_url(url: str) -> bool:
    pattern = re.compile(r"^(https?://)[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$")
    return bool(pattern.match(url))


def generate_uuid() -> str:
    return str(uuid.uuid4())
