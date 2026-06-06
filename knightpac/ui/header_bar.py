"""Top header with search, filter, and sync."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from knightpac.ui.theme import COLORS

FILTERS = ["All", "Official", "AUR", "Installed", "Updates"]


class HeaderBar(QWidget):
    search_requested = Signal(str, str)
    sync_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(68)
        self.setStyleSheet(
            f"background-color: {COLORS['panel']}; border-bottom: 1px solid {COLORS['border']};"
        )
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(500)
        self._debounce.timeout.connect(self._emit_search)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(14)

        title = QLabel("Packages")
        title.setStyleSheet(
            f"color: {COLORS['text']}; font-size: 15px; font-weight: 700; padding-right: 2px;"
        )
        layout.addWidget(title)

        self._search = QLineEdit()
        self._search.setObjectName("headerSearch")
        self._search.setPlaceholderText("Search packages...")
        self._search.setClearButtonEnabled(True)
        self._search.setMinimumWidth(360)
        self._search.setMinimumHeight(40)
        search_icon = QIcon.fromTheme("search")
        if not search_icon.isNull():
            self._search.addAction(search_icon, QLineEdit.ActionPosition.LeadingPosition)
        self._search.textChanged.connect(self._on_text_changed)
        self._search.returnPressed.connect(self._emit_search)
        layout.addWidget(self._search)

        filter_label = QLabel("Filter")
        filter_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600;"
        )
        layout.addWidget(filter_label)
        self._filter = QComboBox()
        self._filter.setObjectName("headerFilter")
        self._filter.addItems(FILTERS)
        self._filter.setMinimumHeight(40)
        self._filter.setMinimumWidth(130)
        self._filter.currentTextChanged.connect(lambda _: self._emit_search())
        layout.addWidget(self._filter)

        layout.addStretch()

        sync_btn = QPushButton("Sync Databases")
        sync_btn.setObjectName("accentButton")
        sync_btn.setMinimumHeight(40)
        sync_btn.clicked.connect(self.sync_requested.emit)
        layout.addWidget(sync_btn)

    def _on_text_changed(self) -> None:
        self._debounce.stop()
        self._debounce.start()

    def _emit_search(self) -> None:
        self.search_requested.emit(self._search.text().strip(), self._filter.currentText())

    def current_filter(self) -> str:
        return self._filter.currentText()

    def set_query(self, text: str) -> None:
        self._search.setText(text)
