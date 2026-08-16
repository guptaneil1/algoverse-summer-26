import json
from pathlib import Path

import pytest

from human_data_budget.runner.failure import FailureState
from human_data_budget.runner.manifest import (
    attach_failure,
    new_manifest,
    record_generation,
    transition_status,
    write_manifest_atomic,
)
from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[2]

CONFIG = {
    "run_id": "fixture_manifest_test",
    "horizon": 3,
    "chain_seed": 1,
    "lifetime_human_budget": 60,
    "total_optimizer_tokens": 300,
}

# Every field the manifest is required to hold, per spec: run ID, commit hash,
# model/tokenizer IDs, Python version, chain seed, lifetime human-token
# budget, total-token budget, current generation, status, structured failure
# info.
REQUIRED_TOP_LEVEL_FIELDS = (
    "run_id",
    "git_commit",
    "model",
    "randomness",
    "budget",
    "current_generation",
    "status",
    "failure",
)


def test_new_manifest_validates_against_schema() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    validate_json(manifest, ROOT / "schemas/run_manifest.schema.json")
    assert manifest["status"] == "planned"
    assert manifest["status_history"] == [{"status": "planned"}]


def test_new_manifest_omits_partitions_when_no_provenance_declared() -> None:
    """Provenance is never synthesised: no declared source means no partitions block.

    The validator then classifies the run ``invalid``, which is the correct outcome.
    Provenance emission is covered in ``test_manifest_provenance.py``.
    """

    manifest = new_manifest(CONFIG, policy_name="random")

    assert "partitions" not in manifest["data"]


def test_new_manifest_holds_all_required_fields() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in manifest, f"missing required manifest field: {field}"

    assert manifest["run_id"] == CONFIG["run_id"]
    assert manifest["git_commit"] == "0" * 40
    assert manifest["model"]["identifier"]
    assert manifest["model"]["tokenizer_revision"]
    assert manifest["environment"]["python"]
    assert manifest["randomness"]["chain_seed"] == CONFIG["chain_seed"]
    assert manifest["budget"]["lifetime_human_optimizer_tokens"] == CONFIG["lifetime_human_budget"]
    assert manifest["budget"]["total_optimizer_tokens"] == CONFIG["total_optimizer_tokens"]
    # No generation has run yet and no failure has occurred.
    assert manifest["current_generation"] is None
    assert manifest["failure"] is None


def test_new_manifest_records_actual_python_version() -> None:
    import platform

    manifest = new_manifest(CONFIG, policy_name="random")
    assert manifest["environment"]["python"] == platform.python_version()


def test_record_generation_advances_current_generation() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    updated = record_generation(manifest, 0)
    assert updated["current_generation"] == 0
    updated = record_generation(updated, 1)
    assert updated["current_generation"] == 1
    # append-only: earlier manifest objects are untouched
    assert manifest["current_generation"] is None


def test_record_generation_rejects_negative_generation() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    with pytest.raises(ValueError):
        record_generation(manifest, -1)


def test_attach_failure_records_structured_failure_info() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    failure = FailureState(
        run_id=CONFIG["run_id"],
        category="implementation_defect",
        message="allocation exceeded budget",
        generation=1,
        evidence={"error_type": "ValueError"},
    )
    updated = attach_failure(manifest, failure.as_dict())
    assert updated["failure"] == failure.as_dict()
    assert updated["failure"]["category"] == "implementation_defect"
    assert updated["failure"]["generation"] == 1
    # append-only: the original manifest is untouched
    assert manifest["failure"] is None


def test_transition_status_appends_history_without_erasing() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    running = transition_status(manifest, "running")
    complete = transition_status(running, "complete")
    assert complete["status"] == "complete"
    assert complete["status_history"] == [
        {"status": "planned"},
        {"status": "running"},
        {"status": "complete"},
    ]
    # earlier manifest objects are untouched (append-only, not in-place)
    assert manifest["status"] == "planned"
    assert running["status"] == "running"


def test_illegal_transition_rejected() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    with pytest.raises(ValueError):
        transition_status(manifest, "complete")


def test_terminal_status_has_no_further_transitions() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    running = transition_status(manifest, "running")
    complete = transition_status(running, "complete")
    with pytest.raises(ValueError):
        transition_status(complete, "running")


def test_write_manifest_atomic_round_trips(tmp_path: Path) -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    path = tmp_path / "nested" / "run_manifest.json"
    write_manifest_atomic(manifest, path)
    assert json.loads(path.read_text(encoding="utf-8")) == manifest
    assert not (path.parent / "run_manifest.json.tmp").exists()
