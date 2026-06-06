"""System diagnostics page."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from knightpac.services.diagnostics_service import DiagnosticItem
from knightpac.ui.theme import COLORS


class DiagnosticsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("System Diagnostics")
        title.setObjectName("title")
        layout.addWidget(title)
        self._refresh_btn = QPushButton("Refresh")
        layout.addWidget(self._refresh_btn)
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Component", "Details", "Status"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

    def set_items(self, items: list[DiagnosticItem]) -> None:
        self._table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._table.setItem(row, 0, QTableWidgetItem(item.name))
            self._table.setItem(row, 1, QTableWidgetItem(item.value))
            status_item = QTableWidgetItem(item.status)
            color = QColor(COLORS["success"] if item.status == "OK" else COLORS["error"])
            status_item.setForeground(color)
            self._table.setItem(row, 2, status_item)
