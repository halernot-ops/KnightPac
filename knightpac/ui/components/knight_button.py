"""KnightPac button component."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton

from knightpac.ui.theme import COLORS


class KnightButton(QPushButton):
    VARIANTS = {
        "default": "",
        "accent": "accentButton",
        "ghost": "ghostButton",
        "danger": "dangerButton",
        "small": "smallButton",
    }

    def __init__(
        self,
        text: str = "",
        *,
        variant: str = "default",
        parent=None,
    ) -> None:
        super().__init__(text, parent)
        obj_name = self.VARIANTS.get(variant, "")
        if obj_name:
            self.setObjectName(obj_name)
        self.setCursor(self.cursor())
        self._apply_cursor()

    def _apply_cursor(self) -> None:
        from PySide6.QtCore import Qt

        self.setCursor(Qt.CursorShape.PointingHandCursor)
