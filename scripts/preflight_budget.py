#!/usr/bin/env python3
"""Preflight budget-equality check, run before any chain launches.

Implements the `docs/weekly/WEEK_3.md` Aarav clause "Verify preflight budget
equality for each chain."

`PROTOCOL.md` §4 makes budget matching the fairness constraint: every policy in a
comparison must consume exactly the same lifetime human-origin optimizer tokens
and the same total optimizer tokens. `scripts/validate_run.py` checks that
*after* a run, from the emitted artifacts. By then the compute is already spent.
This script checks the same property *before* launch, from configuration alone,
so a misconfigured comparison fails in a second rather than after hours on an
accelerator.

Three classes of check:

1. **Internal consistency** — a single config's own numbers must agree
   (per-generation budget times horizon equals the lifetime budget, human tokens
   do not exceed total tokens, candidate supply can actually fund the budget).
2. **Cross-config equality** — every config presented together must declare the
   same lifetime human budget and the same total optimizer budget.
3. **Unfrozen placeholders** — a config still carrying `TBD` cannot be launched.

Exit codes: 0 all checks pass, 1 at least one failure.

Usage
-----
    python scripts/preflight_budget.py configs/experiment/*.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLACEHOLDER_MARKERS = ("TBD", "PENDING", "RESULT_PENDING")


def _is_placeholder(value: object) -> bool:
    return isinstance(value, str) and any(
        marker in value.upper() for marker in PLACEHOLDER_MARKERS
    )


def check_internal(config: dict, path: Path) -> list[str]:
    """Verify one experiment config is internally coherent."""
    failures: list[str] = []

    lifetime = config.get("lifetime_human_budget")
    per_generation = config.get("per_generation_human_budget")
    horizon = config.get("horizon")
    total = config.get("total_optimizer_tokens")

    for name, value in (
        ("lifetime_human_budget", lifetime),
        ("per_generation_human_budget", per_generation),
        ("horizon", horizon),
        ("total_optimizer_tokens", total),
    ):
        if value is None:
            failures.append(f"{path.name}: missing required field {name!r}")
        elif _is_placeholder(value):
            failures.append(
                f"{path.name}: {name} is still a placeholder ({value!r}); "
                "freeze it before launching"
            )

    if failures:
        return failures

    if not isinstance(horizon, int) or horizon < 1:
        failures.append(f"{path.name}: horizon must be a positive integer, got {horizon!r}")
        return failures

    if per_generation * horizon != lifetime:
        failures.append(
            f"{path.name}: per_generation_human_budget ({per_generation}) x horizon "
            f"({horizon}) = {per_generation * horizon}, which does not equal "
            f"lifetime_human_budget ({lifetime})"
        )

    if lifetime > total:
        failures.append(
            f"{path.name}: lifetime_human_budget ({lifetime}) exceeds "
            f"total_optimizer_tokens ({total}); human tokens are a subset of total"
        )

    # A policy cannot spend a budget the candidate pool cannot supply.
    candidates = config.get("candidates") or []
    if candidates:
        supply = sum(int(candidate.get("human_token_count", 0)) for candidate in candidates)
        if supply < per_generation:
            failures.append(
                f"{path.name}: candidate pool supplies {supply} human tokens per "
                f"generation but the per-generation budget is {per_generation}; "
                "the budget is unspendable and policies will silently underspend"
            )

        modes = {candidate.get("mode") for candidate in candidates}
        if len(modes) < 2:
            failures.append(
                f"{path.name}: candidate pool spans {len(modes)} mode(s) {sorted(modes)}; "
                "mode allocation cannot be exercised with fewer than two modes"
            )

    return failures


def check_cross_config(configs: dict[Path, dict]) -> list[str]:
    """Verify every config in the comparison declares identical budgets."""
    if len(configs) < 2:
        return []

    failures: list[str] = []
    human = {path.name: config.get("lifetime_human_budget") for path, config in configs.items()}
    total = {path.name: config.get("total_optimizer_tokens") for path, config in configs.items()}

    if len(set(human.values())) != 1:
        failures.append(f"lifetime human-token budgets differ across configs: {human}")
    if len(set(total.values())) != 1:
        failures.append(f"total optimizer-token budgets differ across configs: {total}")

    horizons = {path.name: config.get("horizon") for path, config in configs.items()}
    if len(set(horizons.values())) != 1:
        failures.append(f"horizons differ across configs: {horizons}")

    policies = [config.get("policy") for config in configs.values()]
    if len(set(policies)) != len(policies):
        failures.append(f"duplicate policies in the comparison set: {policies}")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("config", nargs="+", type=Path)
    parser.add_argument(
        "--compare",
        action="store_true",
        help="also require every config to declare identical budgets (use for one comparison set)",
    )
    args = parser.parse_args(argv)

    loaded: dict[Path, dict] = {}
    failures: list[str] = []

    for path in args.config:
        try:
            loaded[path] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{path}: unreadable ({exc})")

    for path, config in loaded.items():
        failures.extend(check_internal(config, path))

    if args.compare:
        failures.extend(check_cross_config(loaded))

    if failures:
        print(f"PREFLIGHT FAILED ({len(failures)} problem(s)):")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    scope = "and matched across the set " if args.compare else ""
    print(f"PREFLIGHT PASSED: {len(loaded)} config(s) internally consistent {scope}".strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
