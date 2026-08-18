"""Realised budget-matching check, applied to chains that have already run.

`scripts/preflight_budget.py` checks *declared* budgets before launch, from
configuration alone. This module checks *realised* lifetime human-origin spend
afterwards, from what the chains actually consumed. They are different properties,
and the gap between them is FAILURE_LOG.md F-015: a comparison can declare
identical budgets and still spend unequally, because policies stop when the next
indivisible candidate does not fit the remaining allowance.

F-015 recorded a 24% spread from that mechanism and was closed by pricing the
ledger in optimizer tokens and reconciling terminal allocations one generation
earlier. What survives the fix is a floor rather than a defect: over indivisible
examples no policy can land exactly on its ceiling, so the residual is bounded by
the largest single candidate the arm might have been offered next.

The check therefore asserts that bound rather than exact equality. Exact equality
was the original guard in `scripts/run_pilot.py`, and it was unsatisfiable for any
configuration that included a control arm -- the control's structural zero always
differed from the spending arms -- which is why it fired on a grid whose spread was
0.04%. Decision P-008 records the re-specification; it is F-015's option 2.

Three conditions, all required:

1. No arm exceeds its lifetime ceiling. Overspend is a hard error, never rounding.
2. Every *spending* arm lands within one indivisible candidate of the ceiling. This
   is the condition that catches F-015: schedule_only fell roughly 233,000 short
   against a largest candidate of 26,902, which indivisibility cannot explain.
3. Relative spread across spending arms stays an order of magnitude below the
   practical effect threshold, so a difference in how much human data an arm
   received cannot masquerade as the effect the study means to measure.

Arms whose policy spends nothing by construction are excluded from 2 and 3 and
asserted to be exactly zero instead. That zero is the comparison's reference point,
not a shortfall.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Condition 3's margin: realised spread must sit at least this far below the
#: configured practical effect threshold. One order of magnitude is a judgement,
#: not a derivation -- see P-008 for the reasoning and its reversal condition. At
#: the pilot's 2% threshold this permits 0.2%, against a measured 0.04%.
SPREAD_MARGIN_BELOW_THRESHOLD = 0.1


@dataclass(frozen=True)
class BudgetMatchingReport:
    """Verdict of the realised budget-matching check."""

    ok: bool
    failures: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    spending_spread_relative: float | None = None

    def render(self) -> str:
        """Format the verdict for a launcher's stdout."""
        lines: list[str] = []
        if self.ok:
            lines.append("budget matching: HOLDS")
        else:
            lines.append("!! BUDGET MATCHING VIOLATED")
        lines.extend(f"   {line}" for line in self.observations)
        for failure in self.failures:
            lines.append(f"   FAIL {failure}")
        if not self.ok:
            lines.append("   PROTOCOL.md section 4 makes equal spend the fairness "
                         "constraint;")
            lines.append("   this comparison is invalid until the cause is found.")
        return "\n".join(lines)


def max_candidate_optimizer_tokens(manifest_path: str | Path) -> int:
    """Return the largest single candidate's optimizer-token cost.

    This is the indivisibility bound: a policy stops when the next candidate does
    not fit, and that candidate may be the largest in the pool, so a shortfall up to
    this size is explained by indivisibility alone. Reading it from the frozen
    rescue-candidate manifest keeps the bound traceable to a hash-pinned artifact
    rather than to a constant somebody would have to maintain by hand.
    """
    path = Path(manifest_path)
    largest = 0
    found = False
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            cost = record.get("optimizer_token_count")
            if cost is None:
                continue
            found = True
            largest = max(largest, int(cost))
    if not found:
        raise ValueError(
            f"{path}: no record carries optimizer_token_count, so the indivisibility "
            "bound cannot be derived. FAILURE_LOG.md F-010b: a manifest that counts "
            "words instead of tokens produces a bound in the wrong currency."
        )
    return largest


def check_realised_budget_matching(
    chains: Iterable[dict[str, Any]],
    *,
    lifetime_human_budget: int,
    indivisibility_bound: int,
    practical_effect_threshold_relative: float,
    is_spending_arm,
) -> BudgetMatchingReport:
    """Assert realised spend across completed chains.

    ``chains`` are per-chain summaries carrying ``arm``, ``seed`` and
    ``consumed_human_tokens``. ``is_spending_arm`` maps an arm name to whether its
    policy can spend at all; chains from non-spending arms are held to an exact zero
    instead of to the ceiling.
    """
    failures: list[str] = []
    observations: list[str] = []

    considered = [
        chain for chain in chains
        if chain.get("consumed_human_tokens") is not None
    ]
    if not considered:
        return BudgetMatchingReport(
            ok=False,
            failures=["no completed chain reported consumed_human_tokens"],
        )

    spending: list[dict[str, Any]] = []
    for chain in considered:
        arm = chain["arm"]
        spent = chain["consumed_human_tokens"]

        if spent > lifetime_human_budget:
            failures.append(
                f"{arm} seed {chain['seed']} consumed {spent:,}, over the "
                f"{lifetime_human_budget:,} lifetime ceiling"
            )
            continue

        if is_spending_arm(arm):
            spending.append(chain)
            shortfall = lifetime_human_budget - spent
            if shortfall > indivisibility_bound:
                failures.append(
                    f"{arm} seed {chain['seed']} consumed {spent:,}, falling "
                    f"{shortfall:,} short of the {lifetime_human_budget:,} ceiling. "
                    f"One indivisible candidate is at most {indivisibility_bound:,}, "
                    "so indivisibility does not explain this"
                )
        elif spent != 0:
            failures.append(
                f"{arm} spends nothing by construction, but seed {chain['seed']} "
                f"consumed {spent:,}"
            )

    spread_relative: float | None = None
    if spending:
        spends = [chain["consumed_human_tokens"] for chain in spending]
        low, high = min(spends), max(spends)
        spread_relative = (high - low) / high if high else 0.0
        permitted = practical_effect_threshold_relative * SPREAD_MARGIN_BELOW_THRESHOLD
        observations.append(
            f"spending arms: {low:,} to {high:,} against a "
            f"{lifetime_human_budget:,} ceiling "
            f"({spread_relative * 100:.4f}% spread, {permitted * 100:.4f}% permitted)"
        )
        if spread_relative > permitted:
            failures.append(
                f"realised spread across spending arms is {spread_relative * 100:.4f}%, "
                f"above the {permitted * 100:.4f}% permitted "
                f"({SPREAD_MARGIN_BELOW_THRESHOLD:g} of the "
                f"{practical_effect_threshold_relative * 100:g}% practical effect "
                "threshold). A spend difference this large is not separable from the "
                "effect being measured"
            )

    non_spending = [chain for chain in considered if not is_spending_arm(chain["arm"])]
    if non_spending:
        observations.append(
            f"control arms held to an exact zero: "
            f"{len({chain['arm'] for chain in non_spending})} arm(s), "
            f"{len(non_spending)} chain(s)"
        )

    return BudgetMatchingReport(
        ok=not failures,
        failures=failures,
        observations=observations,
        spending_spread_relative=spread_relative,
    )
