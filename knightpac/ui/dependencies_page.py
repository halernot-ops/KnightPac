"""Standalone dependencies explorer page."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from knightpac.models.dependency import DependencyNode
from knightpac.ui.theme import COLORS


class DependenciesPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        hint = QLabel("Enter a package name and load its dependency tree.")
        hint.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(hint)
        row = QWidget()
        from PySide6.QtWidgets import QHBoxLayout

        row_layout = QHBoxLayout(row)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Package name...")
        row_layout.addWidget(self._input)
        self._load_btn = QPushButton("Load Tree")
        row_layout.addWidget(self._load_btn)
        layout.addWidget(row)
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        layout.addWidget(self._tree)

    def set_tree(self, root: DependencyNode | None) -> None:
        self._tree.clear()
        if root:
            self._tree.addTopLevelItem(self._to_item(root))

    def _to_item(self, node: DependencyNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([node.name])
        for child in node.children:
            item.addChild(self._to_item(child))
        return item

    @property
    def package_name(self) -> str:
        return self._input.text().strip()
