"""SVG icon access helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QIcon

_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


@lru_cache(maxsize=64)
def icon(name: str) -> QIcon:
    path = _ICON_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    fallback = _ICON_DIR / "package.svg"
    return QIcon(str(fallback)) if fallback.exists() else QIcon()


def icon_path(name: str) -> Path:
    path = _ICON_DIR / f"{name}.svg"
    return path if path.exists() else _ICON_DIR / "package.svg"
