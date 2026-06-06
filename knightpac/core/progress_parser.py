"""Parse pacman/paru stdout for install progress steps."""

from __future__ import annotations

from knightpac.models.operation_progress import OperationProgress

_PACMAN_STEPS: tuple[tuple[str, str], ...] = (
    ("downloading", "Downloading packages"),
    ("retrieving", "Downloading packages"),
    ("checking keyring", "Downloading packages"),
    ("resolving dependencies", "Checking dependencies"),
    ("checking dependencies", "Checking dependencies"),
    ("installing", "Installing packages"),
    ("upgrading", "Installing packages"),
    ("reinstalling", "Installing packages"),
    ("post-transaction hooks", "Running post-install hooks"),
    ("running post-transaction", "Running post-install hooks"),
)

_PARU_EXTRA: tuple[tuple[str, str], ...] = (
    ("building", "Building AUR package"),
    ("fetching", "Fetching sources"),
)


def parse_output_line(line: str, progress: OperationProgress, *, manager: str = "pacman") -> None:
    lower = line.lower()
    steps = list(_PACMAN_STEPS)
    if manager == "paru":
        steps = list(_PARU_EXTRA) + steps
    total = progress.total_steps or len(_PACMAN_STEPS)
    for index, (pattern, label) in enumerate(steps, start=1):
        if pattern in lower:
            progress.total_steps = max(progress.total_steps, total)
            progress.update(min(index, progress.total_steps), label)
            return
