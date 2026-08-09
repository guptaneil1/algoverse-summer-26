#!/usr/bin/env python3
"""Score promptlab results. Reports pass rates with intervals, per-task
breakdown, paired variant comparisons, and the ranked failure taxonomy.

Usage:
    python promptlab/score.py
    python promptlab/score.py --baseline baseline
    python promptlab/score.py --failures          # what actually went wrong

The paired comparison is the part that matters. Two variants run on the same
tasks are paired data; comparing their marginal pass rates throws away that
pairing and costs you most of your power on an eval this small.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

LAB = Path(__file__).resolve().parent


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Normal approximation is wrong at these n and
    degenerate at 0/n and n/n, which is exactly where prompt evals live."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (centre - half) / d), min(1.0, (centre + half) / d))


def load(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"no results at {path} — run run.py first")
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def bar(lo: float, hi: float, width: int = 24) -> str:
    a, b = int(lo * width), max(int(hi * width), int(lo * width) + 1)
    return "".join("=" if a <= i < b else " " for i in range(width))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(LAB / "results" / "results.jsonl"))
    ap.add_argument("--baseline", default="baseline")
    ap.add_argument("--failures", action="store_true")
    args = ap.parse_args()

    rows = [r for r in load(Path(args.results)) if r.get("passed") is not None]
    if not rows:
        raise SystemExit("no graded rows (dry-run only?)")

    variants = sorted({r["variant"] for r in rows})
    tasks = sorted({r["task"] for r in rows})

    # ---- overall ---------------------------------------------------------- #
    print("\nOVERALL PASS RATE  (95% Wilson interval)\n")
    overall = {}
    for v in variants:
        rs = [r for r in rows if r["variant"] == v]
        k, n = sum(r["passed"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        overall[v] = (k, n, lo, hi)
        cost = sum(r.get("cost_usd") or 0 for r in rs)
        print(f"  {v:<24} {k:>3}/{n:<3} {k/n:>5.0%}  [{lo:.0%}-{hi:.0%}] "
              f"|{bar(lo, hi)}|  ${cost:.2f}")

    # ---- per task --------------------------------------------------------- #
    print("\nPER TASK\n")
    w = max(len(t) for t in tasks) + 2
    print("  " + "task".ljust(w) + "".join(v[:14].ljust(16) for v in variants))
    for t in tasks:
        line = "  " + t.ljust(w)
        for v in variants:
            rs = [r for r in rows if r["variant"] == v and r["task"] == t]
            line += (f"{sum(r['passed'] for r in rs)}/{len(rs)}".ljust(16)
                     if rs else "-".ljust(16))
        print(line)

    # ---- paired ----------------------------------------------------------- #
    if args.baseline in variants and len(variants) > 1:
        print(f"\nPAIRED vs '{args.baseline}'  (per-task pass-count delta)\n")
        for v in variants:
            if v == args.baseline:
                continue
            wins = losses = ties = 0
            deltas = []
            for t in tasks:
                b = [r for r in rows if r["variant"] == args.baseline and r["task"] == t]
                c = [r for r in rows if r["variant"] == v and r["task"] == t]
                if not b or not c:
                    continue
                d = sum(x["passed"] for x in c) / len(c) - \
                    sum(x["passed"] for x in b) / len(b)
                deltas.append(d)
                wins += d > 0
                losses += d < 0
                ties += d == 0
            if not deltas:
                continue
            mean = sum(deltas) / len(deltas)
            print(f"  {v:<24} mean {mean:+.0%}   "
                  f"better on {wins}, worse on {losses}, same on {ties}")

            kb, nb, lob, hib = overall[args.baseline]
            kv, nv, lov, hiv = overall[v]
            if lov <= hib and lob <= hiv:
                print(f"    {'':<22} NOT DISTINGUISHABLE — intervals overlap. "
                      f"Do not claim this variant is better.")
            elif lov > hib:
                print(f"    {'':<22} separated from baseline at this n.")

    # ---- failures --------------------------------------------------------- #
    print("\nFAILURE TAXONOMY  (every prompt line should trace to one of these)\n")
    counts: Counter[tuple[str, str]] = Counter()
    for r in rows:
        for c in r.get("checks", []):
            if not c["passed"]:
                counts[(r["variant"], c.get("message") or c["type"])] += 1
    if not counts:
        print("  no failures recorded")
    else:
        by_variant: dict[str, list] = defaultdict(list)
        for (v, msg), n in counts.items():
            by_variant[v].append((n, msg))
        for v in sorted(by_variant):
            print(f"  {v}")
            for n, msg in sorted(by_variant[v], reverse=True):
                print(f"     {n:>3}x  {msg}")

    if args.failures:
        print("\nFAILING TRANSCRIPTS\n")
        for r in rows:
            if r["passed"]:
                continue
            bad = [c.get("message") for c in r.get("checks", []) if not c["passed"]]
            print(f"--- {r['variant']} / {r['task']} / rep {r['rep']}")
            print(f"    {bad}")
            print("    " + (r.get("text", "")[:400].replace("\n", "\n    ")))
            print()

    n_per_cell = len(rows) / max(len(variants) * len(tasks), 1)
    print(f"\nPOWER NOTE: {len(tasks)} tasks x ~{n_per_cell:.0f} reps. At this "
          f"size only large differences are detectable.\nA variant that wins by "
          f"one or two cells is noise. Prefer deleting lines that do not hurt\n"
          f"over adding lines that seem to help.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
