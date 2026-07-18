"""Schedule-only rescue with random within-generation candidate selection."""

import random

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy, build_allocation, select_with_budget


class ScheduleOnlyPolicy(Policy):
    name = "schedule_only"

    def __init__(self, schedule: dict[int, int]) -> None:
        self.schedule = dict(schedule)

    def allocate(self, state: PolicyState, seed: int) -> Allocation:
        candidates = list(state.candidates)
        random.Random(seed).shuffle(candidates)
        budget = min(self.schedule.get(state.generation, 0), state.remaining_human_tokens)
        presentations = select_with_budget(candidates, budget)
        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations=presentations,
        )
