"""Mode-targeted selection under a fixed per-generation schedule."""

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy, build_allocation, select_with_budget


class SelectionOnlyPolicy(Policy):
    name = "selection_only"

    def __init__(self, per_generation_budget: int) -> None:
        self.per_generation_budget = per_generation_budget

    def allocate(self, state: PolicyState, seed: int) -> Allocation:
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
        budget = min(self.per_generation_budget, state.remaining_human_tokens)
        presentations = select_with_budget(ordered, budget)
        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations=presentations,
            scores=scores,
        )
