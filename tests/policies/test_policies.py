import pytest

from human_data_budget.models import Candidate, PolicyState
from human_data_budget.policies import (
    JointPolicy,
    RandomPolicy,
    ScheduleOnlyPolicy,
    SelectionOnlyPolicy,
)
from human_data_budget.policies.base import validate_allocation


@pytest.fixture
def state() -> PolicyState:
    return PolicyState(
        generation=0,
        remaining_human_tokens=20,
        mode_statistics={"common": 0.1, "tail": 0.8},
        candidates=(
            Candidate("common", 10, "common"),
            Candidate("tail", 10, "tail"),
            Candidate("too-large", 30, "tail"),
        ),
    )


@pytest.mark.parametrize(
    "policy",
    [
        RandomPolicy(20),
        ScheduleOnlyPolicy({0: 20}),
        SelectionOnlyPolicy(20),
        JointPolicy(horizon=3, base_per_generation_budget=10),
    ],
)
def test_policy_respects_budget(policy, state: PolicyState) -> None:
    allocation = policy.allocate(state, seed=7)
    validate_allocation(allocation, state)
    assert allocation.selected_human_tokens <= state.remaining_human_tokens


def test_selection_prioritizes_tail(state: PolicyState) -> None:
    allocation = SelectionOnlyPolicy(10).allocate(state, seed=1)
    assert allocation.presentations == {"tail": 1}


def test_random_policy_is_seed_deterministic(state: PolicyState) -> None:
    policy = RandomPolicy(20)
    assert policy.allocate(state, 9) == policy.allocate(state, 9)
