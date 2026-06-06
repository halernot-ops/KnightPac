"""In-memory cache for search results."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from knightpac.models.package import Package

_MAX_ENTRIES = 64


@dataclass(frozen=True)
class SearchKey:
    query: str
    source_filter: str


class SearchCache:
    def __init__(self, max_entries: int = _MAX_ENTRIES) -> None:
        self._max_entries = max_entries
        self._store: OrderedDict[SearchKey, list[Package]] = OrderedDict()

    def get(self, query: str, source_filter: str) -> list[Package] | None:
        key = SearchKey(query=query.lower().strip(), source_filter=source_filter)
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return list(self._store[key])

    def put(self, query: str, source_filter: str, results: list[Package]) -> None:
        key = SearchKey(query=query.lower().strip(), source_filter=source_filter)
        self._store[key] = list(results)
        self._store.move_to_end(key)
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
