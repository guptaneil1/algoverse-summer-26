#!/usr/bin/env python3
"""Fail CI when required collaboration/research scaffold paths disappear."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "README.md",
    "CLAIMS.md",
    "COMPUTE.md",
    "DECISIONS.md",
    "FAILURE_LOG.md",
    "PROTOCOL.md",
    "PREREGISTRATION.md",
    "docs/PROJECT_CONTEXT.md",
    "docs/GITHUB_SETUP.md",
    "docs/TEAM.md",
    "docs/STATUS.md",
    "docs/ROADMAP.md",
    "docs/WORKFLOW.md",
    "docs/ARCHITECTURE.md",
    "docs/weekly/WEEK_1.md",
    "docs/weekly/WEEK_2.md",
    "docs/weekly/WEEK_3.md",
    "docs/weekly/WEEK_4.md",
    "schemas/run_manifest.schema.json",
    "schemas/chain_result.schema.json",
    "configs/experiment/toy_cpu.json",
    "uv.lock",
    "requirements-lock.txt",
    # Stage A positive-control package (Week 2).
    "configs/experiment/positive_control_fully_synthetic.json",
    "configs/experiment/positive_control_human_mixed.json",
    "scripts/reproduce_positive_control.sh",
    "src/human_data_budget/runner/positive_control_adapter.py",
    "docs/positive_control/expected_vs_observed.md",
    "docs/benchmarks/khantushig_week2.md",
    "tests/runner/test_positive_control_contract.py",
    "tests/runner/test_real_checkpoint_resume.py",
    "tests/runner/test_reproduction_command.py",
    "tests/runner/test_artifact_hashes.py",
]

#: Experiment configs that must remain parseable JSON.
EXPERIMENT_CONFIGS = [
    "configs/experiment/toy_cpu.json",
    "configs/experiment/positive_control_fully_synthetic.json",
    "configs/experiment/positive_control_human_mixed.json",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-structure", action="store_true")
    args = parser.parse_args()
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("missing required repository paths:\n" + "\n".join(missing))
    for path in (ROOT / "schemas").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    for config in EXPERIMENT_CONFIGS:
        json.loads((ROOT / config).read_text(encoding="utf-8"))
    if args.strict_structure:
        required_directories = ["src", "tests", "configs", "data", "docs", "paper", "results"]
        absent = [name for name in required_directories if not (ROOT / name).is_dir()]
        if absent:
            raise SystemExit("missing required directories: " + ", ".join(absent))
    print("repository scaffold audit passed")


if __name__ == "__main__":
    main()
