"""SQLite persistence for operation history."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from knightpac.models.history import HistoryRecord

DB_PATH = Path(__file__).resolve().parent / "history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    manager TEXT NOT NULL,
    action TEXT NOT NULL,
    package TEXT NOT NULL,
    result TEXT NOT NULL,
    duration REAL NOT NULL DEFAULT 0
);
"""


class HistoryRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or DB_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_SCHEMA)
            conn.commit()

    def insert(
        self,
        *,
        timestamp: datetime,
        manager: str,
        action: str,
        package: str,
        result: str,
        duration: float,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO operations (timestamp, manager, action, package, result, duration)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp.isoformat(), manager, action, package, result, duration),
            )
            conn.commit()
            return int(cur.lastrowid)

    def query(
        self,
        *,
        action_filter: str | None = None,
        failed_only: bool = False,
        search: str | None = None,
        limit: int = 500,
    ) -> list[HistoryRecord]:
        clauses: list[str] = []
        params: list[object] = []

        if failed_only:
            clauses.append("result = ?")
            params.append("FAILED")
        elif action_filter == "UPDATE":
            clauses.append("(UPPER(action) = 'UPDATE' OR UPPER(action) = 'REINSTALL')")
        elif action_filter:
            clauses.append("UPPER(action) = ?")
            params.append(action_filter.upper())

        if search:
            clauses.append("(package LIKE ? OR action LIKE ? OR manager LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT id, timestamp, manager, action, package, result, duration
            FROM operations
            {where}
            ORDER BY id DESC
            LIMIT ?
        """
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            HistoryRecord(
                id=row["id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                manager=row["manager"],
                action=row["action"],
                package=row["package"],
                result=row["result"],
                duration=row["duration"],
            )
            for row in rows
        ]

    def list_all(self, limit: int = 500) -> list[HistoryRecord]:
        return self.query(limit=limit)

    def export_csv(self, records: list[HistoryRecord], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["id", "timestamp", "manager", "action", "package", "result", "duration"]
            )
            for row in records:
                writer.writerow(
                    [
                        row.id,
                        row.timestamp.isoformat(),
                        row.manager,
                        row.action,
                        row.package,
                        row.result,
                        row.duration,
                    ]
                )
        return path

    def export_json(self, records: list[HistoryRecord], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "manager": r.manager,
                "action": r.action,
                "package": r.package,
                "result": r.result,
                "duration": r.duration,
            }
            for r in records
        ]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path
