"""Dashboard statistic tile."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from knightpac.ui.components.knight_card import KnightCard
from knightpac.ui.theme import COLORS


class DashboardStatCard(KnightCard):
    def __init__(
        self,
        title: str,
        value: str = "—",
        subtitle: str = "",
        *,
        accent: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent, hover=True)
        self.setMinimumHeight(110)
        layout = self.content_layout()
        self._title = QLabel(title)
        self._title.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 500;"
        )
        layout.addWidget(self._title)
        self._value = QLabel(value)
        value_color = COLORS["accent"] if accent else COLORS["text"]
        self._value.setStyleSheet(
            f"color: {value_color}; font-size: 28px; font-weight: 700;"
        )
        layout.addWidget(self._value)
        self._subtitle = QLabel(subtitle)
        self._subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self._subtitle)
        layout.addStretch()

    def set_value(self, value: str, subtitle: str = "") -> None:
        self._value.setText(value)
        if subtitle:
            self._subtitle.setText(subtitle)
