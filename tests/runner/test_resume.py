import json
from pathlib import Path

import pytest

from human_data_budget.runner.chain import run_toy_chain

ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    return json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))


def test_fresh_run_creates_manifest_checkpoints_and_result(tmp_path: Path) -> None:
    config = _load_config()
    output_dir = tmp_path / "run"
    manifest, result = run_toy_chain(config, output_dir=output_dir)

    assert manifest["status"] == "complete"
    assert (output_dir / "run_manifest.json").exists()
    assert (output_dir / "chain_result.json").exists()
    checkpoints = sorted((output_dir / "checkpoints").glob("generation_*.json"))
    assert len(checkpoints) == config["horizon"]
    assert result.generations_completed == config["horizon"]


def test_resume_from_partial_checkpoint_matches_uninterrupted_run(tmp_path: Path) -> None:
    config = _load_config()
    full_dir = tmp_path / "full"
    _, full_result = run_toy_chain(config, output_dir=full_dir)

    # Simulate a crash after generation 0: seed a fresh run directory with only
    # the first checkpoint that a real interrupted run would have produced.
    resume_dir = tmp_path / "resume"
    (resume_dir / "checkpoints").mkdir(parents=True)
    first_checkpoint = sorted((full_dir / "checkpoints").glob("generation_*.json"))[0]
    (resume_dir / "checkpoints" / first_checkpoint.name).write_text(
        first_checkpoint.read_text(encoding="utf-8"), encoding="utf-8"
    )

    resume_manifest, resume_result = run_toy_chain(config, output_dir=resume_dir, resume=True)

    assert resume_result.as_dict() == full_result.as_dict()
    assert resume_manifest["status"] == "complete"
    resumed_checkpoints = sorted((resume_dir / "checkpoints").glob("generation_*.json"))
    assert len(resumed_checkpoints) == config["horizon"]


def test_resume_without_existing_checkpoint_behaves_like_fresh_run(tmp_path: Path) -> None:
    config = _load_config()
    _, fresh_result = run_toy_chain(config, output_dir=tmp_path / "fresh")
    _, resume_result = run_toy_chain(
        config, output_dir=tmp_path / "resume_no_checkpoint", resume=True
    )
    assert resume_result.as_dict() == fresh_result.as_dict()


def test_same_config_and_seed_is_deterministic_with_output_dir(tmp_path: Path) -> None:
    config = _load_config()
    _, first_result = run_toy_chain(config, output_dir=tmp_path / "first")
    _, second_result = run_toy_chain(config, output_dir=tmp_path / "second")
    assert first_result.as_dict() == second_result.as_dict()


def test_mid_loop_failure_writes_structured_failure_and_marks_manifest_failed(
    tmp_path: Path,
) -> None:
    config = _load_config()
    config["tail_modes"] = ["nonexistent_mode"]
    output_dir = tmp_path / "failure_run"

    with pytest.raises(ValueError, match="missing tail mode score"):
        run_toy_chain(config, output_dir=output_dir)

    failure = json.loads((output_dir / "failure.json").read_text(encoding="utf-8"))
    assert failure["category"] == "implementation_defect"
    assert failure["generation"] == 0
    assert failure["run_id"] == config["run_id"]

    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["status_history"][-1] == {"status": "failed"}
    # chain_result.json is never written on failure -- no fabricated result.
    assert not (output_dir / "chain_result.json").exists()
