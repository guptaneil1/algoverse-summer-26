"""Structured failure state for recursive-chain runs.

Categories mirror the four classes in ``docs/RUNBOOK.md``: an unfavorable
scientific result is not an implementation defect by default.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

FAILURE_CATEGORIES = (
    "infrastructure_failure",
    "implementation_defect",
    "data_protocol_violation",
    "scientific_divergence",
)


@dataclass(frozen=True)
class FailureState:
    run_id: str
    category: str
    message: str
    generation: int | None
    evidence: dict[str, Any] = field(default_factory=dict)
    rerun_allowed: bool = False

    def __post_init__(self) -> None:
        if self.category not in FAILURE_CATEGORIES:
            raise ValueError(f"unknown failure category: {self.category}")
        if self.generation is not None and self.generation < 0:
            raise ValueError("generation must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_failure(failure: FailureState, path: Path) -> None:
    """Atomically write structured failure state as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(failure.as_dict(), indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)
