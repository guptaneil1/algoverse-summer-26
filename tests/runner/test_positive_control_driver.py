"""The resumable driver issues upstream's exact commands and resumes where it stopped.

Splitting an arm across sessions is only legitimate if the commands are unchanged. These
tests pin the argument lists against upstream ``main.py`` at the pinned commit, and pin the
two source facts that make splitting and pruning safe in the first place.
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from human_data_budget.runner.positive_control_adapter import (
    PositiveControlError,
    ingest_generation,
    mark_pruned,
    pruned_artifacts,
    upstream_artifact_paths,
    verify_recorded_hashes,
    write_artifact_record,
)

ROOT = Path(__file__).resolve().parents[2]
DRIVER_PATH = ROOT / "scripts/run_positive_control_arm.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("positive_control_driver", DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


driver = _load_driver()


def _flags(command: list[str]) -> dict[str, str]:
    """Turn a command list into {flag: value}, keeping bare flags as ''."""

    flags: dict[str, str] = {}
    index = 0
    while index < len(command):
        token = command[index]
        if token.startswith("--"):
            following = command[index + 1] if index + 1 < len(command) else ""
            if following.startswith("--"):
                flags[token] = ""
                index += 1
            else:
                flags[token] = following
                index += 2
        else:
            index += 1
    return flags


# ----------------------------------------------------------------------------------
# the two source facts that justify splitting and pruning
# ----------------------------------------------------------------------------------


def test_generation_zero_is_identical_across_arms(
    resolved_arm_config: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    """Sharing generation 0 is only sound if both arms would compute the same thing."""

    kwargs = {"experiment_path": tmp_path / "exp", "data_dir": tmp_path / "data"}
    synthetic = driver.train_command_generation_zero(
        resolved_arm_config("fully_synthetic"), **kwargs
    )
    mixed = driver.train_command_generation_zero(resolved_arm_config("human_mixed"), **kwargs)

    assert synthetic == mixed

    flags = _flags(synthetic)
    # The mixture parameter that distinguishes the arms is absent at generation 0,
    # exactly as in upstream main.py's initial training command.
    assert "--human_data_alpha" not in flags
    assert "--data_selection_strategy" not in flags
    assert flags["--ai_beta"] == "1.0"
    assert flags["--seed"] == "42"
    assert flags["--iteration"] == "0"


def test_every_generation_retrains_from_the_base_model(
    resolved_arm_config: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    """Pruning is safe only because no generation continues from the prior checkpoint."""

    config = resolved_arm_config("fully_synthetic")
    command = driver.train_command_recursive(
        config, experiment_path=tmp_path / "exp", data_dir=tmp_path / "data", generation=4
    )
    flags = _flags(command)

    assert flags["--model_name_or_path"] == "openai-community/gpt2"
    assert "exp/3" not in flags["--model_name_or_path"]
    assert flags["--train_file"].endswith("exp/4/data.json")


# ----------------------------------------------------------------------------------
# command construction mirrors upstream
# ----------------------------------------------------------------------------------


def test_recursive_train_command_carries_the_arm_mixture(
    resolved_arm_config: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    kwargs = {"experiment_path": tmp_path / "exp", "data_dir": tmp_path / "data",
              "generation": 1}
    synthetic = _flags(
        driver.train_command_recursive(resolved_arm_config("fully_synthetic"), **kwargs)
    )
    mixed = _flags(driver.train_command_recursive(resolved_arm_config("human_mixed"), **kwargs))

    assert synthetic["--human_data_alpha"] == "0.0"
    assert mixed["--human_data_alpha"] == "1.0"
    assert synthetic["--ai_beta"] == mixed["--ai_beta"] == "1.0"
    assert synthetic["--data_selection_strategy"] == "None"
    assert synthetic["--accumulate_ai_data"] == "False"

    differing = {key for key in synthetic if synthetic[key] != mixed.get(key)}
    assert differing == {"--human_data_alpha"}


def test_generate_command_matches_the_frozen_decoding_settings(
    resolved_arm_config: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    config = resolved_arm_config("fully_synthetic")
    command = driver.generate_command(
        config,
        experiment_path=tmp_path / "exp",
        data_dir=tmp_path / "data",
        generation=3,
        previous_model=tmp_path / "exp/2/model/final_model",
    )
    flags = _flags(command)

    assert flags["--top_k"] == "50"
    assert flags["--top_p"] == "1.0"
    assert flags["--temperature"] == "1.0"
    # block_size - loss_on_last_n_tokens, as computed in upstream main.py
    assert flags["--input_token_length"] == "256"
    assert flags["--block_size"] == "512"
    assert flags["--classify_text"] == "1"
    assert flags["--detector_path"] == "GeorgeDrayson/modernbert-ai-detection"
    assert flags["--model_path"].endswith("exp/2/model/final_model")


    assert flags["--model_path"].endswith("exp/2/model/final_model")


def test_self_bleu_sample_is_capped_below_the_upstream_default(
    resolved_arm_config: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    """The cap is a cost control on a post-hoc diagnostic, and must stay explicit.

    It is passed on every generation of both arms so the two chains remain comparable,
    and it is bounded well under upstream's default of 1000 so the saving is real.
    """
    for arm in ("fully_synthetic", "human_mixed"):
        command = driver.generate_command(
            resolved_arm_config(arm),
            experiment_path=tmp_path / "exp",
            data_dir=tmp_path / "data",
            generation=3,
            previous_model=tmp_path / "exp/2/model/final_model",
        )
        assert _flags(command)["--self_bleu_n_sample"] == str(driver.SELF_BLEU_N_SAMPLE)


# ----------------------------------------------------------------------------------
# resume
# ----------------------------------------------------------------------------------


def test_completion_is_keyed_on_the_hash_sidecar(
    tmp_path: Path, make_upstream_experiment: Callable[..., Path]
) -> None:
    experiment_path = make_upstream_experiment([10.0, 11.0])

    # Artifacts exist, but nothing has been recorded yet.
    assert driver.generation_is_complete(experiment_path, 0) is False

    write_artifact_record(experiment_path, 0)
    assert driver.generation_is_complete(experiment_path, 0) is True
    assert driver.generation_is_complete(experiment_path, 1) is False


def test_a_pruned_generation_still_counts_as_complete(
    tmp_path: Path, make_upstream_experiment: Callable[..., Path]
) -> None:
    """Pruning must not make finished work look unfinished on the next session."""

    experiment_path = make_upstream_experiment([10.0, 11.0])
    write_artifact_record(experiment_path, 0)
    mark_pruned(experiment_path, 0, "model_dir", "storage quota")

    model_dir = upstream_artifact_paths(experiment_path, 0)["model_dir"]
    for child in model_dir.iterdir():
        child.unlink()
    model_dir.rmdir()

    assert driver.generation_is_complete(experiment_path, 0) is True


def test_state_round_trips(tmp_path: Path) -> None:
    state = {"generations": {"0": {"status": "complete"}}, "remaining_generations": [1, 2]}
    driver.save_state(tmp_path, state)
    assert driver.load_state(tmp_path) == state


def test_missing_state_is_an_empty_start(tmp_path: Path) -> None:
    assert driver.load_state(tmp_path) == {"generations": {}}


# ----------------------------------------------------------------------------------
# pruning keeps the evidence chain honest
# ----------------------------------------------------------------------------------


def test_pruned_model_keeps_its_hash_through_ingest(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    experiment_path = make_upstream_experiment([10.0, 11.0])
    config = resolved_arm_config("fully_synthetic", horizon=2)

    recorded = write_artifact_record(experiment_path, 1)
    original_hash = recorded["artifacts"]["model_dir"]["sha256"]

    mark_pruned(experiment_path, 1, "model_dir", "storage quota")
    model_dir = upstream_artifact_paths(experiment_path, 1)["model_dir"]
    for child in model_dir.iterdir():
        child.unlink()
    model_dir.rmdir()

    record = ingest_generation(config, experiment_path=experiment_path, generation=1)
    assert record["artifacts"]["model_dir"]["sha256"] == original_hash
    assert record["artifacts"]["model_dir"]["pruned"] is True
    # The metric is untouched: only weights are prunable.
    assert record["metrics"]["perplexity"] == 11.0


def test_pruned_artifacts_are_reported_not_hidden(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    from human_data_budget.runner.positive_control_adapter import adapt_run

    experiment_path = make_upstream_experiment([10.0, 11.0])
    config = resolved_arm_config("fully_synthetic", horizon=2)

    write_artifact_record(experiment_path, 0)
    write_artifact_record(experiment_path, 1)
    mark_pruned(experiment_path, 0, "model_dir", "storage quota")
    model_dir = upstream_artifact_paths(experiment_path, 0)["model_dir"]
    for child in model_dir.iterdir():
        child.unlink()
    model_dir.rmdir()

    run_dir = tmp_path / "run"
    adapt_run(config, experiment_path=experiment_path, output_dir=run_dir, repo_root=ROOT)

    # A pruned artifact is not a mismatch...
    assert verify_recorded_hashes(run_dir) == []
    # ...but it is visible, with its reason, so the report can state the limitation.
    reported = pruned_artifacts(run_dir)
    assert len(reported) == 1
    assert reported[0]["generation"] == 0
    assert reported[0]["artifact"] == "model_dir"
    assert reported[0]["reason"] == "storage quota"
    assert len(reported[0]["sha256"]) == 64


def test_tampering_is_still_caught_when_the_artifact_survives(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    """The sidecar must not become a way to launder a changed artifact."""

    experiment_path = make_upstream_experiment([10.0, 11.0])
    config = resolved_arm_config("fully_synthetic", horizon=2)
    write_artifact_record(experiment_path, 1)

    weights = upstream_artifact_paths(experiment_path, 1)["model_dir"] / "model.safetensors"
    weights.write_bytes(b"tampered")

    with pytest.raises(PositiveControlError, match="changed since the run recorded it"):
        ingest_generation(config, experiment_path=experiment_path, generation=1)


def test_only_model_directories_may_be_pruned(
    tmp_path: Path, make_upstream_experiment: Callable[..., Path]
) -> None:
    experiment_path = make_upstream_experiment([10.0, 11.0])
    write_artifact_record(experiment_path, 1)

    for protected in ("eval_results", "generated_data"):
        with pytest.raises(PositiveControlError, match="scientific record"):
            mark_pruned(experiment_path, 1, protected, "should be refused")


def test_pruning_refuses_when_nothing_was_hashed_first(
    tmp_path: Path, make_upstream_experiment: Callable[..., Path]
) -> None:
    """Hash before you delete, or the deletion destroys the evidence."""

    experiment_path = make_upstream_experiment([10.0])
    with pytest.raises(Exception, match="Hash before you delete"):
        mark_pruned(experiment_path, 0, "model_dir", "premature")


def test_artifact_record_is_written_next_to_the_generation(
    tmp_path: Path, make_upstream_experiment: Callable[..., Path]
) -> None:
    experiment_path = make_upstream_experiment([10.0, 11.0])
    write_artifact_record(experiment_path, 1)

    sidecar = experiment_path / "1" / "artifact_record.json"
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["generation"] == 1
    assert set(payload["artifacts"]) == {"model_dir", "eval_results", "generated_data"}
    assert all(entry["pruned"] is False for entry in payload["artifacts"].values())


# ----------------------------------------------------------------------------------
# the subprocess environment actually reaches the subprocess
# ----------------------------------------------------------------------------------


def _capture_run_step_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **kwargs):
    """Run one step with subprocess.run stubbed, returning the env it was handed."""

    captured: dict[str, Any] = {}

    class _Result:
        returncode = 0

    def fake_run(command, **call_kwargs):
        captured["command"] = command
        captured["kwargs"] = call_kwargs
        return _Result()

    monkeypatch.setattr(driver.subprocess, "run", fake_run)
    driver.run_step(
        ["python", "-c", "pass"],
        upstream_dir=tmp_path,
        log_path=tmp_path / "log.txt",
        dry_run=False,
        **kwargs,
    )
    return captured


def test_run_step_passes_its_environment_to_the_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression that put both arms on one GPU for an hour.

    run_step built an environment dict and called subprocess.run without env=, so
    every setting it configured was discarded and the child inherited the parent's
    environment instead. --cuda-device then had no effect whatsoever.
    """

    captured = _capture_run_step_env(tmp_path, monkeypatch, cuda_device=1)

    assert "env" in captured["kwargs"], (
        "subprocess.run was called without env=; the configured environment is dropped"
    )
    assert captured["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] == "1"


def test_run_step_pins_the_requested_gpu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for device in (0, 1):
        captured = _capture_run_step_env(tmp_path, monkeypatch, cuda_device=device)
        assert captured["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] == str(device)


def test_run_step_disables_wandb_in_the_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = _capture_run_step_env(tmp_path, monkeypatch, cuda_device=0)
    environment = captured["kwargs"]["env"]
    assert environment["WANDB_DISABLED"] == "true"
    assert environment["WANDB_MODE"] == "disabled"
