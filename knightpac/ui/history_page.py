"""Operation history page with filters and export."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from knightpac.models.history import HistoryRecord
from knightpac.ui.theme import COLORS

_FILTER_OPTIONS = [
    ("all", "All"),
    ("install", "Install"),
    ("remove", "Remove"),
    ("update", "Update"),
    ("failed", "Failed"),
]


class HistoryPage(QWidget):
    filter_changed = Signal(str, str)
    export_csv_requested = Signal()
    export_json_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._records: list[HistoryRecord] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Filter:"))
        self._filter = QComboBox()
        for _key, label in _FILTER_OPTIONS:
            self._filter.addItem(label)
        self._filter.currentIndexChanged.connect(self._emit_filter)
        toolbar.addWidget(self._filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search history...")
        self._search.textChanged.connect(self._emit_filter)
        toolbar.addWidget(self._search, 1)

        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_csv_requested.emit)
        toolbar.addWidget(csv_btn)
        json_btn = QPushButton("Export JSON")
        json_btn.clicked.connect(self.export_json_requested.emit)
        toolbar.addWidget(json_btn)
        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Date", "Operation", "Package", "Result"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

    def _emit_filter(self) -> None:
        key = _FILTER_OPTIONS[self._filter.currentIndex()][0]
        self.filter_changed.emit(key, self._search.text().strip())

    def current_filter(self) -> tuple[str, str]:
        key = _FILTER_OPTIONS[self._filter.currentIndex()][0]
        return key, self._search.text().strip()

    def set_history(self, entries: list[HistoryRecord]) -> None:
        self._records = entries
        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._table.setItem(
                row, 0, QTableWidgetItem(entry.timestamp.strftime("%Y-%m-%d %H:%M"))
            )
            self._table.setItem(row, 1, QTableWidgetItem(entry.action))
            self._table.setItem(row, 2, QTableWidgetItem(entry.package))
            result_item = QTableWidgetItem(entry.result)
            color = QColor(COLORS["success"] if entry.result == "SUCCESS" else COLORS["error"])
            result_item.setForeground(color)
            self._table.setItem(row, 3, result_item)

    def records(self) -> list[HistoryRecord]:
        return self._records
