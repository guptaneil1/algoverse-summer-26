"""Every recorded checkpoint, generated-data, metric, and config reference has a hash.

Hashes only mean something if they are checked, and if a changed artifact actually
breaks the check. Both halves are tested here: a clean ingest verifies, and a mutated,
truncated, or deleted artifact is detected.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from human_data_budget.runner.checkpoint import checkpoint_path
from human_data_budget.runner.positive_control_adapter import (
    adapt_run,
    sha256_file,
    sha256_path,
    sha256_tree,
    verify_recorded_hashes,
)

ROOT = Path(__file__).resolve().parents[2]

FAKE_PERPLEXITIES = [18.0, 21.0, 26.0]

#: Artifacts that must carry a hash at every generation where they exist.
EXPECTED_ARTIFACT_KEYS = {"model_dir", "eval_results"}


def _run(config: dict[str, Any], experiment_path: Path, output_dir: Path):
    return adapt_run(
        config,
        experiment_path=experiment_path,
        output_dir=output_dir,
        repo_root=ROOT,
    )


def test_every_generation_records_a_hash_for_every_artifact(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)
    run_dir = tmp_path / "run"

    _run(config, experiment_path, run_dir)

    final = json.loads(
        checkpoint_path(run_dir, len(FAKE_PERPLEXITIES) - 1).read_text(encoding="utf-8")
    )
    assert len(final["records"]) == len(FAKE_PERPLEXITIES)

    for record in final["records"]:
        artifacts = record["artifacts"]
        assert EXPECTED_ARTIFACT_KEYS <= set(artifacts)
        # Generated data exists for every generation above zero, and only those.
        assert ("generated_data" in artifacts) == (record["generation"] > 0)
        for name, artifact in artifacts.items():
            assert len(artifact["sha256"]) == 64, f"{name} hash is not a SHA-256"
            assert artifact["path"], f"{name} recorded no path"


def test_manifest_records_the_artifact_list(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)
    run_dir = tmp_path / "run"

    manifest, _ = _run(config, experiment_path, run_dir)
    written = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))

    assert len(manifest["artifacts"]) == len(FAKE_PERPLEXITIES)
    assert written["artifacts"] == manifest["artifacts"]
    assert written["git_commit"] != "0" * 40, "manifest must record the real project commit"
    assert written["stage"] == "positive_control"


def test_clean_run_verifies(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)
    run_dir = tmp_path / "run"

    _run(config, experiment_path, run_dir)

    assert verify_recorded_hashes(run_dir) == []


def test_mutated_metric_file_is_detected(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    """The exact failure this guards against: a metric edited after the fact."""

    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)
    run_dir = tmp_path / "run"
    _run(config, experiment_path, run_dir)

    tampered = experiment_path / "2" / "model" / "eval_results.json"
    tampered.write_text(json.dumps({"perplexity": 1.0, "eval_loss": 0.0}), encoding="utf-8")

    mismatches = verify_recorded_hashes(run_dir)
    assert mismatches
    assert any("eval_results" in mismatch for mismatch in mismatches)


def test_mutated_model_checkpoint_is_detected(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)
    run_dir = tmp_path / "run"
    _run(config, experiment_path, run_dir)

    weights = experiment_path / "1" / "model" / "final_model" / "model.safetensors"
    weights.write_bytes(b"different-weights")

    mismatches = verify_recorded_hashes(run_dir)
    assert any("model_dir" in mismatch for mismatch in mismatches)


def test_deleted_generated_data_is_detected(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)
    run_dir = tmp_path / "run"
    _run(config, experiment_path, run_dir)

    (experiment_path / "2" / "data.json").unlink()

    mismatches = verify_recorded_hashes(run_dir)
    assert any("is gone" in mismatch for mismatch in mismatches)


def test_verification_reports_a_missing_run_directory(tmp_path: Path) -> None:
    mismatches = verify_recorded_hashes(tmp_path / "never_ran")
    assert mismatches == [f"no checkpoints directory under {tmp_path / 'never_ran'}"]


def test_directory_hash_is_order_independent_and_content_sensitive(tmp_path: Path) -> None:
    """A checkpoint directory must hash the same way twice, and differently when changed."""

    first = tmp_path / "first"
    second = tmp_path / "second"
    for directory, order in ((first, ["a", "b"]), (second, ["b", "a"])):
        (directory / "nested").mkdir(parents=True)
        for name in order:
            (directory / "nested" / name).write_text(name, encoding="utf-8")

    assert sha256_tree(first) == sha256_tree(second)

    (second / "nested" / "a").write_text("changed", encoding="utf-8")
    assert sha256_tree(first) != sha256_tree(second)


def test_sha256_path_dispatches_on_file_or_directory(tmp_path: Path) -> None:
    a_file = tmp_path / "artifact.json"
    a_file.write_text("{}", encoding="utf-8")

    assert sha256_path(a_file) == sha256_file(a_file)
    assert sha256_path(tmp_path) == sha256_tree(tmp_path)
