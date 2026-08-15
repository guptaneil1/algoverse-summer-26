"""Provisional joint time-and-mode toy policy.

This implementation exists to exercise the interface. It is not the frozen
scientific contribution and must be replaced or explicitly preregistered by
the method owner before primary treatment outcomes.
"""

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy, build_allocation, select_with_budget


class JointPolicy(Policy):
    name = "joint"

    def __init__(self, horizon: int, base_per_generation_budget: int) -> None:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        self.horizon = horizon
        self.base_per_generation_budget = base_per_generation_budget

    def allocate(self, state: PolicyState, seed: int) -> Allocation:
        remaining_generations = max(1, self.horizon - state.generation)
        urgency = max(state.mode_statistics.values(), default=0.0)
        time_multiplier = 1.0 + max(0.0, urgency)
        adaptive_budget = round(self.base_per_generation_budget * time_multiplier)
        reserve_safe_budget = state.remaining_human_tokens // remaining_generations
        budget = min(
            state.remaining_human_tokens,
            max(self.base_per_generation_budget, reserve_safe_budget),
            adaptive_budget,
        )
        scores = {
            candidate.example_id: state.mode_statistics.get(
                candidate.mode, candidate.undercoverage_score
            )
            for candidate in state.candidates
        }
        ordered = sorted(
            state.candidates,
            key=lambda candidate: (-scores[candidate.example_id], candidate.example_id),
        )
        presentations = select_with_budget(ordered, budget)
        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations=presentations,
            scores=scores,
        )
