"""No rescue: the reference condition, spending nothing after the starting corpus.

`configs/experiment/primary_no_rescue.json` names this policy and describes it as
"the chain receives no human rescue after the frozen starting condition,
establishing reference behaviour". Nothing implemented it, so the config could not
have launched even once frozen.

This is the control arm every budget-matched comparison is read against: it shows
what recursive training does to the model when no human tokens are spent at all.
Its lifetime human spend is exactly zero by construction, not by an empty candidate
set or an exhausted budget, so a comparison against it cannot be confounded by a
policy that merely failed to find anything affordable.
"""

from human_data_budget.models import Allocation, PolicyState
from human_data_budget.policies.base import Policy, build_allocation


class NoRescuePolicy(Policy):
    name = "no_rescue"

    def allocate(self, state: PolicyState, seed: int) -> Allocation:
        """Return an empty allocation, whatever the state and budget say.

        Deliberately ignores ``state.remaining_human_tokens`` and
        ``state.candidates``. A no-rescue arm that consulted the budget would be a
        zero-budget random policy, and would start spending the moment someone
        changed a budget field.
        """
        return build_allocation(
            name=self.name,
            state=state,
            seed=seed,
            presentations={},
        )
