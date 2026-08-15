#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def escape(value: str) -> str:
    return value.replace("_", "\\_")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("--output", type=Path, default=Path("paper/tables/primary_results.tex"))
    args = parser.parse_args()
    data = json.loads(args.aggregate.read_text(encoding="utf-8"))

    # Provenance gate. This script's --output defaults to the manuscript's result
    # table, so it is the last thing standing between a simulated number and the
    # paper. scripts/generate_fixture_tables.py stamps these fields on every
    # aggregate it produces; refuse them here rather than trusting the caller to
    # pass the right file (PROTOCOL.md §5, no-result rule).
    if data.get("fixture_only") or data.get("scientific_evidence") is False:
        raise SystemExit(
            f"refusing to typeset {args.aggregate}: it is marked fixture output.\n"
            "Fixture tables belong in results/tables/ via "
            "scripts/generate_fixture_tables.py, never in paper/tables/."
        )

    lines = [
        "% AUTO-GENERATED. DO NOT EDIT EXPERIMENTAL VALUES MANUALLY.",
        "\\begin{tabular}{lrr}",
        "Policy & Chains & Mean NLL AUC \\\\",
        "\\hline",
    ]
    for policy, values in data.get("policies", {}).items():
        lines.append(
            f"{escape(policy)} & {values['chain_count']} & {values['mean_nll_auc']:.4f} \\\\"
        )
    if not data.get("policies"):
        lines.append("RESULT\\_PENDING & 0 & -- \\\\")
    lines.extend(["\\end{tabular}", ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
