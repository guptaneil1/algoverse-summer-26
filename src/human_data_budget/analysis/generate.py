"""Generate a small aggregate from schema-valid chain-result JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_data_budget.analysis.metrics import mean, regret_auc


def aggregate(paths: list[Path]) -> dict[str, object]:
    by_policy: dict[str, list[float]] = {}
    for path in paths:
        result = json.loads(path.read_text(encoding="utf-8"))
        if not result["valid"]:
            continue
        regrets = [metric["human_nll"] for metric in result["metrics"]]
        by_policy.setdefault(result["policy"], []).append(regret_auc(regrets))
    return {
        "schema_version": "1.0",
        "policies": {
            policy: {"chain_count": len(values), "mean_nll_auc": mean(values)}
            for policy, values in sorted(by_policy.items())
        },
        "warning": "NLL AUC is a fixture aggregate until a frozen regret reference is implemented.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(aggregate(args.inputs), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
