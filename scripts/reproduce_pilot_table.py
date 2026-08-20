#!/usr/bin/env python3
"""Independently recompute every headline number from the chain artifacts.

`docs/SUBMISSION_CHECKLIST.md` requires the headline table to be reproduced by someone
who did not write the analysis, and the primary metrics to be independently recomputed
from frozen outputs. This script exists so that person does not have to reverse-engineer
the analysis first: it reads only `chain_result.json` files, recomputes every published
quantity from scratch, and compares against what the repository claims.

It deliberately shares no code with `scripts/generate_pilot_outputs.py`. The arithmetic
is rewritten here rather than imported, so a defect in the generator cannot hide by being
reused -- an independent check that calls the thing it is checking is not independent.

Usage:
    python scripts/reproduce_pilot_table.py
    python scripts/reproduce_pilot_table.py --run-dir results/runs/primary_pilot_2026-08-18

Exit codes: 0 everything matches, 1 at least one published value could not be reproduced.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

LIFETIME_BUDGET = 750_000
THRESHOLD_RELATIVE = 0.02
ARMS = ("no_rescue", "random", "schedule_only", "selection_only", "joint")

#: What the repository publishes, transcribed from the documents under audit, keyed by
#: run directory. If a value below disagrees with a recomputation, one of the two is wrong
#: and this script says so.
#:
#: Both runs stay checkable. The 2026-08-18 grid is superseded but its numbers are cited
#: in FAILURE_LOG.md F-020 and F-021 and in the paper's account of why it was rejected, so
#: an audit that could no longer verify them would be an audit with a hole in it.
PUBLISHED_BY_RUN = {
    "primary_pilot_v2_2026-08-20": {
        "auc_regret": {
            "no_rescue": 2.64314, "random": 2.53644, "schedule_only": 2.52612,
            "selection_only": 2.29314, "joint": 2.30340,
        },
        "auc_sd": {
            "no_rescue": 0.01401, "random": 0.00801, "schedule_only": 0.01939,
            "selection_only": 0.02502, "joint": 0.02207,
        },
        "human_spend": {
            "no_rescue": 0, "random": 749_869, "schedule_only": 749_878,
            "selection_only": 749_827, "joint": 749_827,
        },
        "total_tokens": {
            "no_rescue": 16_678_912, "random": 16_678_912, "schedule_only": 16_678_912,
            "selection_only": 16_678_912, "joint": 16_678_912,
        },
        "total_spread_percent": 0.00,
        "joint_shortfall_percent": 0.0,
    },
    "primary_pilot_2026-08-18": {
        "auc_regret": {
            "no_rescue": 2.63738, "random": 2.52454, "schedule_only": 2.54581,
            "selection_only": 2.31320, "joint": 2.32163,
        },
        "auc_sd": {
            "no_rescue": 0.01760, "random": 0.02055, "schedule_only": 0.02757,
            "selection_only": 0.01126, "joint": 0.00949,
        },
        "human_spend": {
            "no_rescue": 0, "random": 749_869, "schedule_only": 749_878,
            "selection_only": 749_827, "joint": 674_193,
        },
        "total_tokens": {
            "no_rescue": 16_678_912, "random": 16_777_421, "schedule_only": 16_773_427,
            "selection_only": 17_063_936, "joint": 17_025_024,
        },
        "total_spread_percent": 2.26,
        "joint_shortfall_percent": 10.1,
    },
}


def mean(values):
    values = list(values)
    return sum(values) / len(values)


def stdev(values):
    values = list(values)
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def auc_regret(metrics: list[dict]) -> float:
    """Area under the generation-wise NLL-regret curve, by trapezoid.

    Written out longhand rather than imported: regret against the chain's own
    generation-0 value, trapezoid rule over consecutive generations.
    """
    series = [m["human_nll"] for m in sorted(metrics, key=lambda m: m["generation"])]
    base = series[0]
    regret = [value - base for value in series]
    total = 0.0
    for index in range(len(regret) - 1):
        total += (regret[index] + regret[index + 1]) / 2.0
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path,
                        default=Path("results/runs/primary_pilot_v2_2026-08-20"))
    parser.add_argument("--tolerance", type=float, default=5e-5,
                        help="absolute tolerance for AUC comparisons")
    args = parser.parse_args()

    name = args.run_dir.name
    if name not in PUBLISHED_BY_RUN:
        print(f"no published values transcribed for {name}. Known runs: "
              f"{sorted(PUBLISHED_BY_RUN)}")
        return 1
    published = PUBLISHED_BY_RUN[name]

    chains: dict[str, list[dict]] = {}
    for path in sorted(args.run_dir.rglob("chain_result.json")):
        chain = json.loads(path.read_text(encoding="utf-8"))
        chains.setdefault(chain["policy"], []).append(chain)

    if not chains:
        print(f"no chain_result.json found under {args.run_dir}")
        return 1

    failures: list[str] = []
    print(f"recomputed from {sum(len(v) for v in chains.values())} chain artifacts "
          f"under {args.run_dir}\n")
    print(f"{'arm':16s} {'AUC regret':>12s} {'SD':>10s} {'human':>10s} {'total':>12s}")
    print("-" * 66)

    for arm in ARMS:
        found = chains.get(arm)
        if not found:
            failures.append(f"{arm}: no chains found")
            continue
        if len(found) != 5:
            failures.append(f"{arm}: expected 5 chains, found {len(found)}")

        areas = [auc_regret(c["metrics"]) for c in found]
        got = {
            "auc_regret": mean(areas),
            "auc_sd": stdev(areas),
            "human_spend": mean(c["consumed_human_tokens"] for c in found),
            "total_tokens": mean(c["consumed_total_tokens"] for c in found),
        }
        print(f"{arm:16s} {got['auc_regret']:12.5f} {got['auc_sd']:10.5f} "
              f"{got['human_spend']:10,.0f} {got['total_tokens']:12,.0f}")

        for key, tolerance in (("auc_regret", args.tolerance), ("auc_sd", args.tolerance),
                               ("human_spend", 0.5), ("total_tokens", 0.5)):
            want = published[key][arm]
            if abs(got[key] - want) > tolerance:
                failures.append(
                    f"{arm}.{key}: recomputed {got[key]:,.5f}, published {want:,.5f}"
                )

    totals = [mean(c["consumed_total_tokens"] for c in chains[a]) for a in ARMS if a in chains]
    spread = 100 * (max(totals) - min(totals)) / max(totals)
    shortfall = 100 * (LIFETIME_BUDGET - mean(
        c["consumed_human_tokens"] for c in chains["joint"])) / LIFETIME_BUDGET

    print()
    print(f"cross-arm total-token spread : {spread:.2f}%  "
          f"(published {published['total_spread_percent']}%)")
    print(f"joint human shortfall        : {shortfall:.1f}%  "
          f"(published {published['joint_shortfall_percent']}%)")
    print(f"practical effect threshold   : {THRESHOLD_RELATIVE * 100:g}%")

    if abs(spread - published["total_spread_percent"]) > 0.01:
        failures.append(f"total spread: recomputed {spread:.2f}%, "
                        f"published {published['total_spread_percent']}%")
    if abs(shortfall - published["joint_shortfall_percent"]) > 0.05:
        failures.append(f"joint shortfall: recomputed {shortfall:.1f}%, "
                        f"published {published['joint_shortfall_percent']}%")

    print()
    if failures:
        print(f"{len(failures)} value(s) did NOT reproduce:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("every published value reproduced from the artifacts.")
    print()
    print("Note what this does and does not establish. It confirms the numbers in the")
    print("paper follow from the chain results. It is silent on whether the run was")
    print("valid, which the budget guard and scripts/validate_run.py answer, not")
    print("arithmetic.")
    print()
    # Read from the measured spreads rather than written as a constant, so this text
    # cannot go on describing the run it was first written for.
    if spread <= 0.2 and shortfall <= 0.2:
        print(f"For {name}, both budget axes hold in these artifacts: cross-arm total")
        print(f"spread {spread:.2f}% and joint shortfall {shortfall:.1f}%, each inside the")
        print("0.2% the guard permits. The primary contrast is admissible, and it is")
        print("reported as a null.")
    else:
        print(f"For {name}, at least one budget axis fails in these artifacts: cross-arm")
        print(f"total spread {spread:.2f}%, joint shortfall {shortfall:.1f}%, against 0.2%")
        print("permitted. FAILURE_LOG.md F-020 and F-021 record why, and the primary")
        print("contrast is reported as not established.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
