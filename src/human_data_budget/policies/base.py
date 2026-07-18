"""Policy protocol and exact allocation validation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from human_data_budget.models import Allocation, Candidate, PolicyState


class Policy(ABC):
    name: str

    @abstractmethod
    def allocate(self, state: PolicyState, seed: int) -> Allocation:
        """Return an allocation without exceeding ``remaining_human_tokens``."""


def select_with_budget(candidates: list[Candidate], budget: int) -> dict[str, int]:
    """Select one presentation per candidate while respecting an exact upper bound."""

    remaining = budget
    presentations: dict[str, int] = {}
    for candidate in candidates:
        if candidate.human_token_count <= remaining:
            presentations[candidate.example_id] = 1
            remaining -= candidate.human_token_count
    return presentations


def build_allocation(
    *,
    name: str,
    state: PolicyState,
    seed: int,
    presentations: dict[str, int],
    scores: dict[str, float] | None = None,
) -> Allocation:
    by_id = {candidate.example_id: candidate for candidate in state.candidates}
    selected_tokens = 0
    mode_allocations: dict[str, int] = {}
    for example_id, count in presentations.items():
        if example_id not in by_id:
            raise ValueError(f"unknown candidate: {example_id}")
        if count <= 0:
            raise ValueError("presentation counts must be positive")
        candidate = by_id[example_id]
        tokens = candidate.human_token_count * count
        selected_tokens += tokens
        mode_allocations[candidate.mode] = mode_allocations.get(candidate.mode, 0) + tokens
    if selected_tokens > state.remaining_human_tokens:
        raise ValueError("allocation exceeds remaining lifetime human-token budget")
    return Allocation(
        policy_name=name,
        generation=state.generation,
        policy_seed=seed,
        presentations=presentations,
        selected_human_tokens=selected_tokens,
        mode_allocations=mode_allocations,
        scores=scores or {},
    )


def validate_allocation(allocation: Allocation, state: PolicyState) -> None:
    """Recompute token counts independently of the policy's declaration."""

    rebuilt = build_allocation(
        name=allocation.policy_name,
        state=state,
        seed=allocation.policy_seed,
        presentations=allocation.presentations,
        scores=allocation.scores,
    )
    if rebuilt.selected_human_tokens != allocation.selected_human_tokens:
        raise ValueError("declared human-token count does not match selected presentations")
    if rebuilt.mode_allocations != allocation.mode_allocations:
        raise ValueError("declared per-mode allocation does not match selected presentations")
