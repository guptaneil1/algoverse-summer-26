import json
from pathlib import Path

from human_data_budget.runner.chain import run_directory, run_toy_chain
from human_data_budget.runner.checkpoint import checkpoint_path, load_checkpoint

ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))
    config["horizon"] = 2
    return config


def test_run_directory_is_unique_per_run_id_and_deterministic() -> None:
    config = _load_config()
    base = Path("runs")
    assert run_directory(config, base) == base / config["run_id"]
    # deterministic: calling it again for the same config gives the same path
    assert run_directory(config, base) == run_directory(config, base)

    other_config = dict(config, run_id="a-different-run")
    assert run_directory(other_config, base) != run_directory(config, base)


def test_two_generation_run_writes_manifest_two_checkpoints_and_final_result(
    tmp_path: Path,
) -> None:
    config = _load_config()
    output_dir = tmp_path / "run"

    manifest, result = run_toy_chain(config, output_dir=output_dir)

    assert (output_dir / "run_manifest.json").exists()
    assert manifest["status"] == "complete"
    assert manifest["current_generation"] == 1
    assert manifest["failure"] is None

    checkpoint0 = load_checkpoint(checkpoint_path(output_dir, 0))
    checkpoint1 = load_checkpoint(checkpoint_path(output_dir, 1))
    assert checkpoint0 is not None
    assert checkpoint1 is not None
    assert checkpoint0["generation"] == 0
    assert checkpoint1["generation"] == 1

    assert (output_dir / "chain_result.json").exists()
    final_result = json.loads((output_dir / "chain_result.json").read_text(encoding="utf-8"))
    assert final_result == result.as_dict()
    assert result.generations_completed == 2
    assert len(result.metrics) == 2


def test_generation_one_builds_on_generation_zero_saved_state(tmp_path: Path) -> None:
    config = _load_config()
    output_dir = tmp_path / "run"
    run_toy_chain(config, output_dir=output_dir)

    checkpoint0 = load_checkpoint(checkpoint_path(output_dir, 0))
    checkpoint1 = load_checkpoint(checkpoint_path(output_dir, 1))

    # Generation 1 continues from generation 0's remaining budget, consumed
    # tokens, and allocation history -- it does not start from a fresh chain
    # state.
    assert checkpoint1["remaining_human_tokens"] <= checkpoint0["remaining_human_tokens"]
    assert checkpoint1["consumed_human_tokens"] >= checkpoint0["consumed_human_tokens"]
    assert len(checkpoint0["allocations"]) == 1
    assert len(checkpoint1["allocations"]) == 2
    # generation 0's allocation is carried forward verbatim into generation 1's history
    assert checkpoint1["allocations"][0] == checkpoint0["allocations"][0]
    assert len(checkpoint0["metrics"]) == 1
    assert len(checkpoint1["metrics"]) == 2
    assert checkpoint1["metrics"][0] == checkpoint0["metrics"][0]
