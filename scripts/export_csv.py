#!/usr/bin/env python3
"""Export schema-valid chain results to chain-level and summary CSV.

Implements the CSV half of the `docs/weekly/WEEK_4.md` Aarav clause "Generate
LaTeX/CSV/figures and hashes through one reproducible command".

Two files are written:

``chain_level_long.csv``
    One row per (chain, generation). This is the analysis-ready long format and
    the only one that preserves the within-chain structure. `PROTOCOL.md` §4 is
    explicit that generations within a chain are repeated observations, not
    independent samples, so the generation column must survive into any file an
    analyst opens — a wide format that silently averages generations away is how
    that mistake gets made.

``policy_summary.csv``
    One row per policy: chain count and mean regret AUC. Convenience only;
    uncertainty is computed across chains by the analysis module, not here.

Every input is validated against ``schemas/chain_result.schema.json`` before it
contributes a row. Invalid inputs are refused rather than silently skipped.

Usage
-----
    python scripts/export_csv.py results/runs/*/chain_result.json --output-dir results/csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

from human_data_budget.analysis.metrics import mean, regret_auc
from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "chain_result.schema.json"

LONG_COLUMNS = [
    "run_id",
    "policy",
    "chain_seed",
    "budget_id",
    "generation",
    "human_nll",
    "tail_retention",
    "generations_completed",
    "consumed_human_tokens",
    "consumed_total_tokens",
    "valid",
    "exclusion_reason",
]

SUMMARY_COLUMNS = ["policy", "chain_count", "mean_nll_regret_auc"]


def load_results(paths: list[Path]) -> list[dict]:
    """Read and schema-validate every chain result."""
    documents = []
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        validate_json(document, SCHEMA)
        documents.append(document)
    return documents


def write_long(documents: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LONG_COLUMNS)
        writer.writeheader()
        for document in sorted(documents, key=lambda d: (d["policy"], d["chain_seed"])):
            for metric in document["metrics"]:
                writer.writerow(
                    {
                        "run_id": document["run_id"],
                        "policy": document["policy"],
                        "chain_seed": document["chain_seed"],
                        "budget_id": document["budget_id"],
                        "generation": metric["generation"],
                        "human_nll": metric["human_nll"],
                        "tail_retention": metric["tail_retention"],
                        "generations_completed": document["generations_completed"],
                        "consumed_human_tokens": document["consumed_human_tokens"],
                        "consumed_total_tokens": document["consumed_total_tokens"],
                        "valid": document["valid"],
                        "exclusion_reason": document["exclusion_reason"] or "",
                    }
                )


def write_summary(documents: list[dict], path: Path) -> None:
    by_policy: dict[str, list[float]] = {}
    for document in documents:
        if not document["valid"]:
            continue  # excluded chains contribute to the long file, never to a summary
        auc = regret_auc([metric["human_nll"] for metric in document["metrics"]])
        by_policy.setdefault(document["policy"], []).append(auc)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for policy, values in sorted(by_policy.items()):
            writer.writerow(
                {
                    "policy": policy,
                    "chain_count": len(values),
                    "mean_nll_regret_auc": f"{mean(values):.6f}",
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "csv")
    args = parser.parse_args(argv)

    documents = load_results(args.inputs)
    if not documents:
        print("no chain results supplied", file=sys.stderr)
        return 1

    long_path = args.output_dir / "chain_level_long.csv"
    summary_path = args.output_dir / "policy_summary.csv"
    write_long(documents, long_path)
    write_summary(documents, summary_path)

    for path in (long_path, summary_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{digest}  {path.relative_to(ROOT)}")
    print(f"exported {len(documents)} chain result(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
