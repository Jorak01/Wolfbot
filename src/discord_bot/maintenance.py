"""
Architecture / maintenance utilities.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import shutil
import time
from pathlib import Path
from typing import Dict, Iterable, List

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"


def dependency_check(packages: Iterable[str]) -> Dict[str, bool]:
    """
    Return a mapping of package -> installed status.
    """
    status: Dict[str, bool] = {}
    for pkg in packages:
        spec = importlib.util.find_spec(pkg)
        status[pkg] = spec is not None
    return status


def version_check(packages: Iterable[str]) -> Dict[str, str | None]:
    """
    Return installed versions for packages; None if missing.
    """
    versions: Dict[str, str | None] = {}
    for pkg in packages:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = None
    return versions


def update_notifier(current_version: str, latest_version: str | None = None) -> str:
    """
    Compare versions and suggest update text. If latest_version is unknown, returns a generic message.
    """
    if latest_version is None:
        return f"Current version: {current_version}. Latest version unknown."
    if latest_version == current_version:
        return f"You are up to date (version {current_version})."
    return f"Update available: {current_version} -> {latest_version}"


def backup_data() -> Path:
    """
    Create a timestamped backup of the data directory.
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"backup-{timestamp}"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError(f"Backup path already exists: {dest}")
    if DATA_DIR.exists():
        shutil.copytree(DATA_DIR, dest)
    else:
        dest.mkdir(parents=True, exist_ok=True)
    return dest


def restore_backup(backup_path: Path) -> Path:
    """
    Restore the contents of a given backup path into the data directory.
    """
    backup_path = backup_path.resolve()
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    shutil.copytree(backup_path, DATA_DIR)
    return DATA_DIR
