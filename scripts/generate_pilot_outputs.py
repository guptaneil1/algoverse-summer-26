#!/usr/bin/env python3
"""Generate the pilot's results table and figure from immutable chain artifacts.

Everything this writes is derived from ``chain_result.json`` files and nothing else,
so a reader with the repository can regenerate byte-identical output and check it.
No value is typed by hand, which is the same contract
``scripts/generate_method_tables.py`` holds for the positive control.

Two outputs:

* ``paper/tables/primary_results.tex`` -- per-arm chain counts, realised human spend,
  the primary outcome and its between-chain spread. It replaces a placeholder that
  reads ``RESULT_PENDING``.
* ``results/figures/pilot_nll_by_generation.png`` -- held-out human NLL against
  generation, one line per arm, five seeds each.

**Whether the primary contrast may be computed is decided from the artifacts, not
asserted here.** ``PROTOCOL.md`` §4 requires matched lifetime human-origin tokens *and*
matched total optimizer tokens; ``budget_axes`` measures both from the chains and
``primary_contrast_is_admissible`` gates the comparison on them. For
``primary_pilot_2026-08-18`` both axes fail (``FAILURE_LOG.md`` F-020, F-021) and the
table emits descriptives with `joint` marked. For ``primary_pilot_v2_2026-08-20`` both
hold and the preregistered contrast is emitted.

This used to be a hardcoded refusal that named F-020. That was right for the run in
front of it and would have been silently wrong for the next one -- the same shape as
F-016, F-018, F-020 and F-024, where documented intent and implementation diverged with
nothing asserting they agree. The gate now reads the run.

Usage:
    python scripts/generate_pilot_outputs.py \\
        --run-dir results/runs/primary_pilot_v2_2026-08-20
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from human_data_budget.runner.budget_matching import (  # noqa: E402
    SPREAD_MARGIN_BELOW_THRESHOLD,
)

# Presentation order: control first, then increasing sophistication. Matches the
# treatment-family ordering in paper/sections/05_method.tex.
ARM_ORDER = ("no_rescue", "random", "schedule_only", "selection_only", "joint")

#: U-006, frozen 2026-08-19 at 2% relative and unchangeable now that primary outcomes
#: are open (docs/decisions/effect_threshold_review_2026-08-19.md).
THRESHOLD_RELATIVE = 0.02

ARM_LABEL = {
    "no_rescue": "No rescue (control)",
    "random": "Fresh random",
    "schedule_only": "Schedule-only",
    "selection_only": "Selection-only",
    "joint": "Joint time-and-mode",
}

LIFETIME_BUDGET = 750_000


def load_chains(run_dir: Path) -> dict[str, list[dict]]:
    """Read every chain result under ``run_dir``, keyed by arm."""
    by_arm: dict[str, list[dict]] = {}
    for path in sorted(run_dir.rglob("chain_result.json")):
        chain = json.loads(path.read_text(encoding="utf-8"))
        by_arm.setdefault(chain["policy"], []).append(chain)
    if not by_arm:
        raise SystemExit(f"no chain_result.json found under {run_dir}")
    return by_arm


def nll_series(chain: dict) -> list[float]:
    return [m["human_nll"] for m in sorted(chain["metrics"], key=lambda m: m["generation"])]


def auc_regret(chain: dict) -> float:
    """Area under the generation-wise NLL-regret curve, by trapezoid.

    Regret is measured against the chain's own generation-0 value, so the quantity is
    within-chain and does not depend on any cross-arm baseline.
    """
    series = nll_series(chain)
    regret = [value - series[0] for value in series]
    return sum((regret[i] + regret[i + 1]) / 2 for i in range(len(regret) - 1))


def final_tail_retention(chain: dict) -> float:
    """The confirmatory outcome: tail retention at the last generation.

    ``PREREGISTRATION.md`` names the frozen tail-retention metric as confirmatory
    alongside the primary NLL-regret AUC. It is reported whether or not it agrees.
    """
    return sorted(chain["metrics"], key=lambda m: m["generation"])[-1]["tail_retention"]


def budget_axes(by_arm: dict[str, list[dict]]) -> dict:
    """Measure both axes ``PROTOCOL.md`` §4 requires, from the chains themselves.

    Human spread is assessed across *spending* arms only, because a control arm
    spending zero is matched by design rather than by accident. Total optimizer
    tokens are assessed across every arm, since displacement (``DECISIONS.md`` P-011)
    is supposed to equalise them including the control -- that is the whole point of
    it, and the control is where additive assembly hid a confound nobody had noticed.
    """
    # Per chain, not per arm mean. The launcher's guard compares individual realised
    # spends, and a paper quoting an arm-mean spread would print a smaller number than
    # the tool that gates the run -- two figures for one quantity, which is how F-024
    # started.
    spending = [c["consumed_human_tokens"] for chains in by_arm.values() for c in chains
                if c["consumed_human_tokens"]]
    total = [c["consumed_total_tokens"] for chains in by_arm.values() for c in chains]

    def spread(values) -> float:
        values = list(values)
        if not values:
            return 0.0
        low, high = min(values), max(values)
        return (high - low) / high if high else 0.0

    human_spread = spread(spending)
    total_spread = spread(total)
    # Same margin the launcher's guard uses: an order of magnitude below the frozen
    # practical effect threshold, so a spread that could masquerade as an effect fails.
    permitted = THRESHOLD_RELATIVE * SPREAD_MARGIN_BELOW_THRESHOLD
    return {
        "human_spread": human_spread,
        "total_spread": total_spread,
        "permitted": permitted,
        "human_ok": human_spread <= permitted,
        "total_ok": total_spread <= permitted,
        "both_ok": human_spread <= permitted and total_spread <= permitted,
    }


def wall_hours(run_dir: Path) -> tuple[float, float, float]:
    """Wall-clock hours for the grid, and for everything spent reaching it.

    Shards inside one launch run concurrently, so that launch costs its *longest*
    shard. Launches run one after another, so a grid assembled from several costs
    their *sum*. Taking a single max over every summary in the directory -- which is
    what this did when one launch was the whole run -- reports the longest phase and
    calls it the run, understating a four-phase grid by most of its duration.

    ``FAILURE_LOG.md`` F-020a is the same error in the other direction: a wall time
    inferred rather than read. Both figures here are read from ``wall_seconds``.

    Returns ``(clean, productive, total)`` in hours, each read from ``wall_seconds``:

    * ``clean`` -- launches in which every chain finished. This is what the grid takes
      when the infrastructure works, and the figure a reproducer should budget.
    * ``productive`` -- launches that completed at least one chain. Includes the
      partly-successful attempt that F-026 killed, which still produced four chains.
    * ``total`` -- every launch present, including one that produced nothing. What
      this grid actually cost in pod time.

    Reporting one number here would require choosing which question to answer, so all
    three are emitted and the results document says which is which.
    """
    launches: dict[tuple[str, str], list[tuple[float, int, int]]] = {}
    for path in sorted(run_dir.rglob("pilot_summary*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        stem = path.stem.replace("pilot_summary", "").strip("_")
        parts = [p for p in stem.split("_") if p]
        seeds = next((p for p in parts if p.startswith("seeds")), "")
        # Shard count distinguishes two launches that share a seed scope, which is how
        # the abandoned 4-shard and 2-shard attempts stay separate from each other.
        shard = next((p for p in parts if p.startswith("shard")), "")
        count = shard.split("of")[-1] if "of" in shard else "1"
        chains = payload.get("chains", [])
        done = sum(1 for c in chains if c.get("status") == "complete")
        launches.setdefault((seeds, count), []).append(
            (payload.get("wall_seconds", 0.0), done, len(chains))
        )

    clean = productive = total = 0.0
    for shards in launches.values():
        longest = max(seconds for seconds, _, _ in shards)
        total += longest
        if any(done for _, done, _ in shards):
            productive += longest
        if all(done == seen for _, done, seen in shards):
            clean += longest
    return clean / 3600, productive / 3600, total / 3600


def strongest_eligible_baseline(by_arm: dict[str, list[dict]]) -> str:
    """The non-joint arm with the lowest mean AUC regret.

    ``PREREGISTRATION.md`` fixes the primary contrast as "joint minus strongest
    eligible non-joint baseline". The *rule* is preregistered; which arm satisfies it
    is read from the outcome, and the results document says so. This is the
    conservative direction -- it compares `joint` against the best thing it has to
    beat, never against a convenient one.
    """
    candidates = [a for a in ARM_ORDER if a != "joint" and by_arm.get(a)]
    return min(candidates, key=lambda a: st.mean(auc_regret(c) for c in by_arm[a]))


def primary_contrast_is_admissible(by_arm: dict[str, list[dict]]) -> bool:
    """Whether this run supports the preregistered comparison at all.

    ``CLAIMS.md`` C-002's falsification clause voids the contrast if budget equality
    fails, so a run that fails either axis gets descriptives and no comparison.
    """
    return budget_axes(by_arm)["both_ok"]


def write_table(by_arm: dict[str, list[dict]], out: Path, run_dir: Path) -> None:
    axes = budget_axes(by_arm)
    admissible = axes["both_ok"]
    baseline = strongest_eligible_baseline(by_arm)

    lines = [
        "% AUTO-GENERATED by scripts/generate_pilot_outputs.py. DO NOT EDIT VALUES BY HAND.",
        f"% Derived from chain_result.json artifacts of {run_dir.name}.",
    ]
    if admissible:
        lines += [
            "% Both budget axes hold, so the preregistered contrast is reported below the",
            f"% table. Strongest eligible non-joint baseline: {baseline}.",
        ]
    else:
        lines += [
            "% The primary contrast is absent deliberately: this run fails budget matching",
            "% (FAILURE_LOG.md F-020, F-021), so the preregistered comparison is invalid.",
        ]
    lines += [
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Policy & Chains & Human tokens & AUC regret & SD & Tail retention \\",
        r"\midrule",
    ]
    for arm in ARM_ORDER:
        chains = by_arm.get(arm)
        if not chains:
            continue
        areas = [auc_regret(c) for c in chains]
        spend = st.mean(c["consumed_human_tokens"] for c in chains)
        mean, sd = st.mean(areas), st.stdev(areas)
        tail = st.mean(final_tail_retention(c) for c in chains)
        marker = "" if admissible else (r"$^{\dagger}$" if arm == "joint" else "")
        lines.append(
            f"{ARM_LABEL[arm]}{marker} & {len(chains)} & {spend:,.0f} & "
            f"{mean:.4f} & {sd:.4f} & {tail:.4f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", ""]

    if admissible:
        primary = paired_contrast(by_arm, "joint", baseline)
        threshold = THRESHOLD_RELATIVE * st.mean(auc_regret(c) for c in by_arm["random"])
        equivalent = max(abs(primary["low"]), abs(primary["high"])) < threshold
        lines += [
            f"% Primary contrast, joint minus {baseline} (paired by seed, 95\\% t interval):",
            f"%   {primary['mean']:+.5f} [{primary['low']:+.5f}, {primary['high']:+.5f}], "
            f"{primary['relative_percent']:+.2f}\\% relative.",
            f"%   Practical-equivalence region is +/-{threshold:.5f} "
            f"({THRESHOLD_RELATIVE * 100:.0f}\\% of the fresh-random mean, the "
            "denominator U-006 was settled against).",
            "%   Interval lies entirely inside that region: "
            f"{'yes' if equivalent else 'no'}.",
            f"% Budget axes: human spread {axes['human_spread'] * 100:.4f}\\%, "
            f"total spread {axes['total_spread'] * 100:.4f}\\%, "
            f"permitted {axes['permitted'] * 100:.4f}\\%.",
        ]
    else:
        lines += [
            r"% $\dagger$ joint underspent its human budget at every seed. Its row is",
            r"% descriptive only. See FAILURE_LOG.md F-020.",
        ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def paired_contrast(by_arm: dict[str, list[dict]], treatment: str, baseline: str) -> dict:
    """Paired-by-seed difference in AUC regret, with a 95% interval.

    Paired because chains share a seed across arms; ``tests/analysis`` holds the
    equivalent computation used for the results document.
    """
    treat = {c["chain_seed"]: auc_regret(c) for c in by_arm[treatment]}
    base = {c["chain_seed"]: auc_regret(c) for c in by_arm[baseline]}
    seeds = sorted(set(treat) & set(base))
    diffs = [treat[s] - base[s] for s in seeds]
    mean, sd = st.mean(diffs), st.stdev(diffs)
    # t_{.975, 4} for the frozen five-seed set. Asserted rather than assumed.
    if len(diffs) != 5:
        raise SystemExit(f"expected 5 paired seeds for {treatment} vs {baseline}, got {len(diffs)}")
    half = 2.776 * sd / len(diffs) ** 0.5
    base_mean = st.mean(base.values())
    return {
        "mean": mean,
        "low": mean - half,
        "high": mean + half,
        "relative_percent": 100 * mean / base_mean,
        "sd": sd,
    }


def write_macros(by_arm: dict[str, list[dict]], run_dir: Path, out: Path) -> None:
    """Emit every result number the manuscript quotes, as LaTeX macros.

    ``tests/analysis/test_generated_outputs.py`` forbids bare decimals in section
    prose, because a hand-entered value drifts from the artifacts silently. Prose
    therefore cites macros and this function is the only place the values are computed.
    """
    areas = {arm: [auc_regret(c) for c in chains] for arm, chains in by_arm.items()}
    spends = {arm: [c["consumed_human_tokens"] for c in chains] for arm, chains in by_arm.items()}

    axes = budget_axes(by_arm)
    admissible = axes["both_ok"]
    baseline = strongest_eligible_baseline(by_arm)

    spending = {arm: v for arm, v in spends.items() if any(v)}
    # "Matched" means the arms a contrast may legitimately be drawn between. When both
    # axes hold that is every spending arm including joint; when they do not, joint is
    # the arm that broke them and is excluded so the macro does not overstate coverage.
    matched = ({arm: v for arm, v in spending.items()} if admissible
               else {arm: v for arm, v in spending.items() if arm != "joint"})
    matched_all = [value for values in matched.values() for value in values]
    joint_spend = spends["joint"][0]

    cvs = [100 * st.stdev(v) / st.mean(v) for v in areas.values()]

    wall_clean, wall, wall_all = wall_hours(run_dir)

    contrasts = {
        "SelRand": paired_contrast(by_arm, "selection_only", "random"),
        "SchedRand": paired_contrast(by_arm, "schedule_only", "random"),
        "RandNone": paired_contrast(by_arm, "random", "no_rescue"),
        "JointSel": paired_contrast(by_arm, "joint", "selection_only"),
        "SelNone": paired_contrast(by_arm, "selection_only", "no_rescue"),
        "JointNone": paired_contrast(by_arm, "joint", "no_rescue"),
    }
    # Denominator for the 2% practical threshold is `random` -- the unselective-spending
    # reference -- matching both documents that settled U-006:
    # docs/decisions/effect_threshold_review_2026-08-19.md computes 0.05049 as 2% of
    # random's 2.52454, and powered_design_sizing_2026-08-19.md sizes against the same
    # figure. This script previously used the strongest baseline instead, which is a
    # third convention for one frozen quantity. Corrected to the documented one.
    #
    # The choice is recorded rather than quietly made because it is a threshold
    # definition touched after primary outcomes were open, which U-006 exists to
    # prevent. PilotThresholdUnitsAlt below carries the other convention so a reader can
    # check the verdict under both; for this run they agree.
    threshold_units = THRESHOLD_RELATIVE * st.mean(areas["random"])
    threshold_units_alt = THRESHOLD_RELATIVE * st.mean(areas[baseline])

    def number(value: float, places: int) -> str:
        return f"{value:.{places}f}"

    def thousands(value: float) -> str:
        return f"{value:,.0f}".replace(",", "{,}")

    macros = {
        "PilotChains": str(sum(len(v) for v in by_arm.values())),
        "PilotSeeds": str(len(by_arm["joint"])),
        "PilotHorizon": str(len(by_arm["joint"][0]["metrics"])),
        "PilotWallHoursClean": number(wall_clean, 2),
        "PilotWallHours": number(wall, 2),
        "PilotWallHoursIncludingFailed": number(wall_all, 2),
        "PilotCeiling": thousands(LIFETIME_BUDGET),
        "PilotJointSpend": thousands(joint_spend),
        "PilotJointShortfall": thousands(LIFETIME_BUDGET - joint_spend),
        "PilotJointShortfallPct": number(
            100 * (LIFETIME_BUDGET - joint_spend) / LIFETIME_BUDGET, 1
        ),
        "PilotMatchedLow": thousands(min(matched_all)),
        "PilotMatchedHigh": thousands(max(matched_all)),
        "PilotMatchedSpreadPct": number(
            100 * (max(matched_all) - min(matched_all)) / max(matched_all), 3
        ),
        "PilotCVLow": number(min(cvs), 2),
        "PilotCVHigh": number(max(cvs), 2),
        "PilotThresholdPct": "2",
        "PilotThresholdUnits": number(threshold_units, 4),
        "PilotPairedSD": number(contrasts["JointSel"]["sd"], 4),
    }
    for key, contrast in contrasts.items():
        macros[f"Pilot{key}Pct"] = number(abs(contrast["relative_percent"]), 2)
        macros[f"Pilot{key}Low"] = number(contrast["low"], 3)
        macros[f"Pilot{key}High"] = number(contrast["high"], 3)

    # Second budget axis. PROTOCOL.md section 4 requires matched total optimizer tokens
    # as well as matched human tokens; F-021 records that only the first was ever
    # asserted. These are the figures the results section quotes when saying so.
    totals = {arm: st.mean(c["consumed_total_tokens"] for c in chains)
              for arm, chains in by_arm.items()}
    low_total, high_total = min(totals.values()), max(totals.values())
    macros["PilotTotalSpreadPct"] = number(100 * (high_total - low_total) / high_total, 2)

    def total_gap(treatment: str, baseline: str) -> str:
        return number(100 * (totals[treatment] - totals[baseline]) / totals[baseline], 2)

    macros["PilotSchedRandTotalPct"] = total_gap("schedule_only", "random")
    macros["PilotSelRandTotalPct"] = total_gap("selection_only", "random")
    macros["PilotJointSelTotalPct"] = total_gap("joint", "selection_only")

    # Human-axis gap for the one pair matched on both, quoted alongside its total gap.
    human_means = {arm: st.mean(v) for arm, v in spends.items()}
    macros["PilotSchedRandHumanPct"] = number(
        100 * (human_means["schedule_only"] - human_means["random"]) / human_means["random"], 2
    )

    # Both budget axes, as the launcher's guard measures them: per chain, not per arm
    # mean. A paper quoting a smaller number than its own gate is how F-024 began.
    macros["PilotHumanSpreadPct"] = number(axes["human_spread"] * 100, 4)
    macros["PilotTotalSpreadExactPct"] = number(axes["total_spread"] * 100, 4)
    macros["PilotSpreadPermittedPct"] = number(axes["permitted"] * 100, 1)
    macros["PilotBudgetVerdict"] = "holds" if admissible else "fails"

    # The preregistered primary contrast. PREREGISTRATION.md fixes the rule -- joint
    # minus the strongest eligible non-joint baseline -- and the outcome decides which
    # arm that is. Emitting the identity as a macro keeps the prose from naming an arm
    # the artifacts did not select.
    macros["PilotPrimaryBaseline"] = ARM_LABEL[baseline]
    macros["PilotPrimaryBaselineKey"] = baseline.replace("_", " ")
    primary = paired_contrast(by_arm, "joint", baseline)
    macros["PilotPrimaryMean"] = number(primary["mean"], 4)
    macros["PilotPrimaryLow"] = number(primary["low"], 4)
    macros["PilotPrimaryHigh"] = number(primary["high"], 4)
    macros["PilotPrimaryPct"] = number(primary["relative_percent"], 2)
    macros["PilotPrimaryAbsPct"] = number(abs(primary["relative_percent"]), 2)
    reach = max(abs(primary["low"]), abs(primary["high"]))
    inside = reach < threshold_units
    covers_zero = primary["low"] <= 0 <= primary["high"]
    macros["PilotPrimaryCoversZero"] = "yes" if covers_zero else "no"
    macros["PilotPrimaryWithinThreshold"] = "yes" if inside else "no"
    macros["PilotThresholdUnitsAlt"] = number(threshold_units_alt, 4)
    macros["PilotPrimaryWithinThresholdAlt"] = (
        "yes" if reach < threshold_units_alt else "no")
    macros["PilotPrimaryReach"] = number(reach, 4)
    # C-002's falsification clause: not supported if the interval includes the
    # practically equivalent or harmful region. An interval wholly inside the
    # equivalence band is the strongest form of that -- equivalence, not ignorance.
    macros["PilotPrimarySupportsCTwo"] = "no" if (covers_zero or inside) else "yes"

    # Confirmatory outcome, reported whether or not it agrees with the primary.
    tails = {arm: [final_tail_retention(c) for c in chains]
             for arm, chains in by_arm.items()}
    for arm in ARM_ORDER:
        key = "".join(part.title() for part in arm.split("_"))
        macros[f"PilotTail{key}"] = number(st.mean(tails[arm]), 4)

    def paired_tail(treatment: str, base: str) -> dict:
        t = {c["chain_seed"]: final_tail_retention(c) for c in by_arm[treatment]}
        b = {c["chain_seed"]: final_tail_retention(c) for c in by_arm[base]}
        seeds = sorted(set(t) & set(b))
        diffs = [t[s] - b[s] for s in seeds]
        mean, sd = st.mean(diffs), st.stdev(diffs)
        half = 2.776 * sd / len(diffs) ** 0.5
        return {"mean": mean, "low": mean - half, "high": mean + half}

    tail_primary = paired_tail("joint", baseline)
    macros["PilotTailPrimaryMean"] = number(tail_primary["mean"], 5)
    macros["PilotTailPrimaryLow"] = number(tail_primary["low"], 5)
    macros["PilotTailPrimaryHigh"] = number(tail_primary["high"], 5)
    tail_sched = paired_tail("schedule_only", "random")
    macros["PilotTailSchedRandMean"] = number(tail_sched["mean"], 5)
    macros["PilotTailSchedRandLow"] = number(tail_sched["low"], 5)
    macros["PilotTailSchedRandHigh"] = number(tail_sched["high"], 5)
    macros["PilotTailSchedRandPct"] = number(
        100 * tail_sched["mean"] / st.mean(tails["random"]), 2
    )

    lines = [
        "% AUTO-GENERATED by scripts/generate_pilot_outputs.py. DO NOT EDIT VALUES BY HAND.",
        "% Every result number quoted in paper/sections/ is defined here and computed",
        "% from chain_result.json artifacts, so prose cannot drift from the run.",
        f"% run: {run_dir.name}",
    ]
    lines += [rf"\newcommand{{\{name}}}{{{value}}}" for name, value in sorted(macros.items())]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return macros


def write_figure(by_arm: dict[str, list[dict]], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # The "(underspent)" tag on joint was hardcoded for the run that underspent, and
    # would have gone on labelling a matched arm as unmatched -- the same shape as the
    # hardcoded contrast refusal this file used to carry. Derived from the chains: an arm
    # is flagged only when its own realised spend falls short of the highest by more than
    # the guard permits.
    spends = {arm: st.mean(c["consumed_human_tokens"] for c in chains)
              for arm, chains in by_arm.items()}
    spending = [v for v in spends.values() if v]
    ceiling = max(spending) if spending else 0.0
    permitted = THRESHOLD_RELATIVE * SPREAD_MARGIN_BELOW_THRESHOLD
    underspent = {arm for arm, value in spends.items()
                  if value and ceiling and (ceiling - value) / ceiling > permitted}

    figure, axis = plt.subplots(figsize=(7.0, 4.4))
    colours = plt.get_cmap("viridis")([0.05, 0.3, 0.5, 0.7, 0.92])

    for colour, arm in zip(colours, ARM_ORDER, strict=True):
        chains = by_arm.get(arm)
        if not chains:
            continue
        series = [nll_series(c) for c in chains]
        generations = range(len(series[0]))
        mean = [st.mean(s[g] for s in series) for g in generations]
        low = [min(s[g] for s in series) for g in generations]
        high = [max(s[g] for s in series) for g in generations]
        label = ARM_LABEL[arm] + (" (underspent)" if arm in underspent else "")
        axis.plot(list(generations), mean, color=colour, label=label, linewidth=1.9)
        # Min-max band rather than a confidence interval: five seeds is too few for the
        # latter to mean much, and the observed range is the honest summary.
        axis.fill_between(list(generations), low, high, color=colour, alpha=0.16, linewidth=0)

    axis.set_xlabel("Generation")
    axis.set_ylabel("Held-out human NLL")
    axis.set_title("Recursive degradation by allocation policy (5 seeds, min-max band)")
    axis.legend(frameon=False, fontsize=8, loc="upper left")
    axis.grid(alpha=0.25, linewidth=0.6)
    figure.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=200)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--table", type=Path,
                        default=Path("paper/tables/primary_results.tex"))
    parser.add_argument("--macros", type=Path,
                        default=Path("paper/tables/pilot_macros.tex"))
    parser.add_argument("--figure", type=Path,
                        default=Path("results/figures/pilot_nll_by_generation.png"))
    args = parser.parse_args()

    by_arm = load_chains(args.run_dir)
    counts = {arm: len(chains) for arm, chains in sorted(by_arm.items())}
    print(f"loaded {sum(counts.values())} chains: {counts}")

    write_table(by_arm, args.table, args.run_dir)
    print(f"wrote {args.table}")

    macros = write_macros(by_arm, args.run_dir, args.macros)
    print(f"wrote {args.macros} ({len(macros)} macros)")

    write_figure(by_arm, args.figure)
    print(f"wrote {args.figure}")

    axes = budget_axes(by_arm)
    print(f"\nbudget axes: human {axes['human_spread'] * 100:.4f}%, "
          f"total {axes['total_spread'] * 100:.4f}%, "
          f"permitted {axes['permitted'] * 100:.4f}%")
    if not axes["both_ok"]:
        print("NOTE: at least one axis fails. The primary contrast is not computed "
              "and the table says so.")
        return 0

    baseline = strongest_eligible_baseline(by_arm)
    primary = paired_contrast(by_arm, "joint", baseline)
    threshold = THRESHOLD_RELATIVE * st.mean(auc_regret(c) for c in by_arm["random"])
    print(f"primary contrast: joint - {baseline} = {primary['mean']:+.5f} "
          f"[{primary['low']:+.5f}, {primary['high']:+.5f}], "
          f"{primary['relative_percent']:+.2f}% relative")
    print(f"practical-equivalence region: +/-{threshold:.5f}")
    if max(abs(primary["low"]), abs(primary["high"])) < threshold:
        print("VERDICT: interval lies entirely inside the equivalence region. "
              "C-002 is not supported; this is equivalence, not absence of evidence.")
    elif primary["low"] <= 0 <= primary["high"]:
        print("VERDICT: interval covers zero but extends past the equivalence region. "
              "C-002 is not supported and the run does not establish equivalence either.")
    else:
        direction = "favours joint" if primary["mean"] < 0 else "favours the baseline"
        print(f"VERDICT: interval excludes zero and {direction}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
