"""About page — branding."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from knightpac import __version__
from knightpac.ui.components.knight_card import KnightCard
from knightpac.ui.theme import COLORS

_ICON = Path(__file__).resolve().parent.parent / "assets" / "icons" / "knightpac.svg"


class AboutPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = KnightCard(hover=False)
        card.setMaximumWidth(520)
        inner = card.content_layout()
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.setSpacing(14)

        if _ICON.is_file():
            logo = QLabel()
            logo.setPixmap(QIcon(str(_ICON)).pixmap(96, 96))
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inner.addWidget(logo)

        title = QLabel("KnightPac")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(28)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLORS['accent']};")
        inner.addWidget(title)

        subtitle = QLabel("Premium Linux Package Manager")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        inner.addWidget(subtitle)

        version = QLabel(f"Version {__version__}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"color: {COLORS['text_muted']};")
        inner.addWidget(version)

        divider = QLabel("—")
        divider.setAlignment(Qt.AlignmentFlag.AlignCenter)
        divider.setStyleSheet(f"color: {COLORS['border']};")
        inner.addWidget(divider)

        desc = QLabel(
            "A modern graphical package manager for Arch Linux and beyond.\n\n"
            "Dark metal interface with gold accents. Built on a modular plugin "
            "architecture — pacman, paru, and flatpak supported today.\n\n"
            "The GUI never talks to package managers directly. All operations "
            "flow through the Package Service layer."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.6; padding: 8px;"
        )
        inner.addWidget(desc)

        layout.addWidget(card)
        layout.addStretch()
