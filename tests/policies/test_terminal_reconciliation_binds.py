"""Terminal reconciliation must actually bind, for every arm.

FAILURE_LOG.md F-020. `terminal.py` exists so every spending arm converges on the
same lifetime total. For `RandomPolicy`, `SelectionOnlyPolicy` and
`ScheduleOnlyPolicy` that works by handing over a flat allowance they spend greedily.
`JointPolicy` is different: its spend is gated by an internal urgency rule, and
reconciliation raised its *cap* without making its *floor* bind. It therefore
declined to spend, stranding 75,807 tokens at every seed of the first real pilot --
a 10.1% spread that invalidated the primary contrast.

The dry run could not catch this. `JointPolicy`'s allocation depends on
`mode_statistics`, which the dry run simulates, so the simulated chain reached a
different urgency and spent 749,844 where the real chain spent 674,193. Budget
matching for score-dependent policies is not testable by simulation, only by
asserting the policy's own contract.

That contract: **at the reconciliation generation, with budget remaining, a spending
arm allocates essentially all of it** -- short only by an indivisible candidate.
"""

from __future__ import annotations

import pytest

from human_data_budget.models import Candidate, PolicyState
from human_data_budget.policies.joint import JointPolicy
from human_data_budget.policies.random import RandomPolicy
from human_data_budget.policies.schedule_only import ScheduleOnlyPolicy
from human_data_budget.policies.selection_only import SelectionOnlyPolicy
from human_data_budget.policies.terminal import (
    allocate_with_reconciliation,
    last_spending_generation,
)

HORIZON = 10
BASE = 75_000
# Small relative to the remainder, so indivisibility cannot explain a shortfall.
CANDIDATE_TOKENS = 4_000


def candidates(count: int = 400) -> list[Candidate]:
    return [
        Candidate(
            example_id=f"train-{index:05d}",
            human_token_count=CANDIDATE_TOKENS,
            mode="tail" if index % 2 else "common",
        )
        for index in range(count)
    ]


def state(remaining: int, generation: int, *, urgency: float) -> PolicyState:
    return PolicyState(
        generation=generation,
        remaining_human_tokens=remaining,
        candidates=tuple(candidates()),
        # Low urgency is the case that exposed F-020: joint *wants* to spend nothing,
        # so only a binding floor makes it spend.
        mode_statistics={"tail": urgency, "common": urgency},
    )


def policies():
    schedule = {generation: 0 for generation in range(HORIZON)}
    return [
        ("random", RandomPolicy(BASE)),
        ("selection_only", SelectionOnlyPolicy(BASE)),
        ("schedule_only", ScheduleOnlyPolicy(schedule)),
        ("joint", JointPolicy(HORIZON, BASE)),
    ]


@pytest.mark.parametrize("name,policy", policies(), ids=lambda value: getattr(value, "name", value))
@pytest.mark.parametrize("urgency", [0.0, 0.1, 0.3, 0.9])
def test_reconciliation_spends_the_remainder(name, policy, urgency) -> None:
    """Every spending arm must converge on its ceiling, whatever its internal rule."""
    remaining = 75_807  # the exact amount F-020 stranded
    generation = last_spending_generation(HORIZON)

    allocation, reconciled = allocate_with_reconciliation(
        policy,
        state(remaining, generation, urgency=urgency),
        seed=101,
        config={"horizon": HORIZON},
    )

    assert reconciled, f"{name} was not reconciled at generation {generation}"
    shortfall = remaining - allocation.selected_human_tokens
    assert shortfall < CANDIDATE_TOKENS, (
        f"{name} at urgency {urgency} left {shortfall:,} of {remaining:,} unspent; "
        f"one candidate is {CANDIDATE_TOKENS:,}, so indivisibility does not explain "
        "it. This is F-020"
    )


def test_joint_at_zero_urgency_is_the_f020_regression() -> None:
    """The exact case that stranded budget in the pilot, called out on its own.

    At low urgency joint's `_desired_budget` returns 0. Before F-020 the feasibility
    floor was ~0 as well, so the allocation was 0 and the remainder was lost.
    """
    remaining = 75_807
    allocation, reconciled = allocate_with_reconciliation(
        JointPolicy(HORIZON, BASE),
        state(remaining, last_spending_generation(HORIZON), urgency=0.0),
        seed=101,
        config={"horizon": HORIZON},
    )
    assert reconciled
    assert allocation.selected_human_tokens > 0, (
        "joint allocated nothing at the reconciliation generation despite a remaining "
        "budget; the reconciliation raised its cap but not its floor"
    )
    assert remaining - allocation.selected_human_tokens < CANDIDATE_TOKENS


def test_no_rescue_is_still_exempt() -> None:
    """Topping up the control would convert it into a rescue arm."""
    from human_data_budget.policies.no_rescue import NoRescuePolicy

    allocation, reconciled = allocate_with_reconciliation(
        NoRescuePolicy(),
        state(75_807, last_spending_generation(HORIZON), urgency=0.9),
        seed=101,
        config={"horizon": HORIZON},
    )
    assert not reconciled
    assert allocation.selected_human_tokens == 0


def test_earlier_generations_are_untouched() -> None:
    """Reconciliation must change timing only at the last spending generation."""
    allocation, reconciled = allocate_with_reconciliation(
        JointPolicy(HORIZON, BASE),
        state(750_000, 0, urgency=0.0),
        seed=101,
        config={"horizon": HORIZON},
    )
    assert not reconciled
    assert allocation.selected_human_tokens == 0, (
        "joint spent at generation 0 despite zero urgency; its timing rule was "
        "overridden outside the reconciliation generation"
    )
