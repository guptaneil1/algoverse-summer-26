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
    json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text(encoding="utf-8"))
    if args.strict_structure:
        required_directories = ["src", "tests", "configs", "data", "docs", "paper", "results"]
        absent = [name for name in required_directories if not (ROOT / name).is_dir()]
        if absent:
            raise SystemExit("missing required directories: " + ", ".join(absent))
    print("repository scaffold audit passed")


if __name__ == "__main__":
    main()
