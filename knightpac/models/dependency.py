"""Dependency tree models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyNode:
    name: str
    children: list[DependencyNode] = field(default_factory=list)

    def add_child(self, node: DependencyNode) -> None:
        self.children.append(node)
