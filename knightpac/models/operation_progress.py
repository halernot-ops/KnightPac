"""Operation progress model for package manager output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OperationProgress:
    current_step: int = 0
    total_steps: int = 4
    percentage: float = 0.0
    step_label: str = field(default="")

    def update(self, step: int, label: str) -> None:
        self.current_step = step
        self.step_label = label
        if self.total_steps > 0:
            self.percentage = min(100.0, (step / self.total_steps) * 100.0)
