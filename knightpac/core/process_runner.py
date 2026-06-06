"""Async QProcess wrapper with timeout, cancel, and output throttling."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

from PySide6.QtCore import QProcess, QProcessEnvironment

from knightpac.core.progress_parser import parse_output_line
from knightpac.core.terminal_buffer import TerminalBuffer
from knightpac.models.operation_progress import OperationProgress

logger = logging.getLogger("knightpac.process")

DEFAULT_TIMEOUT_SEC = 3600.0
_START_TIMEOUT_MS = 10_000
_FLUSH_INTERVAL_SEC = 0.05
_MAX_CHUNK_BYTES = 65_536


class ProcessCancelled(Exception):
    """Raised when an operation is cancelled by the user."""


class ProcessTimeout(Exception):
    """Raised when an operation exceeds its time limit."""


class ProcessRunner:
    """Runs external commands via QProcess without blocking the GUI."""

    def __init__(self, terminal: TerminalBuffer) -> None:
        self._terminal = terminal
        self._active: QProcess | None = None
        self._cancel_requested = False
        self._progress_callback: Callable[[OperationProgress], None] | None = None
        self._progress = OperationProgress(total_steps=4)
        self._progress_manager = "pacman"
        self._pending_stdout: list[str] = []
        self._pending_stderr: list[str] = []
        self._last_flush = 0.0
        self._echo_terminal = True

    def user_message(self, message: str) -> None:
        """Short status line for the UI terminal (not a shell command)."""
        self._terminal.append_stdout(f"\n{message}\n")

    def set_progress_callback(
        self, callback: Callable[[OperationProgress], None] | None, *, manager: str = "pacman"
    ) -> None:
        self._progress_callback = callback
        self._progress_manager = manager
        self._progress = OperationProgress(total_steps=4)

    def request_cancel(self) -> None:
        self._cancel_requested = True
        process = self._active
        if process is None:
            return
        state = process.state()
        if state != QProcess.ProcessState.NotRunning:
            logger.debug("Killing process %s (cancel requested)", process.program())
            process.kill()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def _emit_progress(self, line: str) -> None:
        if not self._progress_callback or not self._echo_terminal:
            return
        parse_output_line(line, self._progress, manager=self._progress_manager)
        self._progress_callback(self._progress)

    def _flush_terminal(self, force: bool = False) -> None:
        if not self._echo_terminal:
            return
        now = time.monotonic()
        if not force and (now - self._last_flush) < _FLUSH_INTERVAL_SEC:
            if sum(len(s) for s in self._pending_stdout) < _MAX_CHUNK_BYTES:
                return
        if self._pending_stdout:
            self._terminal.append_stdout("".join(self._pending_stdout))
            self._pending_stdout.clear()
        if self._pending_stderr:
            self._terminal.append_stderr("".join(self._pending_stderr))
            self._pending_stderr.clear()
        self._last_flush = now

    def _buffer_line(self, text: str, *, stderr: bool) -> None:
        if not self._echo_terminal:
            return
        for line in text.splitlines(keepends=True):
            if stderr:
                self._pending_stderr.append(line)
            else:
                self._pending_stdout.append(line)
                if line.strip():
                    self._emit_progress(line)
        self._flush_terminal()

    async def run(
        self,
        program: str,
        args: list[str] | None = None,
        *,
        use_pkexec: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SEC,
        echo_terminal: bool = True,
    ) -> tuple[int, str, str]:
        args = args or []
        if use_pkexec:
            program, args = "pkexec", [program, *args]

        self._cancel_requested = False
        self._echo_terminal = echo_terminal
        logger.debug("Running: %s %s", program, " ".join(args))
        if echo_terminal:
            self._terminal.append_stdout(f"$ {program} {' '.join(args)}\n")

        process = QProcess()
        process.setProgram(program)
        process.setArguments(args)
        env = QProcessEnvironment.systemEnvironment()
        process.setProcessEnvironment(env)

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        done = asyncio.Event()
        exit_code = -1

        def on_ready_read_stdout() -> None:
            data = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
            if data:
                stdout_chunks.append(data)
                self._buffer_line(data, stderr=False)

        def on_ready_read_stderr() -> None:
            data = bytes(process.readAllStandardError()).decode("utf-8", errors="replace")
            if data:
                stderr_chunks.append(data)
                self._buffer_line(data, stderr=True)

        def on_finished(code: int, _status: QProcess.ExitStatus) -> None:
            nonlocal exit_code
            exit_code = code
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(done.set)

        process.readyReadStandardOutput.connect(on_ready_read_stdout)
        process.readyReadStandardError.connect(on_ready_read_stderr)
        process.finished.connect(on_finished)

        self._active = process
        try:
            process.start()
            if not process.waitForStarted(_START_TIMEOUT_MS):
                msg = f"Failed to start: {program}"
                logger.error(msg)
                if echo_terminal:
                    self._terminal.append_stderr(f"ERROR: {msg}\n")
                return -1, "", msg

            try:
                await asyncio.wait_for(done.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error("Process timed out: %s", program)
                process.kill()
                process.waitForFinished(5000)
                if echo_terminal:
                    self._terminal.append_stderr(
                        f"\nERROR: Operation timed out after {timeout:.0f}s\n"
                    )
                raise ProcessTimeout(f"{program} timed out") from None

            if self._cancel_requested:
                if echo_terminal:
                    self._terminal.append_stderr("\nOperation cancelled.\n")
                raise ProcessCancelled(f"{program} cancelled")

            self._flush_terminal(force=True)
            return exit_code, "".join(stdout_chunks), "".join(stderr_chunks)
        finally:
            self._disconnect_process(process)
            if self._active is process:
                self._active = None
            process.deleteLater()
            self._echo_terminal = True

    @staticmethod
    def _disconnect_process(process: QProcess) -> None:
        for signal in (
            process.readyReadStandardOutput,
            process.readyReadStandardError,
            process.finished,
        ):
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass
