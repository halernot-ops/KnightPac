"""Terminal output buffer — storage separate from GUI widgets."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal


@dataclass
class TerminalLine:
    text: str
    is_stderr: bool
    timestamp: datetime


class TerminalBuffer(QObject):
    """Stores command output; GUI subscribes via signals."""

    line_appended = Signal(str, bool)
    buffer_cleared = Signal()

    def __init__(self, max_lines: int = 10_000, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._max_lines = max_lines
        self._lines: deque[TerminalLine] = deque(maxlen=max_lines)

    def append_stdout(self, text: str) -> None:
        self._append(text, is_stderr=False)

    def append_stderr(self, text: str) -> None:
        self._append(text, is_stderr=True)

    def append(self, text: str, *, is_stderr: bool = False) -> None:
        self._append(text, is_stderr=is_stderr)

    def _append(self, text: str, *, is_stderr: bool) -> None:
        if not text:
            return
        line = TerminalLine(text=text, is_stderr=is_stderr, timestamp=datetime.now())
        self._lines.append(line)
        self.line_appended.emit(text, is_stderr)

    def full_text(self) -> str:
        return "".join(line.text for line in self._lines)

    def lines(self) -> list[TerminalLine]:
        return list(self._lines)

    def clear(self) -> None:
        self._lines.clear()
        self.buffer_cleared.emit()

    def trim_to_max_bytes(self, max_bytes: int) -> None:
        while self._lines and len(self.full_text().encode("utf-8")) > max_bytes:
            self._lines.popleft()

    def save_to_file(self, path: Path | None = None) -> Path:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        if path is None:
            path = log_dir / f"terminal_{datetime.now():%Y%m%d_%H%M%S}.log"
        path.write_text(self.full_text(), encoding="utf-8")
        return path
