"""Unified package data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    PACMAN = "PACMAN"
    AUR = "AUR"
    APT = "APT"
    DNF = "DNF"
    ZYPPER = "ZYPPER"
    FLATPAK = "FLATPAK"
    SNAP = "SNAP"


_DISPLAY_SOURCE = {
    SourceType.PACMAN: "Official",
    SourceType.AUR: "AUR",
    SourceType.APT: "APT",
    SourceType.DNF: "DNF",
    SourceType.ZYPPER: "ZYPPER",
    SourceType.FLATPAK: "Flatpak",
    SourceType.SNAP: "Snap",
}


@dataclass
class Package:
    name: str
    version: str = ""
    description: str = ""
    source_type: SourceType = SourceType.PACMAN
    repository: str = ""
    architecture: str = ""
    size: str = ""
    installed_size: str = ""
    installed: bool = False
    update_available: bool = False
    dependencies: list[str] = field(default_factory=list)
    manager: str = ""
    installed_date: datetime | None = None
    icon: str = ""

    @property
    def display_source(self) -> str:
        if self.installed and not self.update_available:
            return "Installed"
        return _DISPLAY_SOURCE.get(self.source_type, self.source_type.value)

    @property
    def source(self) -> SourceType:
        """Compatibility alias used by legacy call sites."""
        return self.source_type
