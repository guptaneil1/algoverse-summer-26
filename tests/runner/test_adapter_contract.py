"""Conformance tests for the runner adapter contracts and the uniform mock policy."""

from __future__ import annotations

import dataclasses

import pytest

from human_data_budget.generation.toy import toy_generate_step
from human_data_budget.models import Candidate, PolicyState
from human_data_budget.policies.base import validate_allocation
from human_data_budget.runner.adapter import (
    ChainComponents,
    Evaluator,
    GenerateStep,
    TrainStep,
    toy_components,
)
from human_data_budget.runner.evaluator import NullEvaluator
from human_data_budget.runner.uniform_policy import UniformPolicy
from human_data_budget.training.toy import toy_train_step

# --------------------------------------------------------------------------
# Adapter contracts
# --------------------------------------------------------------------------


def test_toy_implementations_satisfy_the_protocols() -> None:
    """The contracts must describe what chain.py already calls, not an aspiration."""
    assert isinstance(toy_train_step, TrainStep)
    assert isinstance(toy_generate_step, GenerateStep)
    assert isinstance(NullEvaluator(), Evaluator)


def test_toy_components_bundle_is_marked_fixture() -> None:
    components = toy_components()
    assert components.is_fixture
    assert components.label == "toy"


def test_non_toy_label_is_not_fixture() -> None:
    """A pilot bundle must not report itself as fixture output."""
    components = ChainComponents(
        train_step=toy_train_step,
        generate_step=toy_generate_step,
        evaluator=NullEvaluator(),
        label="pilot",
    )
    assert not components.is_fixture


def test_components_are_immutable() -> None:
    """Swapping a component mid-chain would invalidate the manifest."""
    components = toy_components()
    with pytest.raises(dataclasses.FrozenInstanceError):
        components.label = "pilot"  # type: ignore[misc]


def test_train_step_is_deterministic_under_seed() -> None:
    state = {"generation": 2, "consumed_tokens": 40}
    assert toy_train_step(dict(state), 7) == toy_train_step(dict(state), 7)
    assert toy_train_step(dict(state), 7) != toy_train_step(dict(state), 8)


def test_generate_step_is_deterministic_under_seed() -> None:
    state = {"generation": 1, "examples_per_generation": 3}
    assert toy_generate_step(dict(state), 5) == toy_generate_step(dict(state), 5)


def test_generated_records_carry_provenance() -> None:
    """Synthetic output must be identifiable as synthetic in the next generation."""
    produced = toy_generate_step({"generation": 4, "examples_per_generation": 2}, 1)
    for example in produced["examples"]:
        assert example["origin"] == "synthetic"
        assert example["generation"] == 4
        assert example["example_id"].startswith("synthetic-g4-")


# --------------------------------------------------------------------------
# Uniform mock policy
# --------------------------------------------------------------------------

HORIZON = 5
LIFETIME = 50


def candidates() -> tuple[Candidate, ...]:
    return (
        Candidate("a-common", 10, "common", 0.9),
        Candidate("b-tail", 10, "tail", 0.1),
    )


def state(generation: int, remaining: int, statistics: dict[str, float]) -> PolicyState:
    return PolicyState(
        generation=generation,
        remaining_human_tokens=remaining,
        mode_statistics=statistics,
        candidates=candidates(),
    )


def test_uniform_policy_spends_an_even_share() -> None:
    policy = UniformPolicy(horizon=HORIZON, lifetime_human_budget=LIFETIME)
    allocation = policy.allocate(state(0, LIFETIME, {"common": 0.1, "tail": 0.5}), seed=0)
    assert allocation.selected_human_tokens == 10


def test_uniform_policy_ignores_mode_statistics() -> None:
    """Identical allocation under opposite mode signals: the control is neutral."""
    policy = UniformPolicy(horizon=HORIZON, lifetime_human_budget=LIFETIME)
    favouring_tail = policy.allocate(state(0, LIFETIME, {"common": 0.0, "tail": 1.0}), seed=0)
    favouring_common = policy.allocate(state(0, LIFETIME, {"common": 1.0, "tail": 0.0}), seed=0)
    assert favouring_tail.mode_allocations == favouring_common.mode_allocations
    assert favouring_tail.presentations == favouring_common.presentations


def test_uniform_policy_is_seed_independent() -> None:
    policy = UniformPolicy(horizon=HORIZON, lifetime_human_budget=LIFETIME)
    current = state(1, 40, {"common": 0.2, "tail": 0.3})
    assert policy.allocate(current, seed=1).presentations == policy.allocate(
        current, seed=999
    ).presentations


def test_uniform_policy_consumes_the_exact_lifetime_budget() -> None:
    """The invariant the runner actually needs: no drift over a full chain."""
    policy = UniformPolicy(horizon=HORIZON, lifetime_human_budget=LIFETIME)
    remaining = LIFETIME
    for generation in range(HORIZON):
        current = state(generation, remaining, {"common": 0.1, "tail": 0.2})
        allocation = policy.allocate(current, seed=generation)
        validate_allocation(allocation, current)
        remaining -= allocation.selected_human_tokens
    assert remaining == 0


def test_uniform_policy_never_exceeds_remaining_budget() -> None:
    policy = UniformPolicy(horizon=HORIZON, lifetime_human_budget=LIFETIME)
    current = state(4, 5, {"common": 0.1, "tail": 0.2})
    allocation = policy.allocate(current, seed=0)
    assert allocation.selected_human_tokens <= 5


def test_uniform_policy_redistributes_an_underspend() -> None:
    """A shortfall must be recovered later, not silently lost from the budget.

    Generation 0's even share is 30 // 2 = 15. Candidates cost 10 each, so only
    one fits and the generation underspends by 5. The final generation is handed
    the entire remainder (20) rather than another 15, and both candidates fit —
    so the chain still consumes exactly 30.
    """
    policy = UniformPolicy(horizon=2, lifetime_human_budget=30)

    first = state(0, 30, {"common": 0.1, "tail": 0.2})
    first_allocation = policy.allocate(first, seed=0)
    assert first_allocation.selected_human_tokens == 10  # underspends its 15 share

    second = state(1, 30 - first_allocation.selected_human_tokens, {"common": 0.1, "tail": 0.2})
    second_allocation = policy.allocate(second, seed=1)
    assert second_allocation.selected_human_tokens == 20  # recovers the shortfall

    total = first_allocation.selected_human_tokens + second_allocation.selected_human_tokens
    assert total == 30


def test_uniform_policy_is_named_as_a_fixture() -> None:
    """Its name must make an accidental appearance in a comparison obvious."""
    assert UniformPolicy(horizon=1, lifetime_human_budget=0).name == "uniform_fixture"


@pytest.mark.parametrize(("horizon", "budget"), [(0, 10), (-1, 10), (5, -1)])
def test_uniform_policy_rejects_invalid_construction(horizon: int, budget: int) -> None:
    with pytest.raises(ValueError):
        UniformPolicy(horizon=horizon, lifetime_human_budget=budget)
