"""Sequential operation queue for package actions."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QObject, Signal

from knightpac.core.process_runner import ProcessCancelled, ProcessRunner, ProcessTimeout
from knightpac.models.operation import OperationResult, OperationType
from knightpac.models.operation_progress import OperationProgress
from knightpac.models.package import Package

logger = logging.getLogger("knightpac.queue")


class QueueStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class QueuedOperation:
    id: str
    action: OperationType
    package: Package
    _handler: Callable[[], Awaitable[bool]] = field(repr=False)
    status: QueueStatus = QueueStatus.PENDING
    error: str = ""
    duration: float = 0.0
    progress: OperationProgress = field(default_factory=OperationProgress)

    @property
    def package_name(self) -> str:
        return self.package.name

    @property
    def manager_name(self) -> str:
        return self.package.manager or "unknown"


class OperationQueue(QObject):
    operation_enqueued = Signal(object)
    operation_started = Signal(object)
    operation_finished = Signal(object)
    progress_updated = Signal(object, object)
    queue_changed = Signal()

    def __init__(self, runner: ProcessRunner, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._runner = runner
        self._queue: asyncio.Queue[QueuedOperation | None] = asyncio.Queue()
        self._pending: list[QueuedOperation] = []
        self._current: QueuedOperation | None = None
        self._worker_task: asyncio.Task | None = None

    def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            try:
                self._worker_task = asyncio.get_running_loop().create_task(self._worker())
            except RuntimeError:
                self._worker_task = asyncio.get_event_loop().create_task(self._worker())

    def cancel_current(self) -> None:
        self._runner.request_cancel()

    async def _worker(self) -> None:
        while True:
            op = await self._queue.get()
            if op is None:
                break
            self._current = op
            op.status = QueueStatus.RUNNING
            op.progress = OperationProgress(total_steps=4)
            self.operation_started.emit(op)
            self.queue_changed.emit()

            manager = op.manager_name if op.manager_name != "unknown" else "pacman"
            self._runner.set_progress_callback(
                lambda p, operation=op: self._on_progress(operation, p),
                manager=manager,
            )

            started = time.monotonic()
            try:
                ok = await op._handler()
                op.duration = time.monotonic() - started
                op.status = QueueStatus.SUCCESS if ok else QueueStatus.FAILED
            except ProcessCancelled:
                op.status = QueueStatus.CANCELLED
                op.error = "Cancelled by user"
                op.duration = time.monotonic() - started
            except ProcessTimeout as exc:
                op.status = QueueStatus.FAILED
                op.error = str(exc)
                op.duration = time.monotonic() - started
            except asyncio.CancelledError:
                op.status = QueueStatus.CANCELLED
                raise
            except Exception as exc:
                logger.exception("Queued operation failed: %s", exc)
                op.status = QueueStatus.FAILED
                op.error = str(exc)
                op.duration = time.monotonic() - started
            finally:
                self._runner.set_progress_callback(None)
                if op in self._pending:
                    self._pending.remove(op)
                self._current = None
                self.operation_finished.emit(op)
                self.queue_changed.emit()
                self._queue.task_done()

    def _on_progress(self, op: QueuedOperation, progress: OperationProgress) -> None:
        op.progress = progress
        self.progress_updated.emit(op, progress)

    def enqueue(
        self,
        action: OperationType,
        package: Package,
        handler: Callable[[], Awaitable[bool]],
    ) -> QueuedOperation:
        op = QueuedOperation(
            id=uuid.uuid4().hex[:12],
            action=action,
            package=package,
            _handler=handler,
        )
        self._pending.append(op)
        self._queue.put_nowait(op)
        self.operation_enqueued.emit(op)
        self.queue_changed.emit()
        self.start()
        return op

    def pending_operations(self) -> list[QueuedOperation]:
        return list(self._pending)

    def current_operation(self) -> QueuedOperation | None:
        return self._current

    @staticmethod
    def result_for_status(status: QueueStatus) -> OperationResult:
        if status == QueueStatus.SUCCESS:
            return OperationResult.SUCCESS
        if status == QueueStatus.CANCELLED:
            return OperationResult.CANCELLED
        return OperationResult.FAILED
