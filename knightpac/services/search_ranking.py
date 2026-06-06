"""Relevance ranking for search results."""

from __future__ import annotations

from knightpac.models.package import Package


def rank_results(query: str, packages: list[Package]) -> list[Package]:
    q = query.lower().strip()
    if not q:
        return packages

    def score(pkg: Package) -> tuple[int, str]:
        name = pkg.name.lower()
        desc = (pkg.description or "").lower()
        if name == q:
            return (0, name)
        if name.startswith(q):
            return (1, name)
        if q in name:
            return (2, name)
        if q in desc:
            return (3, name)
        return (4, name)

    return sorted(packages, key=score)
