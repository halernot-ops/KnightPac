"""Package manager registry — GUI never imports concrete backends."""

from __future__ import annotations

import importlib
import logging
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knightpac.backend.plugin import PackageManagerPlugin
    from knightpac.core.process_runner import ProcessRunner

logger = logging.getLogger("knightpac.registry")

_BUILTIN_PLUGINS: tuple[tuple[str, str, str], ...] = (
    ("pacman", "knightpac.backend.pacman_manager", "PacmanManager"),
    ("paru", "knightpac.backend.paru_manager", "ParuManager"),
    ("flatpak", "knightpac.backend.flatpak_manager", "FlatpakManager"),
)


class PackageManagerRegistry:
    def __init__(self) -> None:
        self._managers: dict[str, PackageManagerPlugin] = {}

    def register(self, manager: PackageManagerPlugin) -> None:
        self._managers[manager.name] = manager
        logger.debug("Registered package manager: %s", manager.name)

    def get(self, name: str) -> PackageManagerPlugin | None:
        return self._managers.get(name)

    def list_managers(self) -> list[PackageManagerPlugin]:
        return list(self._managers.values())

    def primary(self) -> PackageManagerPlugin | None:
        return self.get("pacman") or (self.list_managers()[0] if self._managers else None)


def autodiscover(runner: ProcessRunner) -> PackageManagerRegistry:
    registry = PackageManagerRegistry()
    for binary, module_path, class_name in _BUILTIN_PLUGINS:
        if not shutil.which(binary):
            continue
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            registry.register(cls(runner))
        except (ImportError, AttributeError) as exc:
            logger.warning("Could not load plugin %s: %s", class_name, exc)
    return registry
