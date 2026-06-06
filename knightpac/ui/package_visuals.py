"""Helpers for consistent package presentation across the UI."""

from __future__ import annotations

from knightpac.models.operation import OperationType
from knightpac.models.package import Package, SourceType

_SOURCE_BADGES = {
    SourceType.PACMAN: ("Official", "accent"),
    SourceType.AUR: ("AUR", "warning"),
    SourceType.FLATPAK: ("Flatpak", "neutral"),
}

_ICON_BY_SOURCE = {
    SourceType.PACMAN: "package",
    SourceType.AUR: "aur",
    SourceType.FLATPAK: "package",
}


def package_badges(package: Package) -> list[tuple[str, str]]:
    badges: list[tuple[str, str]] = []
    source_badge = _SOURCE_BADGES.get(package.source_type)
    if source_badge:
        badges.append(source_badge)
    if package.installed:
        badges.append(("Installed", "success"))
    if package.update_available:
        badges.append(("Update Available", "warning"))
    return badges


def package_icon_name(package: Package) -> str:
    return _ICON_BY_SOURCE.get(package.source_type, "package")


def primary_action(package: Package) -> tuple[str, str, OperationType | None]:
    if package.update_available:
        return "Update", "primary", OperationType.UPDATE
    if package.installed:
        return "Remove", "danger", OperationType.REMOVE
    return "Install", "primary", OperationType.INSTALL
