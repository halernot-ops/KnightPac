"""Pacman cache cleaner page."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from knightpac.ui.theme import COLORS


class CachePage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Cache Cleaner")
        title.setObjectName("title")
        layout.addWidget(title)
        self._size_label = QLabel("Cache size: calculating...")
        self._size_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        layout.addWidget(self._size_label)
        path = QLabel("/var/cache/pacman/pkg")
        path.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(path)
        btn_row = QHBoxLayout()
        self._clear_old_btn = QPushButton("Clear Old Packages")
        self._clear_all_btn = QPushButton("Clear All Cache")
        self._clear_all_btn.setObjectName("dangerButton")
        btn_row.addWidget(self._clear_old_btn)
        btn_row.addWidget(self._clear_all_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()

    def set_cache_size(self, size: str) -> None:
        self._size_label.setText(f"Cache size: {size}")
