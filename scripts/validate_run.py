#!/usr/bin/env python3
"""Audit one run directory and emit exactly one validity classification.

Contract checks (JSON schema) run first; the full audit then applies the frozen
validity rules and prints a machine-readable report. The command never mutates
the audited directory.

    python scripts/validate_run.py <run_directory>
    python scripts/validate_run.py <run_directory> --report out/report.json

Exit codes: 0 valid, 1 valid_with_limitation, 2 invalid, 3 usage error.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from human_data_budget.runner.schema import validate_json
from human_data_budget.validation.audit import audit_run
from human_data_budget.validation.classification import (
    INVALID,
    VALID,
    VALID_WITH_LIMITATION,
)

ROOT = Path(__file__).resolve().parents[1]

EXIT_CODES = {VALID: 0, VALID_WITH_LIMITATION: 1, INVALID: 2}


def validator_commit() -> str:
    """Return the commit the validator itself is running from."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def contract_check(run_directory: Path) -> list[str]:
    """Validate the two core artifacts against their frozen schemas."""
    failures: list[str] = []
    pairs = (
        ("run_manifest.json", "schemas/run_manifest.schema.json"),
        ("chain_result.json", "schemas/chain_result.schema.json"),
    )
    for name, schema in pairs:
        path = run_directory / name
        if not path.is_file():
            failures.append(f"{name}: absent")
            continue
        try:
            validate_json(json.loads(path.read_text(encoding="utf-8")), ROOT / schema)
        except Exception as error:  # noqa: BLE001 - reported, never raised onward
            failures.append(f"{name}: {error}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--report", type=Path, help="write the JSON report to this path")
    parser.add_argument(
        "--audited-at",
        default=datetime.now(timezone.utc).isoformat(),
        help="timestamp recorded in the report; pass a fixed value for reproducible output",
    )
    args = parser.parse_args()

    if not args.run_directory.is_dir():
        print(f"not a directory: {args.run_directory}")
        return 3

    schema_failures = contract_check(args.run_directory)
    report = audit_run(
        args.run_directory,
        validator_commit=validator_commit(),
        audited_at=args.audited_at,
    )

    if schema_failures:
        report.classification = INVALID
        if "ARTIFACT_SCHEMA_INVALID" not in report.reason_codes:
            report.reason_codes = sorted([*report.reason_codes, "ARTIFACT_SCHEMA_INVALID"])
        report.checks_failed = sorted([*report.checks_failed, "artifact_schema:contract"])

    payload = report.to_dict()
    if schema_failures:
        payload["schema_failures"] = schema_failures

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")

    return EXIT_CODES[report.classification]


if __name__ == "__main__":
    raise SystemExit(main())
