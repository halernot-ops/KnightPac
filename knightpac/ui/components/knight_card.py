"""KnightPac card container."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from knightpac.ui.theme import COLORS, RADIUS


class KnightCard(QFrame):
    def __init__(self, parent: QWidget | None = None, *, hover: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("KnightCard")
        self._hover = hover
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)
        self._apply_style()

    def _apply_style(self) -> None:
        hover_rule = ""
        if self._hover:
            hover_rule = f"KnightCard:hover {{ border-color: {COLORS['accent']}; }}"
        self.setStyleSheet(
            f"""
            KnightCard {{
                background-color: {COLORS['panel']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['lg']}px;
            }}
            {hover_rule}
            """
        )

    def content_layout(self) -> QVBoxLayout:
        return self._layout
