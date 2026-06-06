"""Resolve package icons without blocking the GUI thread."""

from __future__ import annotations

import configparser
import logging
import os
import threading
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer

logger = logging.getLogger("knightpac.ui.icons")

_DESKTOP_DIRS = (
    Path("/usr/share/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
    Path.home() / ".local/share/applications",
)
_ICON_THEME_ROOTS = (
    Path.home() / ".icons",
    Path.home() / ".local/share/icons",
    Path("/usr/local/share/icons"),
    Path("/usr/share/icons"),
)
_PIXMAP_DIRS = (
    Path.home() / ".local/share/pixmaps",
    Path("/usr/local/share/pixmaps"),
    Path("/usr/share/pixmaps"),
)
_SIZES = ("scalable", "512x512", "256x256", "192x192", "128x128", "96x96", "64x64", "48x48", "32x32", "24x24", "22x22", "16x16")
_FALLBACK_SVG = Path(__file__).resolve().parent.parent / "assets" / "icons" / "package.svg"
_FALLBACK_THEMES = ("hicolor", "Papirus", "Papirus-Dark", "Papirus-Light", "breeze", "breeze-dark")
_instance_lock = threading.Lock()


@lru_cache(maxsize=4096)
def icon_for_package(package_name: str, declared_icon: str = "") -> QIcon:
    return _icon_from_spec(resolve_icon_spec(package_name, declared_icon))


@lru_cache(maxsize=4096)
def resolve_icon_spec(package_name: str, declared_icon: str = "") -> str:
    resolver = _IconResolver.instance()
    return resolver.resolve_spec(package_name, declared_icon)


def create_icon_request(package_name: str, declared_icon: str = "") -> IconRequest:
    return IconRequest(package_name, declared_icon)


class _IconResolver:
    _instance: _IconResolver | None = None

    def __init__(self) -> None:
        self._desktop_icon: dict[str, str] = {}
        self._theme_cache: dict[str, tuple[str, ...]] = {}
        self._build_desktop_index()

    @classmethod
    def instance(cls) -> _IconResolver:
        if cls._instance is None:
            with _instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def resolve_spec(self, package_name: str, declared_icon: str = "") -> str:
        key = package_name.lower().strip()
        if not key:
            return "fallback"

        candidates = self._icon_candidates(key, declared_icon)
        for icon_name in candidates:
            path = self._absolute_icon(icon_name)
            if path:
                return f"file:{path}"

        for icon_name in candidates:
            themed_path = self._find_in_current_theme(icon_name)
            if themed_path:
                return f"file:{themed_path}"

        for icon_name in candidates:
            themed_path = self._find_in_known_themes(icon_name)
            if themed_path:
                return f"file:{themed_path}"

        return "fallback"

    def _build_desktop_index(self) -> None:
        for directory in _DESKTOP_DIRS:
            if not directory.is_dir():
                continue
            for desktop in directory.rglob("*.desktop"):
                try:
                    data = self._read_desktop(desktop)
                except OSError:
                    continue
                icon_name = data.get("icon", "").strip()
                if not icon_name:
                    continue
                for candidate in self._desktop_candidates(desktop, data):
                    self._desktop_icon.setdefault(candidate, icon_name)

    @staticmethod
    def _read_desktop(path: Path) -> dict[str, str]:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(path, encoding="utf-8")
        if "Desktop Entry" not in parser:
            return {}
        section = parser["Desktop Entry"]
        return {
            "icon": section.get("Icon", section.get("icon", "")),
            "name": section.get("Name", section.get("name", "")),
            "exec": section.get("Exec", section.get("exec", "")),
            "startup_wm_class": section.get(
                "StartupWMClass", section.get("startupwmclass", "")
            ),
        }

    @staticmethod
    def _normalize_token(value: str) -> str:
        clean = value.strip().lower()
        for char in (" ", "_", "."):
            clean = clean.replace(char, "-")
        while "--" in clean:
            clean = clean.replace("--", "-")
        return clean.strip("-")

    def _desktop_candidates(self, desktop: Path, data: dict[str, str]) -> set[str]:
        candidates: set[str] = set()
        candidates.update(self._name_variants(desktop.stem))
        candidates.update(self._name_variants(data.get("name", "")))
        candidates.update(self._name_variants(data.get("startup_wm_class", "")))
        exec_field = data.get("exec", "").split()
        if exec_field:
            candidates.update(self._name_variants(Path(exec_field[0]).name))
        return {candidate for candidate in candidates if candidate}

    def _icon_candidates(self, package_name: str, declared_icon: str) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()
        desktop_icon = self._desktop_icon.get(package_name)
        ordered = [declared_icon, desktop_icon]
        ordered.extend(self._guess_icon_names(package_name))
        for candidate in ordered:
            if not candidate:
                continue
            for name in self._name_variants(candidate):
                if name and name not in seen:
                    candidates.append(name)
                    seen.add(name)
        return candidates

    def _guess_icon_names(self, package_name: str) -> list[str]:
        variants: list[str] = []
        base = self._normalize_token(package_name)
        parts = [part for part in base.split("-") if part]
        variants.extend(
            [
                package_name,
                base,
                package_name.replace("_", "-"),
                package_name.replace("-", ""),
                parts[0] if parts else base,
                base.removesuffix("-git"),
                base.removesuffix("-bin"),
                base.removesuffix("-app"),
                base.removesuffix("-gtk"),
                base.removesuffix("-qt"),
            ]
        )
        return [variant for variant in variants if variant]

    def _absolute_icon(self, icon_name: str) -> Path | None:
        candidate = Path(icon_name)
        if candidate.is_file():
            return candidate
        if candidate.suffix:
            return None
        for directory in _PIXMAP_DIRS:
            for ext in (".svg", ".png", ".xpm"):
                file_path = directory / f"{icon_name}{ext}"
                if file_path.is_file():
                    return file_path
        return None

    def _find_in_known_themes(self, icon_name: str) -> Path | None:
        for theme in self._fallback_theme_order():
            path = self._find_icon_in_theme(theme, icon_name)
            if path:
                return path
        return self._find_in_pixmaps(icon_name)

    def _find_in_current_theme(self, icon_name: str) -> Path | None:
        for theme in self._current_theme_order():
            path = self._find_icon_in_theme(theme, icon_name)
            if path:
                return path
        return None

    def _current_theme_order(self) -> tuple[str, ...]:
        current = [QIcon.themeName(), QIcon.fallbackThemeName(), os.environ.get("ICON_THEME", "")]
        order: list[str] = []
        seen: set[str] = set()
        for theme in current:
            theme = theme.strip()
            if not theme:
                continue
            for inherited in self._theme_with_inherits(theme):
                if inherited not in seen:
                    seen.add(inherited)
                    order.append(inherited)
        return tuple(order)

    def _fallback_theme_order(self) -> tuple[str, ...]:
        order: list[str] = []
        seen = set(self._current_theme_order())
        for theme in _FALLBACK_THEMES:
            if theme not in seen:
                seen.add(theme)
                order.append(theme)
        return tuple(order)

    def _theme_with_inherits(self, theme: str) -> tuple[str, ...]:
        cached = self._theme_cache.get(theme)
        if cached:
            return cached
        ordered: list[str] = [theme]
        index_file = self._find_theme_index(theme)
        if index_file:
            parser = configparser.ConfigParser(interpolation=None)
            try:
                parser.read(index_file, encoding="utf-8")
                inherits = parser.get("Icon Theme", "Inherits", fallback="")
            except (configparser.Error, OSError):
                inherits = ""
            for item in inherits.split(","):
                child = item.strip()
                if child and child not in ordered:
                    ordered.extend(
                        theme_name
                        for theme_name in self._theme_with_inherits(child)
                        if theme_name not in ordered
                    )
        self._theme_cache[theme] = tuple(ordered)
        return self._theme_cache[theme]

    def _find_theme_index(self, theme: str) -> Path | None:
        for root in _ICON_THEME_ROOTS:
            candidate = root / theme / "index.theme"
            if candidate.is_file():
                return candidate
        return None

    def _find_icon_in_theme(self, theme: str, icon_name: str) -> Path | None:
        for root in _ICON_THEME_ROOTS:
            theme_dir = root / theme
            if not theme_dir.is_dir():
                continue
            for size in _SIZES:
                for category in ("apps", "categories", "places", "devices", "mimetypes", "actions"):
                    for ext in (".svg", ".png", ".xpm"):
                        candidate = theme_dir / size / category / f"{icon_name}{ext}"
                        if candidate.is_file():
                            return candidate
            for ext in (".svg", ".png", ".xpm"):
                for candidate in theme_dir.rglob(f"{icon_name}{ext}"):
                    if candidate.is_file():
                        return candidate
        return None

    def _find_in_pixmaps(self, icon_name: str) -> Path | None:
        for directory in _PIXMAP_DIRS:
            if not directory.is_dir():
                continue
            for ext in (".svg", ".png", ".xpm"):
                candidate = directory / f"{icon_name}{ext}"
                if candidate.is_file():
                    return candidate
        return None

    def _name_variants(self, raw: str) -> list[str]:
        normalized = self._normalize_token(raw)
        if not normalized:
            return []
        compact = normalized.replace("-", "")
        variants = [
            raw.strip(),
            normalized,
            compact,
            normalized.replace("-", "_"),
        ]
        parts = normalized.split("-")
        if parts:
            variants.append(parts[0])
        return [variant for variant in variants if variant]

class _IconTaskSignals(QObject):
    resolved = Signal(str, str)


class _IconLookupTask(QRunnable):
    def __init__(self, key: str, package_name: str, declared_icon: str) -> None:
        super().__init__()
        self._key = key
        self._package_name = package_name
        self._declared_icon = declared_icon
        self.signals = _IconTaskSignals()

    def run(self) -> None:
        spec = resolve_icon_spec(self._package_name, self._declared_icon)
        self.signals.resolved.emit(self._key, spec)


class _AsyncIconProvider(QObject):
    icon_resolved = Signal(str, str)
    _instance: _AsyncIconProvider | None = None

    def __init__(self) -> None:
        super().__init__()
        self._pool = QThreadPool.globalInstance()
        self._resolved: dict[str, str] = {}
        self._inflight: set[str] = set()

    @classmethod
    def instance(cls) -> _AsyncIconProvider:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def request(self, package_name: str, declared_icon: str = "") -> str:
        key = _request_key(package_name, declared_icon)
        cached = self._resolved.get(key)
        if cached is not None:
            QTimer.singleShot(0, lambda k=key, spec=cached: self.icon_resolved.emit(k, spec))
            return key
        if key in self._inflight:
            return key
        self._inflight.add(key)
        task = _IconLookupTask(key, package_name, declared_icon)
        task.signals.resolved.connect(self._on_resolved)
        self._pool.start(task)
        return key

    def _on_resolved(self, key: str, spec: str) -> None:
        self._inflight.discard(key)
        self._resolved[key] = spec
        self.icon_resolved.emit(key, spec)


class IconRequest(QObject):
    ready = Signal(QIcon)

    def __init__(self, package_name: str, declared_icon: str = "", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._provider = _AsyncIconProvider.instance()
        self._key = self._provider.request(package_name, declared_icon)
        self._provider.icon_resolved.connect(self._on_icon_resolved)

    def _on_icon_resolved(self, key: str, spec: str) -> None:
        if key != self._key:
            return
        try:
            self._provider.icon_resolved.disconnect(self._on_icon_resolved)
        except (RuntimeError, TypeError):
            pass
        self.ready.emit(_icon_from_spec(spec))


def _request_key(package_name: str, declared_icon: str = "") -> str:
    return f"{package_name.strip().lower()}|{declared_icon.strip().lower()}"


@lru_cache(maxsize=4096)
def _icon_from_spec(spec: str) -> QIcon:
    if spec.startswith("file:"):
        return QIcon(spec.removeprefix("file:"))
    return _fallback_icon()


@lru_cache(maxsize=1)
def _fallback_icon() -> QIcon:
    if _FALLBACK_SVG.is_file():
        renderer = QSvgRenderer(str(_FALLBACK_SVG))
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        from PySide6.QtGui import QPainter

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    return QIcon()
