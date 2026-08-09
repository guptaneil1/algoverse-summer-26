#!/usr/bin/env python3
"""Build one chain-level aggregate from immutable chain_result.json files.

One row per completed chain. Generations inside a chain are repeated
observations, never independent samples, so every summary here is computed
across chains.

    python scripts/aggregate_chain_results.py runs/*/chain_result.json \\
        --output results/aggregates/provisional_week3.json

Every input path, run ID, and SHA-256 is recorded so the aggregate can be
regenerated exactly. No value is ever entered by hand.

Exit codes: 0 written, 2 rejected input, 3 usage error.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from human_data_budget.analysis.metrics import mean, regret_auc
from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[1]
CHAIN_RESULT_SCHEMA = ROOT / "schemas/chain_result.schema.json"
ANALYSIS_VERSION = "1.0"
ELIGIBLE_CLASSIFICATIONS = {"valid", "valid_with_limitation"}


class RejectedInput(Exception):
    """Raised when an input cannot enter the aggregate."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_chain_result(path: Path) -> dict[str, Any]:
    """Load and schema-validate one chain result."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RejectedInput(f"{path}: not valid JSON ({error})") from error
    try:
        validate_json(payload, CHAIN_RESULT_SCHEMA)
    except Exception as error:  # noqa: BLE001 - surfaced as a rejection
        raise RejectedInput(f"{path}: schema invalid ({error})") from error
    return payload


def load_classifications(path: Path) -> dict[str, str]:
    """Read Neil's classification index as ``run_id -> classification``."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    missing = [r for r in rows if not r.get("run_id") or not r.get("classification")]
    if missing:
        raise RejectedInput(f"{path}: rows missing run_id or classification")
    return {row["run_id"]: row["classification"] for row in rows}


def nll_auc(chain_result: dict[str, Any]) -> float:
    """Trapezoidal area under the held-out NLL curve for one chain."""
    ordered = sorted(chain_result["metrics"], key=lambda entry: entry["generation"])
    if len(ordered) < 2:
        raise RejectedInput(
            f"{chain_result['run_id']}: a curve summary needs at least two generations, "
            f"found {len(ordered)}"
        )
    return regret_auc([float(entry["human_nll"]) for entry in ordered])


def final_tail_retention(chain_result: dict[str, Any]) -> float:
    ordered = sorted(chain_result["metrics"], key=lambda entry: entry["generation"])
    return float(ordered[-1]["tail_retention"])


def aggregate(
    paths: list[Path],
    *,
    classifications: dict[str, str] | None = None,
    label: str = "provisional",
) -> dict[str, Any]:
    """Aggregate chain results into one row per chain, grouped by policy."""
    if not paths:
        raise RejectedInput("no chain results supplied")

    inputs: list[dict[str, Any]] = []
    included: list[dict[str, Any]] = []
    seen_run_ids: dict[str, Path] = {}
    budget_ids: set[str] = set()

    for path in paths:
        chain_result = load_chain_result(path)
        run_id = chain_result["run_id"]

        if run_id in seen_run_ids:
            raise RejectedInput(
                f"duplicate run_id {run_id!r} in {path} and {seen_run_ids[run_id]}"
            )
        seen_run_ids[run_id] = path
        budget_ids.add(chain_result["budget_id"])

        classification = (classifications or {}).get(run_id)
        if classification is not None:
            eligible = classification in ELIGIBLE_CLASSIFICATIONS
            reason = None if eligible else f"classified {classification}"
        else:
            eligible = bool(chain_result["valid"])
            reason = None if eligible else (chain_result.get("exclusion_reason") or "valid=false")

        record = {
            "run_id": run_id,
            "path": str(path),
            "sha256": sha256_file(path),
            "policy": chain_result["policy"],
            "chain_seed": chain_result["chain_seed"],
            "budget_id": chain_result["budget_id"],
            "classification": classification,
            "included": eligible,
            "exclusion_reason": reason,
        }
        inputs.append(record)
        if eligible:
            included.append(chain_result)

    if len(budget_ids) != 1:
        raise RejectedInput(f"chains span multiple budget ids: {sorted(budget_ids)}")

    policies: dict[str, Any] = {}
    for chain_result in included:
        policies.setdefault(chain_result["policy"], []).append(chain_result)

    summary = {}
    for policy, chains in sorted(policies.items()):
        summary[policy] = {
            "chain_count": len(chains),
            "chain_seeds": sorted(chain["chain_seed"] for chain in chains),
            "mean_nll_auc": mean([nll_auc(chain) for chain in chains]),
            "mean_final_tail_retention": mean([final_tail_retention(chain) for chain in chains]),
        }

    return {
        "schema_version": "1.0",
        "analysis_version": ANALYSIS_VERSION,
        "label": label,
        "generated_by": "scripts/aggregate_chain_results.py",
        "unit_of_analysis": "one independently seeded recursive chain",
        "budget_id": next(iter(budget_ids)),
        "chains_supplied": len(inputs),
        "chains_included": len(included),
        "chains_excluded": len(inputs) - len(included),
        "inputs": sorted(inputs, key=lambda record: record["run_id"]),
        "policies": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chain_results", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--classifications",
        type=Path,
        help="Neil's classification CSV; without it the chain's own valid flag is used",
    )
    parser.add_argument(
        "--label",
        default="provisional",
        choices=["provisional", "frozen"],
        help="frozen is only correct after the results freeze",
    )
    args = parser.parse_args()

    try:
        classifications = (
            load_classifications(args.classifications) if args.classifications else None
        )
        payload = aggregate(
            args.chain_results, classifications=classifications, label=args.label
        )
    except RejectedInput as error:
        print(f"REJECTED: {error}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"wrote {args.output} "
        f"({payload['chains_included']} included, {payload['chains_excluded']} excluded)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
