"""Right panel with polished package details and tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from knightpac.models.dependency import DependencyNode
from knightpac.models.package import Package
from knightpac.ui.components.knight_button import KnightButton
from knightpac.ui.icon_resolver import create_icon_request
from knightpac.ui.theme import COLORS


class PackageDetailsPanel(QWidget):
    install_clicked = Signal(object)
    reinstall_clicked = Signal(object)
    remove_clicked = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._package: Package | None = None
        self._icon_request = None
        self.setMinimumWidth(300)
        self.setStyleSheet(f"background-color: {COLORS['panel']};")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self._placeholder = QLabel("Select a package card to view details")
        self._placeholder.setObjectName("secondary")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 14px; padding: 24px;"
        )
        layout.addWidget(self._placeholder)

        self._content = QWidget()
        content_layout = QVBoxLayout(self._content)
        name_row = QHBoxLayout()
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(40, 40)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_row.addWidget(self._icon_label)
        self._name_label = QLabel()
        self._name_label.setObjectName("title")
        name_row.addWidget(self._name_label, 1)
        content_layout.addLayout(name_row)

        self._meta = QLabel()
        self._meta.setWordWrap(True)
        self._meta.setStyleSheet(f"color: {COLORS['text_secondary']};")
        content_layout.addWidget(self._meta)

        self._tabs = QTabWidget()
        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._deps_tree = QTreeWidget()
        self._deps_tree.setHeaderHidden(True)
        self._files_list = QTextEdit()
        self._files_list.setReadOnly(True)
        self._changelog = QTextEdit()
        self._changelog.setReadOnly(True)
        self._tabs.addTab(self._details_text, "Details")
        self._tabs.addTab(self._deps_tree, "Dependencies")
        self._tabs.addTab(self._files_list, "Files")
        self._tabs.addTab(self._changelog, "Changelog")
        content_layout.addWidget(self._tabs)

        btn_row = QHBoxLayout()
        self._install_btn = KnightButton("Install", variant="accent")
        self._install_btn.clicked.connect(self._on_install)
        self._reinstall_btn = KnightButton("Reinstall", variant="ghost")
        self._reinstall_btn.clicked.connect(self._on_reinstall)
        self._remove_btn = KnightButton("Remove", variant="danger")
        self._remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self._install_btn)
        btn_row.addWidget(self._reinstall_btn)
        btn_row.addWidget(self._remove_btn)
        content_layout.addLayout(btn_row)

        self._content.hide()
        layout.addWidget(self._content)
        layout.addStretch()

    def clear(self) -> None:
        self._package = None
        self._placeholder.show()
        self._content.hide()

    def show_package(self, package: Package, detail_text: str, meta_lines: list[str]) -> None:
        self._package = package
        self._placeholder.hide()
        self._content.show()
        self._name_label.setText(package.name)
        self._icon_label.setPixmap(QPixmap())
        self._icon_label.setText("PKG")
        self._icon_label.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 11px; font-weight: 700;"
        )
        self._icon_request = create_icon_request(package.name, package.icon)
        self._icon_request.setParent(self)
        self._icon_request.ready.connect(self._apply_icon)
        self._meta.setText("\n".join(meta_lines))
        self._details_text.setPlainText(detail_text)

    def _apply_icon(self, icon) -> None:
        pixmap = icon.pixmap(32, 32)
        if pixmap.isNull():
            return
        self._icon_label.setText("")
        self._icon_label.setPixmap(pixmap)

    def set_dependency_tree(self, root: DependencyNode) -> None:
        self._deps_tree.clear()
        self._deps_tree.addTopLevelItem(self._node_to_item(root))

    def _node_to_item(self, node: DependencyNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([node.name])
        for child in node.children:
            item.addChild(self._node_to_item(child))
        return item

    def set_files(self, files: list[str]) -> None:
        self._files_list.setPlainText("\n".join(files) if files else "No files listed.")

    def set_changelog(self, text: str) -> None:
        self._changelog.setPlainText(text or "No changelog available.")

    def _on_install(self) -> None:
        if self._package:
            self.install_clicked.emit(self._package)

    def _on_reinstall(self) -> None:
        if self._package:
            self.reinstall_clicked.emit(self._package)

    def _on_remove(self) -> None:
        if self._package:
            self.remove_clicked.emit(self._package)
