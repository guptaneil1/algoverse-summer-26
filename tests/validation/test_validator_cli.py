"""One command writes a machine-readable report and never mutates the audited run."""

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from human_data_budget.validation.audit import sha256_file

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts" / "validate_run.py"

REQUIRED_FIELDS = {
    "run_id",
    "classification",
    "reason_codes",
    "checks_passed",
    "checks_failed",
    "limitations",
    "input_hashes",
    "validator_commit",
    "audited_at",
}


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def test_valid_run_exits_zero_with_full_report(valid_run: Path) -> None:
    completed = run_cli(str(valid_run))
    assert completed.returncode == 0, completed.stdout + completed.stderr

    payload = json.loads(completed.stdout)
    assert payload["classification"] == "valid"
    assert REQUIRED_FIELDS <= set(payload)


def test_invalid_run_exits_two(make_run: Callable[..., Path]) -> None:
    def leak(manifest: dict) -> None:
        partitions = manifest["data"]["partitions"]
        partitions["generation_prompts"] = list(partitions["final_human_test"])

    completed = run_cli(str(make_run(leak)))
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["classification"] == "invalid"


def test_limited_run_exits_one(make_run: Callable[..., Path]) -> None:
    def short(result: dict) -> None:
        result["generations_completed"] = 1
        result["metrics"] = result["metrics"][:1]

    completed = run_cli(str(make_run(None, short)))
    assert completed.returncode == 1
    assert json.loads(completed.stdout)["classification"] == "valid_with_limitation"


def test_schema_violation_is_reported_and_invalid(make_run: Callable[..., Path]) -> None:
    def break_schema(result: dict) -> None:
        result["generations_completed"] = "two"

    completed = run_cli(str(make_run(None, break_schema)))
    assert completed.returncode == 2

    payload = json.loads(completed.stdout)
    assert payload["classification"] == "invalid"
    assert payload["schema_failures"]


def test_report_file_is_written(valid_run: Path, tmp_path: Path) -> None:
    destination = tmp_path / "reports" / "certificate.json"
    completed = run_cli(str(valid_run), "--report", str(destination))
    assert completed.returncode == 0
    assert json.loads(destination.read_text(encoding="utf-8"))["classification"] == "valid"


def test_cli_does_not_mutate_the_audited_directory(valid_run: Path) -> None:
    before = {
        path.name: sha256_file(path) for path in sorted(valid_run.iterdir()) if path.is_file()
    }
    run_cli(str(valid_run))
    after = {
        path.name: sha256_file(path) for path in sorted(valid_run.iterdir()) if path.is_file()
    }
    assert before == after


def test_missing_directory_is_a_usage_error(tmp_path: Path) -> None:
    completed = run_cli(str(tmp_path / "absent"))
    assert completed.returncode == 3


def test_audited_at_is_caller_supplied(valid_run: Path) -> None:
    stamp = "2026-08-07T23:59:00+00:00"
    completed = run_cli(str(valid_run), "--audited-at", stamp)
    assert json.loads(completed.stdout)["audited_at"] == stamp
