"""KnightPac section with title."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from knightpac.ui.theme import COLORS


class KnightSection(QWidget):
    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        if title:
            heading = QLabel(title)
            heading.setObjectName("sectionTitle")
            heading.setStyleSheet(
                f"color: {COLORS['accent']}; font-size: 13px; font-weight: 600; letter-spacing: 0.5px;"
            )
            root.addWidget(heading)
        self._body = QVBoxLayout()
        self._body.setSpacing(8)
        root.addLayout(self._body)

    def body_layout(self) -> QVBoxLayout:
        return self._body
