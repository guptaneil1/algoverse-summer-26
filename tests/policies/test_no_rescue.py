"""The no-rescue control arm must spend nothing, unconditionally.

Every budget-matched comparison is read against this arm. If it ever spends, the
contrast between "no human data" and "some human data" stops being what it claims.
"""

from __future__ import annotations

import pytest

from human_data_budget.models import Candidate, PolicyState
from human_data_budget.policies import NoRescuePolicy
from human_data_budget.runner.chain import policy_from_config

CANDIDATES = (
    Candidate(example_id="h-1", human_token_count=900, mode="tail",
              undercoverage_score=0.9),
    Candidate(example_id="h-2", human_token_count=1100, mode="common",
              undercoverage_score=0.1),
)


def _state(remaining: int = 1_000_000, generation: int = 0) -> PolicyState:
    return PolicyState(
        generation=generation,
        remaining_human_tokens=remaining,
        mode_statistics={"tail": 0.5, "common": 0.1},
        candidates=CANDIDATES,
        history=(),
    )


@pytest.mark.parametrize("remaining", [0, 1_000, 1_000_000])
@pytest.mark.parametrize("generation", [0, 5, 9])
def test_spends_nothing_whatever_the_budget_or_generation(
    remaining: int, generation: int
) -> None:
    allocation = NoRescuePolicy().allocate(_state(remaining, generation), seed=42)
    assert allocation.selected_human_tokens == 0
    assert allocation.presentations == {}


def test_spends_nothing_even_when_a_mode_is_badly_undercovered() -> None:
    """A policy that reacted to urgency here would not be a control arm."""
    state = PolicyState(
        generation=3, remaining_human_tokens=1_000_000,
        mode_statistics={"tail": 0.99, "common": 0.99},
        candidates=CANDIDATES, history=(),
    )
    assert NoRescuePolicy().allocate(state, seed=1).selected_human_tokens == 0


def test_is_reachable_from_config() -> None:
    """primary_no_rescue.json names this policy; it must resolve."""
    assert policy_from_config(
        {"policy": "no_rescue", "per_generation_human_budget": 75_000, "horizon": 10}
    ).name == "no_rescue"


def test_is_deterministic_across_seeds() -> None:
    first = NoRescuePolicy().allocate(_state(), seed=1)
    second = NoRescuePolicy().allocate(_state(), seed=999)
    assert first.presentations == second.presentations == {}
