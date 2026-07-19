"""Fresh random rescue under an externally supplied budget."""

import random

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy, build_allocation, select_with_budget


class RandomPolicy(Policy):
    name = "random"

    def __init__(self, per_generation_budget: int) -> None:
        self.per_generation_budget = per_generation_budget

    def allocate(self, state: PolicyState, seed: int) -> Allocation:
        candidates = list(state.candidates)
        random.Random(seed).shuffle(candidates)
        budget = min(self.per_generation_budget, state.remaining_human_tokens)
        presentations = select_with_budget(candidates, budget)
        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations=presentations,
        )
