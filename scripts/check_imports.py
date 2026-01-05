"""
Verify required third-party packages and keep requirements.txt in sync with imports.
"""

from __future__ import annotations

import ast
import importlib
import importlib.metadata
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS_PATH = ROOT_DIR / "requirements.txt"

PACKAGE_MAP = {
    "discord": "discord.py",
    "dotenv": "python-dotenv",
    "duckduckgo_search": "duckduckgo-search",
    "yt_dlp": "yt-dlp",
}


def _iter_py_files() -> Iterable[Path]:
    """Iterate over all Python files in src/, tests/, and scripts/."""
    for root, dirs, files in os.walk(ROOT_DIR):
        # Skip virtualenvs and caches.
        dirs[:] = [
            d
            for d in dirs
            if d not in {".venv", "__pycache__", ".pytest_cache", ".git", "node_modules"}
        ]
        for name in files:
            if name.endswith(".py"):
                yield Path(root) / name


def _stdlib_names() -> Set[str]:
    names = set(sys.builtin_module_names)
    names.update(getattr(sys, "stdlib_module_names", set()))
    return names


def _discover_imports() -> Set[str]:
    modules: Set[str] = set()
    for path in _iter_py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import
                if node.module:
                    modules.add(node.module.split(".")[0])
    return modules


def _filter_third_party(modules: Iterable[str]) -> Set[str]:
    stdlib = _stdlib_names()
    third_party: Set[str] = set()
    for mod in modules:
        if mod in stdlib:
            continue
        if mod in {"src", "scripts"}:
            continue
        # If it's importable as a local module path under src, skip.
        # Check both as directory and as .py file
        local_dir = ROOT_DIR / "src" / mod
        local_file = ROOT_DIR / "src" / f"{mod}.py"
        if local_dir.exists() or local_file.exists():
            continue
        third_party.add(mod)
    return third_party


def _modules_to_packages(modules: Iterable[str]) -> Set[str]:
    packages: Set[str] = set()
    dist_map = importlib.metadata.packages_distributions()
    for mod in modules:
        if mod in PACKAGE_MAP:
            packages.add(PACKAGE_MAP[mod])
            continue
        dists = dist_map.get(mod)
        if dists:
            packages.add(dists[0])
        else:
            packages.add(mod)
    return packages


def _parse_requirements(lines: List[str]) -> Tuple[List[str], Set[str]]:
    entries: List[str] = []
    names: Set[str] = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
        name = re.split(r"[<>=]", line, 1)[0].strip()
        if name:
            names.add(name)
    return entries, names


def _write_requirements(existing: List[str], new_packages: Set[str]) -> None:
    if not new_packages:
        return
    updated = existing + sorted(new_packages)
    REQUIREMENTS_PATH.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _installed(package: str) -> bool:
    try:
        importlib.metadata.version(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def _install_missing(packages: Iterable[str]) -> List[str]:
    missing: List[str] = []
    for pkg in packages:
        if _installed(pkg):
            continue
        missing.append(pkg)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            check=False,
        )
    return missing


def main() -> int:
    discovered_modules = _discover_imports()
    third_party = _filter_third_party(discovered_modules)
    discovered_packages = _modules_to_packages(third_party)

    print(f"Discovered {len(discovered_modules)} total modules")
    print(f"Found {len(third_party)} third-party modules: {sorted(third_party)}")
    print(f"Mapped to {len(discovered_packages)} packages: {sorted(discovered_packages)}")

    if REQUIREMENTS_PATH.exists():
        existing_lines = REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
    else:
        existing_lines = []
    existing_entries, existing_names = _parse_requirements(existing_lines)

    new_packages = {pkg for pkg in discovered_packages if pkg not in existing_names}
    if new_packages:
        print(f"Adding {len(new_packages)} new packages to requirements.txt: {sorted(new_packages)}")
        _write_requirements(existing_entries, new_packages)
    else:
        print("No new packages to add to requirements.txt")

    # Install missing packages from requirements.
    _, names = _parse_requirements(existing_entries + sorted(new_packages))
    missing = _install_missing(sorted(names))
    if missing:
        print("Installed missing packages:")
        for pkg in missing:
            print(f"  - {pkg}")
    else:
        print("All required packages are already installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
