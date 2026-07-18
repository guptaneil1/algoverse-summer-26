"""Shared immutable data structures crossing team-owned component boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candidate:
    """A policy-visible human rescue candidate.

    ``human_token_count`` means non-padding tokens consumed per optimizer
    presentation under the frozen tokenizer/preprocessing definition.
    """

    example_id: str
    human_token_count: int
    mode: str
    undercoverage_score: float = 0.0

    def __post_init__(self) -> None:
        if self.human_token_count <= 0:
            raise ValueError("human_token_count must be positive")


@dataclass(frozen=True)
class PolicyState:
    generation: int
    remaining_human_tokens: int
    mode_statistics: dict[str, float]
    candidates: tuple[Candidate, ...]
    history: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.generation < 0:
            raise ValueError("generation must be non-negative")
        if self.remaining_human_tokens < 0:
            raise ValueError("remaining_human_tokens must be non-negative")


@dataclass(frozen=True)
class Allocation:
    policy_name: str
    generation: int
    policy_seed: int
    presentations: dict[str, int]
    selected_human_tokens: int
    mode_allocations: dict[str, int]
    scores: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationMetric:
    generation: int
    human_nll: float
    tail_retention: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChainResult:
    run_id: str
    policy: str
    chain_seed: int
    budget_id: str
    generations_completed: int
    valid: bool
    metrics: tuple[GenerationMetric, ...]
    consumed_human_tokens: int
    consumed_total_tokens: int
    exclusion_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["schema_version"] = "1.0"
        result["metrics"] = [metric.as_dict() for metric in self.metrics]
        return result
