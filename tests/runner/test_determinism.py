import hashlib
import json
from pathlib import Path

from human_data_budget.generation.toy import toy_generate_step
from human_data_budget.runner.chain import run_toy_chain
from human_data_budget.training.toy import toy_train_step

ROOT = Path(__file__).resolve().parents[2]


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


def test_whole_smoke_chain_reproduces_byte_identical_artifacts(tmp_path: Path) -> None:
    """The frozen smoke condition, end to end, not just its individual steps.

    Every test above exercises one step function in isolation. Deterministic steps
    do not by themselves make a deterministic chain: seed propagation, iteration
    order, and serialisation all sit between them. This runs the whole chain twice
    from the frozen config and compares the persisted artifacts byte for byte.
    """

    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    run_toy_chain(config, output_dir=first_dir)
    run_toy_chain(config, output_dir=second_dir)

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    for name in ("chain_result.json", "run_manifest.json"):
        assert sha256(first_dir / name) == sha256(second_dir / name), name

    first_checkpoints = sorted((first_dir / "checkpoints").glob("*.json"))
    second_checkpoints = sorted((second_dir / "checkpoints").glob("*.json"))
    assert [p.name for p in first_checkpoints] == [p.name for p in second_checkpoints]
    for left, right in zip(first_checkpoints, second_checkpoints, strict=True):
        assert sha256(left) == sha256(right), left.name


def test_different_chain_seed_changes_the_smoke_chain_outputs(tmp_path: Path) -> None:
    """Determinism must come from the seed, not from the chain ignoring it."""

    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))

    _, baseline = run_toy_chain(config, output_dir=tmp_path / "seed_default")
    _, reseeded = run_toy_chain({**config, "chain_seed": 999}, output_dir=tmp_path / "seed_999")

    assert baseline.as_dict() != reseeded.as_dict()
