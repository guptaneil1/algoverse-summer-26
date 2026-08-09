"""Corrupt hashes, missing files, and unreadable artifacts produce the expected codes."""

import json
from collections.abc import Callable
from pathlib import Path

from human_data_budget.validation.audit import audit_run, sha256_file
from human_data_budget.validation.classification import INVALID, VALID_WITH_LIMITATION


def test_corrupt_checkpoint_hash_is_detected(make_run: Callable[..., Path]) -> None:
    run = make_run()
    (run / "checkpoint.txt").write_text("tampered-bytes", encoding="utf-8")

    report = audit_run(run)
    assert report.classification == INVALID
    assert "ARTIFACT_HASH_MISMATCH" in report.reason_codes


def test_missing_referenced_artifact_is_detected(make_run: Callable[..., Path]) -> None:
    run = make_run()
    (run / "checkpoint.txt").unlink()

    report = audit_run(run)
    assert report.classification == INVALID
    assert "ARTIFACT_MISSING" in report.reason_codes


def test_artifact_without_recorded_hash_is_a_limitation(make_run: Callable[..., Path]) -> None:
    def drop_hash(manifest: dict) -> None:
        manifest["artifacts"] = [{"path": "notes.txt"}]

    run = make_run(drop_hash, checkpoint_text=None)
    (run / "notes.txt").write_text("unhashed", encoding="utf-8")

    report = audit_run(run)
    assert report.classification == VALID_WITH_LIMITATION
    assert "LIMIT_MISSING_OPTIONAL_ARTIFACT" in report.reason_codes


def test_missing_chain_result_is_detected(make_run: Callable[..., Path]) -> None:
    run = make_run()
    (run / "chain_result.json").unlink()

    report = audit_run(run)
    assert report.classification == INVALID
    assert "ARTIFACT_MISSING" in report.reason_codes


def test_unparseable_manifest_is_schema_invalid(make_run: Callable[..., Path]) -> None:
    run = make_run()
    (run / "run_manifest.json").write_text("{not json", encoding="utf-8")

    report = audit_run(run)
    assert report.classification == INVALID
    assert "ARTIFACT_SCHEMA_INVALID" in report.reason_codes


def test_absent_directory_reports_missing_artifacts(tmp_path: Path) -> None:
    report = audit_run(tmp_path / "no_such_run")
    assert report.classification == INVALID
    assert "ARTIFACT_MISSING" in report.reason_codes


def test_input_hashes_are_recorded_for_audited_files(valid_run: Path) -> None:
    report = audit_run(valid_run)
    assert report.input_hashes["run_manifest"] == sha256_file(valid_run / "run_manifest.json")
    assert report.input_hashes["chain_result"] == sha256_file(valid_run / "chain_result.json")


def test_audit_does_not_mutate_the_run_directory(valid_run: Path) -> None:
    before = {
        path.name: sha256_file(path) for path in sorted(valid_run.iterdir()) if path.is_file()
    }
    audit_run(valid_run)
    after = {
        path.name: sha256_file(path) for path in sorted(valid_run.iterdir()) if path.is_file()
    }
    assert before == after


def test_audit_reads_the_recorded_manifest_run_id(make_run: Callable[..., Path]) -> None:
    def rename(manifest: dict) -> None:
        manifest["run_id"] = "chain-42"

    def rename_result(result: dict) -> None:
        result["run_id"] = "chain-42"

    run = make_run(rename, rename_result, name="directory_name_differs")
    report = audit_run(run)
    assert report.run_id == "chain-42"


def test_report_round_trips_through_json(valid_run: Path) -> None:
    report = audit_run(valid_run, audited_at="2026-08-09T00:00:00+00:00")
    restored = json.loads(json.dumps(report.to_dict()))
    assert restored["classification"] == report.classification
    assert restored["audited_at"] == "2026-08-09T00:00:00+00:00"
