"""Regression tests documenting that the provisional joint policy is degenerate.

**Finding (2026-08-15):** under every configuration the fixture simulator permits,
``JointPolicy`` produces allocations identical to ``SelectionOnlyPolicy``, and
``RandomPolicy`` produces allocations identical to ``ScheduleOnlyPolicy``. The
time-allocation axis — the thing that makes the policy *joint* — is inert.

Mechanism, from ``policies/joint.py``::

    budget = min(
        state.remaining_human_tokens,
        max(self.base_per_generation_budget, reserve_safe_budget),
        adaptive_budget,
    )

``reserve_safe_budget`` is ``remaining_human_tokens // remaining_generations``. When
the lifetime budget divides evenly across the horizon — which ``simulate_policy``
*enforces*, raising otherwise — that quotient equals ``base_per_generation_budget``
at every generation. The ``max(...)`` term therefore collapses to
``base_per_generation_budget``, which caps the whole expression. ``adaptive_budget``
is always greater than or equal to it (``time_multiplier >= 1.0``), so it is never
the binding term and the urgency signal never changes what is spent.

**Why these tests assert the defect rather than a fix.** Choosing how the joint
policy should allocate across time is a scientific decision owned by Aarav and
gated by ``PREREGISTRATION.md``; silently changing the allocation rule here would
be freezing a method by side effect. These tests pin the current behaviour so the
degeneracy is visible in CI instead of hiding inside a passing suite.

**When the real joint policy lands, these tests are expected to FAIL.** That is the
signal to delete this file and replace it with tests of the frozen rule. Failure
here is not a regression; silence here would be.

See ``FAILURE_LOG.md`` entry F-001.
"""

from __future__ import annotations

import pytest

from human_data_budget.analysis.simulator import simulate_policy
from human_data_budget.models import Candidate, PolicyState
from human_data_budget.policies import (
    JointPolicy,
    RandomPolicy,
    ScheduleOnlyPolicy,
    SelectionOnlyPolicy,
)

HORIZON = 10
PER_GENERATION = 10


def candidates() -> tuple[Candidate, ...]:
    return (
        Candidate("common-example", PER_GENERATION, "common", 0.0),
        Candidate("tail-example", PER_GENERATION, "tail", 0.0),
    )


def state(generation: int, remaining: int, statistics: dict[str, float]) -> PolicyState:
    return PolicyState(
        generation=generation,
        remaining_human_tokens=remaining,
        mode_statistics=statistics,
        candidates=candidates(),
    )


@pytest.mark.parametrize("generation", range(HORIZON))
def test_joint_matches_selection_only_at_every_generation(generation: int) -> None:
    """The two policies allocate identically, generation by generation."""
    joint = JointPolicy(horizon=HORIZON, base_per_generation_budget=PER_GENERATION)
    selection = SelectionOnlyPolicy(PER_GENERATION)

    remaining = (HORIZON - generation) * PER_GENERATION
    statistics = {"common": 0.10 + 0.04 * generation, "tail": 0.20 + 0.10 * generation}
    current = state(generation, remaining, statistics)

    joint_allocation = joint.allocate(current, seed=generation)
    selection_allocation = selection.allocate(current, seed=generation)

    assert joint_allocation.selected_human_tokens == selection_allocation.selected_human_tokens
    assert joint_allocation.mode_allocations == selection_allocation.mode_allocations
    assert joint_allocation.presentations == selection_allocation.presentations


def test_joint_never_exceeds_the_uniform_per_generation_budget() -> None:
    """The adaptive term is never binding, even under extreme urgency."""
    joint = JointPolicy(horizon=HORIZON, base_per_generation_budget=PER_GENERATION)

    saturated = state(0, HORIZON * PER_GENERATION, {"common": 1.0, "tail": 1.0})
    allocation = joint.allocate(saturated, seed=0)

    assert allocation.selected_human_tokens == PER_GENERATION, (
        "urgency of 1.0 should double the adaptive budget, but the max(...) term "
        "caps spending at the uniform per-generation budget"
    )


def test_random_matches_schedule_only_over_a_full_chain() -> None:
    """The second degenerate pair: both spend uniformly and select identically."""
    random_policy = RandomPolicy(PER_GENERATION)
    schedule_policy = ScheduleOnlyPolicy(
        {generation: PER_GENERATION for generation in range(HORIZON)}
    )

    for generation in range(HORIZON):
        remaining = (HORIZON - generation) * PER_GENERATION
        current = state(generation, remaining, {"common": 0.1, "tail": 0.2})
        assert (
            random_policy.allocate(current, seed=generation).selected_human_tokens
            == schedule_policy.allocate(current, seed=generation).selected_human_tokens
        )


def test_simulated_chains_are_indistinguishable() -> None:
    """End to end: the two pairs yield identical metric trajectories.

    This is why `results/figures/nll_by_generation.png` shows two visible lines
    rather than four — the other two are exactly beneath them.
    """
    chains = {
        name: simulate_policy(name, chain_seed=1, horizon=HORIZON)
        for name in ("random", "schedule_only", "selection_only", "joint")
    }

    def trajectory(name: str) -> list[float]:
        return [metric["human_nll"] for metric in chains[name]["chain_result"]["metrics"]]

    assert trajectory("random") == trajectory("schedule_only")
    assert trajectory("selection_only") == trajectory("joint")
    assert trajectory("joint") != trajectory("schedule_only"), (
        "if this fails, all four policies have collapsed together and the fixture "
        "can no longer distinguish any treatment family at all"
    )


def test_budget_matching_still_holds_despite_degeneracy() -> None:
    """Degeneracy does not break the fairness constraint — it makes it trivial.

    Budget equality passing is therefore *not* evidence that the four treatment
    families are distinct. Recorded so no one reads a green budget test as
    validation of the method.
    """
    consumed = {
        name: simulate_policy(name, chain_seed=1, horizon=HORIZON)["chain_result"][
            "consumed_human_tokens"
        ]
        for name in ("random", "schedule_only", "selection_only", "joint")
    }
    assert len(set(consumed.values())) == 1
