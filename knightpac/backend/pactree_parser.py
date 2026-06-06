"""Parse pactree output into DependencyNode trees."""

from __future__ import annotations

import re

from knightpac.models.dependency import DependencyNode

_BRANCH_RE = re.compile(r"^([│├└─\s]*)([^\s│├└─]+)\s*$")


def parse_pactree(output: str, root_name: str) -> DependencyNode:
    root = DependencyNode(name=root_name)
    if not output.strip():
        return root

    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return root

    stack: list[tuple[int, DependencyNode]] = [(0, root)]

    for line in lines:
        name = _extract_name(line)
        if not name or name == root_name:
            continue
        depth = _tree_depth(line)
        node = DependencyNode(name=name)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1] if stack else root
        parent.add_child(node)
        stack.append((depth, node))

    return root


def _extract_name(line: str) -> str:
    if "─" in line or "├" in line or "└" in line or "│" in line:
        match = _BRANCH_RE.match(line)
        if match:
            return match.group(2).strip()
        parts = re.split(r"[├└│─]+", line)
        candidate = parts[-1].strip() if parts else line.strip()
        return candidate.split()[0] if candidate else ""
    return line.strip().split()[0]


def _tree_depth(line: str) -> int:
    prefix = line.split("─")[0] if "─" in line else line
    depth = 0
    i = 0
    while i < len(prefix):
        ch = prefix[i]
        if ch in "│":
            depth += 1
            i += 1
        elif ch in "├└":
            depth += 1
            i += 1
            while i < len(prefix) and prefix[i] in "─ ":
                i += 1
            break
        elif ch == " ":
            i += 1
        else:
            break
    return max(depth, 1)
