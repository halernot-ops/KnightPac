"""History persistence models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryRecord:
    id: int
    timestamp: datetime
    manager: str
    action: str
    package: str
    result: str
    duration: float
