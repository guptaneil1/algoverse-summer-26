"""The frozen resume-equivalence rule, checked on every dimension it names.

`docs/weekly/WEEK_3.md` and the Week 3 packet state the rule as: stop the same
frozen seed and config at an approved checkpoint, resume once, finish, then
compare *cumulative token ledgers, generation state, manifest history, metric
outputs, and deterministic hashes where the framework allows*.

`test_checkpoint_resume.py` already proves the resumed chain equals the
uninterrupted one and that generation 0 is not recomputed. It compares whole
result objects, so a regression in any single dimension would surface as an
opaque dict inequality. These tests assert each named dimension separately, so a
failure says which invariant broke.

The ledger case is the one that matters most in practice: the classic resume bug
is re-adding the tokens of the generation you resumed from, which silently
inflates consumption above the frozen budget and would make the chain
budget-mismatched rather than obviously broken.

Scope: this is the **smoke** condition, which is what the packet's test table
specifies. It exercises the toy CPU path with no model and no accelerator. It
says nothing about GPU kernel nondeterminism, dataloader ordering, or mixed
precision — see `docs/runner/week3_integrity_report.md` §5.
"""

import hashlib
import json
from pathlib import Path

import pytest

from human_data_budget.runner.chain import run_toy_chain

ROOT = Path(__file__).resolve().parents[2]


def _config() -> dict:
    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))
    config["horizon"] = 2
    return config


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_generation_zero_checkpoint(full_dir: Path, resume_dir: Path) -> None:
    """Simulate a crash immediately after generation 0's checkpoint was written."""

    (resume_dir / "checkpoints").mkdir(parents=True)
    checkpoint = full_dir / "checkpoints" / "generation_0000.json"
    (resume_dir / "checkpoints" / checkpoint.name).write_text(
        checkpoint.read_text(encoding="utf-8"), encoding="utf-8"
    )


@pytest.fixture
def interrupted_and_uninterrupted(tmp_path: Path) -> tuple[dict, dict, Path, Path]:
    """One uninterrupted chain and one stopped-then-resumed chain, same seed and config."""

    config = _config()

    full_dir = tmp_path / "uninterrupted"
    full_manifest, full_result = run_toy_chain(config, output_dir=full_dir)

    resume_dir = tmp_path / "resumed"
    _seed_generation_zero_checkpoint(full_dir, resume_dir)
    resume_manifest, resume_result = run_toy_chain(config, output_dir=resume_dir, resume=True)

    return (
        {"manifest": full_manifest, "result": full_result},
        {"manifest": resume_manifest, "result": resume_result},
        full_dir,
        resume_dir,
    )


def test_cumulative_token_ledgers_continue_exactly_once(
    interrupted_and_uninterrupted: tuple[dict, dict, Path, Path],
) -> None:
    """Resuming must not re-add the tokens of the generation it resumed from."""

    full, resumed, _, _ = interrupted_and_uninterrupted

    assert resumed["result"].consumed_human_tokens == full["result"].consumed_human_tokens
    assert resumed["result"].consumed_total_tokens == full["result"].consumed_total_tokens

    # Guard against the double-count specifically, not just against inequality:
    # a resumed chain that replayed generation 0's ledger would exceed the
    # uninterrupted total, and could breach the frozen budget.
    config = _config()
    assert resumed["result"].consumed_human_tokens <= config["lifetime_human_budget"]
    assert resumed["result"].consumed_total_tokens <= config["total_optimizer_tokens"]


def test_generation_state_matches(
    interrupted_and_uninterrupted: tuple[dict, dict, Path, Path],
) -> None:
    full, resumed, _, _ = interrupted_and_uninterrupted

    assert resumed["result"].generations_completed == full["result"].generations_completed
    assert resumed["manifest"]["current_generation"] == full["manifest"]["current_generation"]
    assert resumed["manifest"]["horizon"] == full["manifest"]["horizon"]


def test_manifest_status_history_matches_and_is_terminal(
    interrupted_and_uninterrupted: tuple[dict, dict, Path, Path],
) -> None:
    full, resumed, _, _ = interrupted_and_uninterrupted

    assert resumed["manifest"]["status"] == full["manifest"]["status"] == "complete"
    assert resumed["manifest"]["status_history"] == full["manifest"]["status_history"]
    # Append-only: planned must remain the first recorded state.
    assert resumed["manifest"]["status_history"][0]["status"] == "planned"


def test_metric_outputs_match_generation_by_generation(
    interrupted_and_uninterrupted: tuple[dict, dict, Path, Path],
) -> None:
    full, resumed, _, _ = interrupted_and_uninterrupted

    full_metrics = [metric.as_dict() for metric in full["result"].metrics]
    resumed_metrics = [metric.as_dict() for metric in resumed["result"].metrics]

    assert resumed_metrics == full_metrics
    assert full_metrics, "the chain must produce at least one generation metric"


def test_persisted_artifact_hashes_match(
    interrupted_and_uninterrupted: tuple[dict, dict, Path, Path],
) -> None:
    """Deterministic hashes, which the toy framework does allow."""

    _, _, full_dir, resume_dir = interrupted_and_uninterrupted

    for name in ("chain_result.json", "run_manifest.json"):
        assert _sha256(full_dir / name) == _sha256(resume_dir / name), name

    for checkpoint in sorted((full_dir / "checkpoints").glob("*.json")):
        counterpart = resume_dir / "checkpoints" / checkpoint.name
        assert counterpart.is_file(), f"{checkpoint.name} missing from the resumed run"
        assert _sha256(checkpoint) == _sha256(counterpart), checkpoint.name
