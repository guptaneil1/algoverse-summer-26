"""An interrupted ingest and an uninterrupted ingest satisfy the frozen equivalence rule.

The equivalence claim tested here is deliberately narrow, and the narrowness is the
point. This exercises the *adapter's* resume path: ingesting an existing upstream run
into the frozen contracts is a pure function of the artifacts on disk, so it is exactly
reproducible and the comparison can be byte-for-byte.

It does NOT claim that re-running upstream training from a checkpoint reproduces
bit-identical weights. That is a separate, weaker claim about a framework this
repository does not control, and ``docs/positive_control/expected_vs_observed.md``
records the honest tolerance for it rather than asserting equality here.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from human_data_budget.runner.checkpoint import checkpoint_path, latest_checkpoint
from human_data_budget.runner.positive_control_adapter import (
    UnresolvedIdentifierError,
    adapt_run,
    load_arm_config,
)

ROOT = Path(__file__).resolve().parents[2]

# A monotonically degrading fake curve. The values carry no scientific meaning; they
# exist so the summary arithmetic has something deterministic to chew on.
FAKE_PERPLEXITIES = [20.0, 22.0, 25.0, 29.0, 34.0]


def _run(config: dict[str, Any], experiment_path: Path, output_dir: Path, **kwargs: Any):
    return adapt_run(
        config,
        experiment_path=experiment_path,
        output_dir=output_dir,
        repo_root=ROOT,
        **kwargs,
    )


def _copy_checkpoints_through(source: Path, destination: Path, last_generation: int) -> None:
    """Simulate a crash: only checkpoints up to ``last_generation`` survived."""

    (destination / "checkpoints").mkdir(parents=True)
    for generation in range(last_generation + 1):
        name = checkpoint_path(source, generation).name
        (destination / "checkpoints" / name).write_text(
            (source / "checkpoints" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )


def test_resumed_ingest_matches_uninterrupted_ingest_exactly(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)

    full_dir = tmp_path / "full"
    full_manifest, full_summary = _run(config, experiment_path, full_dir)

    resume_dir = tmp_path / "resume"
    _copy_checkpoints_through(full_dir, resume_dir, last_generation=1)
    resume_manifest, resume_summary = _run(config, experiment_path, resume_dir, resume=True)

    # 1. scientific state
    assert resume_summary == full_summary

    # 2. generation-wise metric outputs
    assert resume_summary["metric_by_generation"] == full_summary["metric_by_generation"]
    assert resume_summary["degradation_ratio"] == full_summary["degradation_ratio"]

    # 3. artifact hashes, generation by generation
    for generation in range(len(FAKE_PERPLEXITIES)):
        resumed = json.loads(
            checkpoint_path(resume_dir, generation).read_text(encoding="utf-8")
        )
        uninterrupted = json.loads(
            checkpoint_path(full_dir, generation).read_text(encoding="utf-8")
        )
        assert resumed == uninterrupted

    # 4. manifest history: both reached complete, neither erased earlier state
    assert resume_manifest["status"] == full_manifest["status"] == "complete"
    assert resume_manifest["current_generation"] == full_manifest["current_generation"]
    assert [entry["status"] for entry in resume_manifest["status_history"]] == [
        "planned",
        "running",
        "complete",
    ]


def test_resume_does_not_recompute_surviving_generations(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resume must continue from the checkpoint, not silently redo finished work."""

    from human_data_budget.runner import positive_control_adapter as adapter

    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)

    full_dir = tmp_path / "full"
    _run(config, experiment_path, full_dir)

    resume_dir = tmp_path / "resume"
    _copy_checkpoints_through(full_dir, resume_dir, last_generation=2)

    ingested: list[int] = []
    real_ingest = adapter.ingest_generation

    def spy_ingest(config_arg, *, experiment_path, generation):
        ingested.append(generation)
        return real_ingest(config_arg, experiment_path=experiment_path, generation=generation)

    monkeypatch.setattr(adapter, "ingest_generation", spy_ingest)
    _run(config, experiment_path, resume_dir, resume=True)

    assert ingested == [3, 4]


def test_resume_without_a_checkpoint_ingests_every_generation(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    config = resolved_arm_config("fully_synthetic", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)

    fresh_dir = tmp_path / "fresh"
    resume_dir = tmp_path / "resume_no_checkpoint"

    _, fresh_summary = _run(config, experiment_path, fresh_dir)
    _, resumed_summary = _run(config, experiment_path, resume_dir, resume=True)

    assert resumed_summary == fresh_summary
    assert latest_checkpoint(resume_dir) is not None


def test_both_arms_resume_equivalently(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
    resolved_arm_config: Callable[..., dict[str, Any]],
) -> None:
    """The equivalence rule must hold for the human-mixed arm too, not just arm A."""

    config = resolved_arm_config("human_mixed", horizon=len(FAKE_PERPLEXITIES))
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)

    full_dir = tmp_path / "full_mixed"
    _, full_summary = _run(config, experiment_path, full_dir)

    resume_dir = tmp_path / "resume_mixed"
    _copy_checkpoints_through(full_dir, resume_dir, last_generation=0)
    _, resume_summary = _run(config, experiment_path, resume_dir, resume=True)

    assert resume_summary == full_summary
    assert resume_summary["arm"] == "human_mixed"


def test_ingest_refuses_unresolved_identifiers(
    tmp_path: Path,
    make_upstream_experiment: Callable[..., Path],
) -> None:
    """The committed config must not be runnable until the host resolves its revisions."""

    config = load_arm_config(ROOT / "configs/experiment/positive_control_fully_synthetic.json")
    config["horizon"] = len(FAKE_PERPLEXITIES)
    experiment_path = make_upstream_experiment(FAKE_PERPLEXITIES)

    with pytest.raises(UnresolvedIdentifierError):
        _run(config, experiment_path, tmp_path / "blocked")
