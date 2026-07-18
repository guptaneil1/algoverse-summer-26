#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    manifest_path = args.run_directory / "run_manifest.json"
    result_path = args.run_directory / "chain_result.json"
    validate_json(json.loads(manifest_path.read_text()), ROOT / "schemas/run_manifest.schema.json")
    validate_json(json.loads(result_path.read_text()), ROOT / "schemas/chain_result.schema.json")
    print("VALID CONTRACT ARTIFACTS (scientific validity still requires Neil's full audit)")


if __name__ == "__main__":
    main()
