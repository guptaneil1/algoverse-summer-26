import json

from human_data_budget.generation.toy import toy_generate_step
from human_data_budget.training.toy import toy_train_step


def _dumps(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True)


def test_toy_train_step_is_byte_identical_for_same_state_and_seed() -> None:
    state = {"generation": 2, "consumed_tokens": 40}
    first = toy_train_step(state, seed=7)
    second = toy_train_step(state, seed=7)
    assert _dumps(first) == _dumps(second)


def test_toy_generate_step_is_byte_identical_for_same_state_and_seed() -> None:
    state = {"generation": 1, "examples_per_generation": 3}
    first = toy_generate_step(state, seed=42)
    second = toy_generate_step(state, seed=42)
    assert _dumps(first) == _dumps(second)


def test_toy_steps_differ_across_seeds() -> None:
    state = {"generation": 0, "examples_per_generation": 2}
    first = toy_generate_step(state, seed=1)
    second = toy_generate_step(state, seed=2)
    assert _dumps(first) != _dumps(second)


def test_full_config_seed_reproduces_across_repeated_runs() -> None:
    state = {"generation": 0, "consumed_tokens": 0, "examples_per_generation": 2}
    seed = 12345
    baseline_train = _dumps(toy_train_step(state, seed=seed))
    baseline_generate = _dumps(toy_generate_step(state, seed=seed))
    for _ in range(3):
        assert _dumps(toy_train_step(state, seed=seed)) == baseline_train
        assert _dumps(toy_generate_step(state, seed=seed)) == baseline_generate
