import json
from pathlib import Path

import pytest

from human_data_budget.runner import chain as chain_module
from human_data_budget.runner.chain import run_toy_chain

ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))
    config["horizon"] = 2
    return config


def _seed_resume_dir_with_generation_zero_checkpoint(full_dir: Path, resume_dir: Path) -> None:
    """Simulate a crash right after generation 0's checkpoint was written."""

    (resume_dir / "checkpoints").mkdir(parents=True)
    checkpoint0 = full_dir / "checkpoints" / "generation_0000.json"
    (resume_dir / "checkpoints" / checkpoint0.name).write_text(
        checkpoint0.read_text(encoding="utf-8"), encoding="utf-8"
    )


def test_resumed_run_matches_uninterrupted_run_exactly(tmp_path: Path) -> None:
    config = _load_config()

    full_dir = tmp_path / "full"
    full_manifest, full_result = run_toy_chain(config, output_dir=full_dir)

    resume_dir = tmp_path / "resume"
    _seed_resume_dir_with_generation_zero_checkpoint(full_dir, resume_dir)

    resume_manifest, resume_result = run_toy_chain(config, output_dir=resume_dir, resume=True)

    assert resume_result.as_dict() == full_result.as_dict()
    assert resume_manifest["status"] == full_manifest["status"] == "complete"
    assert resume_manifest["current_generation"] == full_manifest["current_generation"] == 1

    resumed_checkpoint1 = json.loads(
        (resume_dir / "checkpoints" / "generation_0001.json").read_text(encoding="utf-8")
    )
    full_checkpoint1 = json.loads(
        (full_dir / "checkpoints" / "generation_0001.json").read_text(encoding="utf-8")
    )
    assert resumed_checkpoint1 == full_checkpoint1


def test_resume_loads_generation_zero_verbatim_without_recomputing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _load_config()

    full_dir = tmp_path / "full"
    run_toy_chain(config, output_dir=full_dir)
    gen0_checkpoint_path = full_dir / "checkpoints" / "generation_0000.json"
    gen0_checkpoint_before = gen0_checkpoint_path.read_text(encoding="utf-8")

    resume_dir = tmp_path / "resume"
    _seed_resume_dir_with_generation_zero_checkpoint(full_dir, resume_dir)

    trained_generations: list[int] = []
    real_toy_train_step = chain_module.toy_train_step

    def spy_toy_train_step(state: dict, seed: int):
        trained_generations.append(state["generation"])
        return real_toy_train_step(state, seed)

    monkeypatch.setattr(chain_module, "toy_train_step", spy_toy_train_step)

    run_toy_chain(config, output_dir=resume_dir, resume=True)

    # Only generation 1 was (re)trained; generation 0 was never recomputed.
    assert trained_generations == [1]

    # The seeded generation-0 checkpoint file itself was never touched.
    assert (
        resume_dir / "checkpoints" / "generation_0000.json"
    ).read_text(encoding="utf-8") == gen0_checkpoint_before


def test_resume_false_ignores_existing_checkpoint_and_recomputes_generation_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _load_config()

    full_dir = tmp_path / "full"
    run_toy_chain(config, output_dir=full_dir)

    restart_dir = tmp_path / "restart_no_resume"
    _seed_resume_dir_with_generation_zero_checkpoint(full_dir, restart_dir)

    trained_generations: list[int] = []
    real_toy_train_step = chain_module.toy_train_step

    def spy_toy_train_step(state: dict, seed: int):
        trained_generations.append(state["generation"])
        return real_toy_train_step(state, seed)

    monkeypatch.setattr(chain_module, "toy_train_step", spy_toy_train_step)

    run_toy_chain(config, output_dir=restart_dir, resume=False)

    # Without resume=True, generation 0 is recomputed from scratch even
    # though a checkpoint for it already exists on disk.
    assert trained_generations == [0, 1]


def test_resume_with_no_existing_checkpoint_computes_both_generations(
    tmp_path: Path,
) -> None:
    config = _load_config()
    fresh_dir = tmp_path / "fresh"
    resume_dir = tmp_path / "resume_no_checkpoint"

    _, fresh_result = run_toy_chain(config, output_dir=fresh_dir)
    _, resume_result = run_toy_chain(config, output_dir=resume_dir, resume=True)

    assert resume_result.as_dict() == fresh_result.as_dict()
