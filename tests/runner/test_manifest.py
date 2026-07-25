import json
from pathlib import Path

import pytest

from human_data_budget.runner.manifest import (
    new_manifest,
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


def test_new_manifest_validates_against_schema() -> None:
    manifest = new_manifest(CONFIG, policy_name="random")
    validate_json(manifest, ROOT / "schemas/run_manifest.schema.json")
    assert manifest["status"] == "planned"
    assert manifest["status_history"] == [{"status": "planned"}]


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
