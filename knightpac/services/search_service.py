"""Search service with cache and relevance ranking."""

from __future__ import annotations

from knightpac.models.package import Package
from knightpac.services.package_service import PackageService
from knightpac.services.search_cache import SearchCache
from knightpac.services.search_ranking import rank_results


class SearchService:
    def __init__(self, package_service: PackageService) -> None:
        self._packages = package_service
        self._cache = SearchCache()

    async def search(self, query: str, source_filter: str = "All") -> list[Package]:
        cached = self._cache.get(query, source_filter)
        if cached is not None:
            return cached

        raw = await self._packages.search(query, source_filter)
        ranked = rank_results(query, raw)
        self._cache.put(query, source_filter, ranked)
        return ranked

    def invalidate_cache(self) -> None:
        self._cache.clear()
