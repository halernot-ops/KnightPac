"""Bottom terminal log panel with improved IDE-like readability."""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from knightpac.core.terminal_buffer import TerminalBuffer
from knightpac.ui.components.knight_button import KnightButton
from knightpac.ui.components.knight_section import KnightSection
from knightpac.ui.theme import COLORS, LOG_COLORS


_LEVEL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ERROR", re.compile(r"(?i)(error|failed|cancelled|exception)")),
    ("WARNING", re.compile(r"(?i)(warning|warn)")),
    ("SUCCESS", re.compile(r"(?i)(success|loaded \d+|installed|removed|up to date)")),
    ("INFO", re.compile(r"(?i)(loading|search|queued|\$ )")),
)


class TerminalPanel(QWidget):
    cancel_requested = Signal()

    def __init__(self, buffer: TerminalBuffer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buffer = buffer
        self._build_ui()
        self._buffer.line_appended.connect(self._on_line_appended)
        self._buffer.buffer_cleared.connect(self._on_clear)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 6, 10, 10)
        outer.setSpacing(8)

        section = KnightSection("Terminal Panel")
        body = section.body_layout()

        header = QHBoxLayout()
        for level, color in (
            ("INFO", LOG_COLORS["INFO"]),
            ("OK", LOG_COLORS["SUCCESS"]),
            ("WARN", LOG_COLORS["WARNING"]),
            ("ERR", LOG_COLORS["ERROR"]),
        ):
            chip = QLabel(level)
            chip.setStyleSheet(
                f"color: {color}; font-size: 10px; font-weight: 600; padding-right: 8px;"
            )
            header.addWidget(chip)
        header.addStretch()

        self._progress_label = QLabel("")
        self._progress_label.setObjectName("terminalProgress")
        self._progress_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header.addWidget(self._progress_label)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("terminalSearch")
        self._search_input.setPlaceholderText("Search logs...")
        self._search_input.setMaximumWidth(220)
        self._search_input.textChanged.connect(self._highlight_search)
        header.addWidget(self._search_input)

        save_btn = KnightButton("Save", variant="ghost")
        save_btn.clicked.connect(self._save_log)
        header.addWidget(save_btn)
        cancel_btn = KnightButton("Cancel", variant="ghost")
        cancel_btn.clicked.connect(self.cancel_requested.emit)
        header.addWidget(cancel_btn)
        clear_btn = KnightButton("Clear", variant="ghost")
        clear_btn.clicked.connect(self._buffer.clear)
        header.addWidget(clear_btn)
        body.addLayout(header)

        from PySide6.QtWidgets import QPlainTextEdit

        self._output = QPlainTextEdit()
        self._output.setObjectName("terminalOutput")
        self._output.setReadOnly(True)
        self._output.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._output.setTabStopDistance(32)
        font = QFont("JetBrains Mono")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(10)
        self._output.setFont(font)
        copy_action = QAction("Copy", self._output)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self._output.copy)
        self._output.addAction(copy_action)
        body.addWidget(self._output)

        outer.addWidget(section)

        for line in self._buffer.lines():
            self._append_styled(line.text, is_stderr=line.is_stderr)

    def set_progress_text(self, text: str) -> None:
        self._progress_label.setText(text)

    def _classify(self, text: str, *, is_stderr: bool) -> str:
        if is_stderr:
            return "ERROR"
        for level, pattern in _LEVEL_PATTERNS:
            if pattern.search(text):
                return level
        return "DEFAULT"

    def _format_for_level(self, level: str) -> QTextCharFormat:
        fmt = QTextCharFormat()
        color = LOG_COLORS.get(level, LOG_COLORS["DEFAULT"])
        fmt.setForeground(QColor(color))
        if level == "ERROR":
            fmt.setFontWeight(600)
        return fmt

    def _append_styled(self, text: str, *, is_stderr: bool = False) -> None:
        level = self._classify(text, is_stderr=is_stderr)
        channel = "stderr" if is_stderr else "stdout"
        prefix = f"[{channel}] "
        if level in ("ERROR", "WARNING", "SUCCESS") and not text.strip().startswith("["):
            prefix += f"[{level}] "
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(prefix, self._format_for_level(level))
        cursor.insertText(text, self._format_for_level(level))
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    @Slot(str, bool)
    def _on_line_appended(self, text: str, is_stderr: bool) -> None:
        self._append_styled(text, is_stderr=is_stderr)

    def _on_clear(self) -> None:
        self._output.clear()

    def _highlight_search(self, term: str) -> None:
        cursor = self._output.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        fmt.setBackground(Qt.GlobalColor.transparent)
        cursor.setCharFormat(fmt)
        cursor.clearSelection()
        if not term:
            return
        doc = self._output.document()
        highlight = QTextCharFormat()
        highlight.setBackground(QColor("#4A4000"))
        pos = 0
        while True:
            found = doc.find(term, pos)
            if found.isNull():
                break
            found.mergeCharFormat(highlight)
            pos = found.position() + len(term)

    def _save_log(self) -> None:
        path = self._buffer.save_to_file()
        self._buffer.append_stdout(f"\n[Saved log to {path}]\n")
