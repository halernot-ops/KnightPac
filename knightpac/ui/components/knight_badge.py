"""KnightPac badge label."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from knightpac.ui.theme import BADGE_VARIANTS, COLORS


class KnightBadge(QLabel):
    def __init__(self, text: str, *, variant: str = "default", parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_variant(variant)

    def set_variant(self, variant: str) -> None:
        colors = BADGE_VARIANTS.get(variant, BADGE_VARIANTS["default"])
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {colors['fg']};
                background-color: {colors['bg']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            """
        )

    @staticmethod
    def for_source(source_label: str) -> KnightBadge:
        mapping = {
            "Official": "official",
            "AUR": "aur",
            "Installed": "installed",
            "Flatpak": "flatpak",
        }
        return KnightBadge(source_label, variant=mapping.get(source_label, "default"))
