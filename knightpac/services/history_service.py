"""Operation history via SQLite repository."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from knightpac.data.history_repository import HistoryRepository
from knightpac.models.history import HistoryRecord
from knightpac.models.operation import OperationResult, OperationType

logger = logging.getLogger("knightpac.history")

EXPORT_DIR = Path(__file__).resolve().parent.parent / "logs" / "exports"


class HistoryService:
    def __init__(self, repository: HistoryRepository | None = None) -> None:
        self._repo = repository or HistoryRepository()

    def record(
        self,
        *,
        manager: str,
        action: OperationType,
        package: str,
        result: OperationResult,
        duration: float = 0.0,
    ) -> int:
        return self._repo.insert(
            timestamp=datetime.now(),
            manager=manager,
            action=action.value,
            package=package,
            result=result.value,
            duration=duration,
        )

    def list_filtered(
        self,
        *,
        filter_key: str = "all",
        search: str = "",
    ) -> list[HistoryRecord]:
        action_filter = None
        failed_only = False
        key = filter_key.lower()
        if key == "install":
            action_filter = "INSTALL"
        elif key == "remove":
            action_filter = "REMOVE"
        elif key == "update":
            action_filter = "UPDATE"
        elif key == "failed":
            failed_only = True
        return self._repo.query(
            action_filter=action_filter,
            failed_only=failed_only,
            search=search.strip() or None,
        )

    def list_all(self) -> list[HistoryRecord]:
        return self._repo.list_all()

    def export_csv(self, records: list[HistoryRecord]) -> Path:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = EXPORT_DIR / f"history_{datetime.now():%Y%m%d_%H%M%S}.csv"
        return self._repo.export_csv(records, path)

    def export_json(self, records: list[HistoryRecord]) -> Path:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = EXPORT_DIR / f"history_{datetime.now():%Y%m%d_%H%M%S}.json"
        return self._repo.export_json(records, path)
