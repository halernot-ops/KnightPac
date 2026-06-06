"""Operation history models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OperationType(str, Enum):
    INSTALL = "INSTALL"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"
    REINSTALL = "REINSTALL"
    SYNC = "SYNC"
    CACHE_CLEAR = "CACHE_CLEAR"


class OperationResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Operation:
    timestamp: datetime
    operation: OperationType
    package: str
    result: OperationResult
    details: str = ""
