#!/usr/bin/env python3
"""Generate the final experiment's table set from immutable chain artifacts.

Implements the layout frozen in ``docs/paper/final_tables_plan.md``: five tables
whose columns, ordering and rounding are fixed now so that when the corrected grid
lands the only change is ``--run-dir``. Every number is computed from
``chain_result.json`` files. Nothing is typed.

The outcome computation is imported from ``generate_pilot_outputs`` rather than
restated, so the two scripts cannot drift into disagreeing about what AUC regret is.

**Budget gating.** A contrast whose two arms differ by more than the *permitted spread*
on either budget axis renders ``NOT ESTABLISHED`` instead of numbers. The permitted
spread is the project's own, imported rather than restated: the practical effect
threshold times ``SPREAD_MARGIN_BELOW_THRESHOLD`` (P-008), which is 0.2% at the frozen
2% threshold.
The pilot produced perfectly readable numbers for a comparison that was not
interpretable (FAILURE_LOG.md F-020, F-021); a table that prints them anyway invites
the reading the run cannot support.

Usage:
    python scripts/generate_final_tables.py \\
        --run-dir results/runs/primary_pilot_2026-08-18 \\
        --config configs/experiment/primary_pilot.json \\
        --outdir docs/paper/table_previews
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_pilot_outputs import (  # noqa: E402
    ARM_LABEL,
    ARM_ORDER,
    auc_regret,
    load_chains,
    nll_series,
)

from human_data_budget.runner.budget_matching import (  # noqa: E402
    SPREAD_MARGIN_BELOW_THRESHOLD,
    max_candidate_optimizer_tokens,
)

# Secondary contrasts, in the order the results section discusses them. The primary
# contrast is not in this list: it needs a baseline chosen by the preregistered rule
# from validation-only screening chains, which no run artifact carries.
SECONDARY = (
    ("joint", "schedule_only"),
    ("joint", "selection_only"),
    ("schedule_only", "random"),
    ("selection_only", "random"),
    ("random", "no_rescue"),
)

NOT_ESTABLISHED = r"\multicolumn{4}{c}{\textsc{not established}}"


def pct(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator


def arm_summary(chains: list[dict]) -> dict:
    areas = [auc_regret(c) for c in chains]
    final_tail = [c["metrics"][-1]["tail_retention"] for c in chains]
    human = [c["consumed_human_tokens"] for c in chains]
    total = [c["consumed_total_tokens"] for c in chains]
    return {
        "n": len(chains),
        "auc_mean": st.mean(areas),
        "auc_sd": st.stdev(areas),
        "auc_cv": pct(st.stdev(areas), st.mean(areas)),
        "tail_mean": st.mean(final_tail),
        "tail_sd": st.stdev(final_tail),
        "human": st.mean(human),
        "total": st.mean(total),
    }


def contrast(by_arm: dict[str, list[dict]], treatment: str, baseline: str) -> dict:
    """Paired-by-seed difference in AUC regret, with both budget gaps attached."""
    treat = {c["chain_seed"]: auc_regret(c) for c in by_arm[treatment]}
    base = {c["chain_seed"]: auc_regret(c) for c in by_arm[baseline]}
    seeds = sorted(set(treat) & set(base))
    diffs = [treat[s] - base[s] for s in seeds]
    mean, sd = st.mean(diffs), st.stdev(diffs)
    # Student t, two-sided 95%, n-1 df. Tabulated rather than imported so the script
    # keeps its no-dependency property; asserted below so an unlisted n cannot pass.
    t_crit = {2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 10: 2.228, 43: 2.017}
    if len(diffs) - 1 not in t_crit:
        raise SystemExit(f"no tabulated t for {len(diffs)} pairs; add it deliberately")
    half = t_crit[len(diffs) - 1] * sd / len(diffs) ** 0.5

    def spend(arm: str, field: str) -> float:
        return st.mean(c[field] for c in by_arm[arm])

    base_human = spend(baseline, "consumed_human_tokens")
    human_gap = (
        pct(spend(treatment, "consumed_human_tokens") - base_human, base_human)
        if base_human
        else float("nan")
    )
    total_gap = pct(
        spend(treatment, "consumed_total_tokens") - spend(baseline, "consumed_total_tokens"),
        spend(baseline, "consumed_total_tokens"),
    )
    return {
        "treatment": treatment,
        "baseline": baseline,
        "seeds": len(diffs),
        "mean": mean,
        "sd": sd,
        "low": mean - half,
        "high": mean + half,
        "relative": pct(mean, st.mean(base.values())),
        "human_gap": human_gap,
        "total_gap": total_gap,
    }


def verdict(c: dict, threshold_pct: float, permitted_pct: float) -> tuple[str, bool]:
    """Preregistered label, plus whether the budget gate lets it be reported.

    Labels are the four in PREREGISTRATION.md, decided by the mean and the interval
    against the practical threshold -- not by a p-value and not by the sign alone.
    The gate is the separate, tighter quantity: the permitted realised spread.
    """
    gated = abs(c["total_gap"]) > permitted_pct or (
        c["human_gap"] == c["human_gap"] and abs(c["human_gap"]) > permitted_pct
    )
    if gated:
        return "not established", False
    if c["relative"] <= -threshold_pct and c["high"] < 0:
        label = "beneficial"
    elif c["relative"] >= threshold_pct and c["low"] > 0:
        label = "harmful"
    elif -threshold_pct < c["relative"] < threshold_pct and c["low"] > -abs(
        c["mean"] / c["relative"] * threshold_pct if c["relative"] else 0
    ):
        label = "negligible"
    else:
        label = "uncertain"
    return label, True


def banner(run_id: str, source: str) -> list[str]:
    return [
        "% AUTO-GENERATED by scripts/generate_final_tables.py. DO NOT EDIT VALUES BY HAND.",
        f"% run: {run_id}",
        f"% source: {source}",
        "% Layout frozen in docs/paper/final_tables_plan.md.",
    ]


def money(value: float) -> str:
    return f"{value:,.0f}".replace(",", "{,}")


def write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def table_budget(
    summaries: dict, ceiling: int, run_id: str, source: str, permitted: float, bound: int
) -> list[str]:
    """T1: did the run earn the right to be compared at all.

    The per-arm column applies P-008's rule -- a spending arm lands within one
    indivisible candidate of its ceiling, a control arm sits at exactly zero -- and the
    footer applies the cross-arm rule on both axes. Neither is invented here; both come
    from ``runner.budget_matching``, which is what the launcher asserts.
    """
    spending = {a: s for a, s in summaries.items() if s["human"] > 0}
    human_hi, human_lo = max(s["human"] for s in spending.values()), min(
        s["human"] for s in spending.values()
    )
    totals = [s["total"] for s in summaries.values()]
    human_spread = pct(human_hi - human_lo, human_hi)
    total_spread = pct(max(totals) - min(totals), max(totals))
    lines = banner(run_id, source) + [
        r"\begin{tabular}{lrrrrc}",
        r"\toprule",
        r"Policy & Chains & Human tokens & \% of ceiling & Total tokens & "
        r"Within bound \\",
        r"\midrule",
    ]
    for arm in ARM_ORDER:
        s = summaries.get(arm)
        if not s:
            continue
        if s["human"] == 0:
            within = r"\checkmark"  # control: exactly zero is the constructed value
        else:
            within = r"\checkmark" if ceiling - s["human"] <= bound else r"$\times$"
        lines.append(
            f"{ARM_LABEL[arm]} & {s['n']} & {money(s['human'])} & "
            f"{pct(s['human'], ceiling):.2f} & {money(s['total'])} & {within} \\\\"
        )
    lines += [
        r"\midrule",
        f"Realised spread & & {human_spread:.2f}\\% & & {total_spread:.2f}\\% & "
        + (r"\checkmark" if max(human_spread, total_spread) <= permitted
           else r"$\times$") + r" \\",
        f"Permitted (P-008) & & {permitted:.2f}\\% & & {permitted:.2f}\\% & \\\\",
        r"\bottomrule",
        r"\end{tabular}",
    ]
    return lines


def table_outcomes(summaries: dict, run_id: str, source: str, comparable: set) -> list[str]:
    """T2: per-arm outcomes.

    ``comparable`` is the set of arms whose realised spend lets them be ranked against
    each other. The best value is bolded only within that set and only if it holds more
    than one arm: bolding a winner across arms that received different amounts of data
    is the overclaim this project's whole budget apparatus exists to prevent.
    """
    rankable = {a: s for a, s in summaries.items() if a in comparable}
    best_auc = min((s["auc_mean"] for s in rankable.values()), default=None)
    best_tail = max((s["tail_mean"] for s in rankable.values()), default=None)
    if len(rankable) < 2:
        best_auc = best_tail = None

    def mark(value: float, best: float | None) -> str:
        return (
            rf"\textbf{{{value:.4f}}}"
            if best is not None and abs(value - best) < 1e-12
            else f"{value:.4f}"
        )

    lines = banner(run_id, source) + [
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"& & \multicolumn{3}{c}{NLL-regret AUC $\downarrow$} & "
        r"\multicolumn{2}{c}{Tail retention $\uparrow$} \\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-7}",
        r"Policy & Chains & Mean & SD & CV (\%) & Final & SD \\",
        r"\midrule",
    ]
    for arm in ARM_ORDER:
        s = summaries.get(arm)
        if not s:
            continue
        lines.append(
            f"{ARM_LABEL[arm]} & {s['n']} & {mark(s['auc_mean'], best_auc)} & "
            f"{s['auc_sd']:.4f} & {s['auc_cv']:.2f} & "
            f"{mark(s['tail_mean'], best_tail)} & {s['tail_sd']:.4f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return lines


def table_contrasts(contrasts: list[dict], thr: float, permitted: float, run_id: str,
                    source: str) -> list[str]:
    lines = banner(run_id, source) + [
        r"\begin{tabular}{lrrrrrl}",
        r"\toprule",
        r"Contrast & $\Delta$ AUC $\downarrow$ & 95\% CI & Relative (\%) & "
        r"$\Delta$ human (\%) & $\Delta$ total (\%) & Verdict \\",
        r"\midrule",
        r"\textbf{Joint $-$ selected baseline} & "
        r"\multicolumn{5}{c}{\textsc{baseline not selected}} & --- \\",
        r"\midrule",
    ]
    for c in contrasts:
        label = f"{ARM_LABEL[c['treatment']]} $-$ {ARM_LABEL[c['baseline']].lower()}"
        text, reportable = verdict(c, thr, permitted)
        human = "---" if c["human_gap"] != c["human_gap"] else f"{c['human_gap']:.2f}"
        if reportable:
            body = (
                f"{c['mean']:.4f} & [{c['low']:.3f}, {c['high']:.3f}] & "
                f"{c['relative']:.2f} & {human} & {c['total_gap']:.2f}"
            )
        else:
            body = f"{NOT_ESTABLISHED} & {human} & {c['total_gap']:.2f}"
        lines.append(f"{label} & {body} & {text} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return lines


def table_per_chain(by_arm: dict, ceiling: int, bound: int, run_id: str,
                    source: str) -> list[str]:
    """T5: one row per chain, so the headline is reproducible without a re-run."""
    lines = banner(run_id, source) + [
        r"\begin{tabular}{llrrrrrl}",
        r"\toprule",
        r"Policy & Seed & Human tokens & Total tokens & Gens & "
        r"AUC regret $\downarrow$ & Tail retention $\uparrow$ & Budget \\",
        r"\midrule",
    ]
    for arm in ARM_ORDER:
        for c in sorted(by_arm.get(arm, []), key=lambda c: c["chain_seed"]):
            human = c["consumed_human_tokens"]
            if human == 0:
                status = "control"
            else:
                status = "within bound" if ceiling - human <= bound else "short"
            lines.append(
                f"{ARM_LABEL[arm]} & {c['chain_seed']} & {money(human)} & "
                f"{money(c['consumed_total_tokens'])} & {c['generations_completed']} & "
                f"{auc_regret(c):.4f} & {c['metrics'][-1]['tail_retention']:.4f} & "
                f"{status} \\\\"
            )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return lines


def table_trajectory(by_arm: dict, run_id: str, source: str) -> list[str]:
    horizon = len(next(iter(by_arm.values()))[0]["metrics"])
    arms = [a for a in ARM_ORDER if a in by_arm]
    lines = banner(run_id, source) + [
        r"\begin{tabular}{r" + "r" * len(arms) + "}",
        r"\toprule",
        r"Generation & " + " & ".join(ARM_LABEL[a] for a in arms)
        + r" \\",
        r"\multicolumn{" + str(len(arms) + 1)
        + r"}{l}{\footnotesize Held-out human NLL (nats), lower is better} \\",
        r"\midrule",
    ]
    for g in range(horizon):
        cells = [f"{st.mean(nll_series(c)[g] for c in by_arm[a]):.4f}" for a in arms]
        lines.append(f"{g} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return lines


# Arms that cannot be ranked are drawn dashed, so the figure carries the same
# distinction the tables do. Written as raw SVG because the analysis environment
# has no plotting dependency and a figure that cannot be regenerated is not evidence.
PALETTE = {
    "no_rescue": "#6b7280",
    "random": "#2563eb",
    "schedule_only": "#0891b2",
    "selection_only": "#c2410c",
    "joint": "#7c3aed",
}


def write_svg(trajectory: dict[str, list[float]], comparable: set, out: Path) -> None:
    """Held-out human NLL against generation, one line per arm."""
    width, height = 720, 420
    left, right, top, bottom = 70, 250, 30, 55
    arms = [a for a in ARM_ORDER if a in trajectory]
    horizon = len(trajectory[arms[0]])
    values = [v for series in trajectory.values() for v in series]
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad

    def x(g: int) -> float:
        return left + (width - left - right) * g / (horizon - 1)

    def y(v: float) -> float:
        return top + (height - top - bottom) * (hi - v) / (hi - lo)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="system-ui, sans-serif" font-size="12">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    for tick in range(5):
        v = lo + (hi - lo) * tick / 4
        parts.append(
            f'<line x1="{left}" y1="{y(v):.1f}" x2="{width - right}" y2="{y(v):.1f}" '
            f'stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{left - 8}" y="{y(v) + 4:.1f}" text-anchor="end" '
            f'fill="#4b5563">{v:.2f}</text>'
        )
    for g in range(horizon):
        parts.append(
            f'<text x="{x(g):.1f}" y="{height - bottom + 18}" text-anchor="middle" '
            f'fill="#4b5563">{g}</text>'
        )
    parts.append(
        f'<text x="{(left + width - right) / 2:.0f}" y="{height - 12}" '
        f'text-anchor="middle" fill="#111827">Generation</text>'
    )
    parts.append(
        f'<text x="16" y="{(top + height - bottom) / 2:.0f}" fill="#111827" '
        f'transform="rotate(-90 16 {(top + height - bottom) / 2:.0f})" '
        f'text-anchor="middle">Held-out human NLL (nats)</text>'
    )
    for index, arm in enumerate(arms):
        points = " ".join(f"{x(g):.1f},{y(v):.1f}" for g, v in enumerate(trajectory[arm]))
        dash = "" if arm in comparable else ' stroke-dasharray="5 4"'
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{PALETTE[arm]}" '
            f'stroke-width="2"{dash}/>'
        )
        ly = top + 6 + index * 20
        parts.append(
            f'<line x1="{width - right + 10}" y1="{ly}" x2="{width - right + 34}" '
            f'y2="{ly}" stroke="{PALETTE[arm]}" stroke-width="2"{dash}/>'
        )
        suffix = "" if arm in comparable else " (not comparable)"
        parts.append(
            f'<text x="{width - right + 40}" y="{ly + 4}" fill="#111827">'
            f'{ARM_LABEL[arm]}{suffix}</text>'
        )
    parts.append("</svg>")
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_markdown(payload: dict, out: Path) -> None:
    """A reviewable preview: the same numbers, rendered, with draft captions.

    Captions follow the Algoverse submission checklist section 7 -- readable alone,
    units stated, direction marked, best result marked, and a stated takeaway rather
    than a description of the visual.
    """
    arms = payload["arms"]
    comparable = payload["comparable_arms"]
    permitted = payload["permitted_spread_percent"]
    label = dict(ARM_LABEL)
    lines = [
        f"# Table preview -- {payload['run_id']}",
        "",
        "**AUTO-GENERATED by `scripts/generate_final_tables.py`. Do not edit values.**",
        f"Source: `{payload['source']}`. Layout: `docs/paper/final_tables_plan.md`.",
        "",
        "> These are **pilot** numbers, shown to exercise the layout the final grid will",
        "> use. The pilot's primary contrast is not established (FAILURE_LOG.md F-020,",
        "> F-021). Nothing here is a result.",
        "",
        "## Table 1 — Budget realisation",
        "",
        "| Policy | Chains | Human tokens | % of ceiling | Total tokens | Within bound |",
        "|---|---:|---:|---:|---:|:--:|",
    ]
    for arm in ARM_ORDER:
        if arm not in arms:
            continue
        a = arms[arm]
        within = "yes" if (a["human"] == 0 or payload["ceiling"] - a["human"]
                           <= payload["indivisibility_bound"]) else "**no**"
        lines.append(
            f"| {label[arm]} | {a['n']} | {a['human']:,.0f} | "
            f"{100 * a['human'] / payload['ceiling']:.2f} | {a['total']:,.0f} | {within} |"
        )
    lines += [
        "",
        f"*Caption (draft).* Realised spend per policy against a "
        f"{payload['ceiling']:,} optimizer-token lifetime ceiling, in tokens actually "
        "consumed by the optimizer. A policy is within bound when its shortfall is no "
        f"larger than the largest single rescue candidate "
        f"({payload['indivisibility_bound']:,} tokens), which is the only shortfall "
        "indivisibility can explain. Fair comparison additionally requires the realised "
        f"spread across arms to stay below {permitted:.2f}% on both axes.",
        "",
        "## Table 2 — Per-arm outcomes",
        "",
        "| Policy | Chains | AUC regret ↓ | SD | CV (%) | Tail retention ↑ | SD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    rankable = {a: arms[a] for a in comparable if a in arms}
    best_auc = min((v["auc_mean"] for v in rankable.values()), default=None)
    best_tail = max((v["tail_mean"] for v in rankable.values()), default=None)
    for arm in ARM_ORDER:
        if arm not in arms:
            continue
        a = arms[arm]
        auc = (f"**{a['auc_mean']:.4f}**" if best_auc is not None
               and abs(a["auc_mean"] - best_auc) < 1e-12 else f"{a['auc_mean']:.4f}")
        tail = (f"**{a['tail_mean']:.4f}**" if best_tail is not None
                and abs(a["tail_mean"] - best_tail) < 1e-12 else f"{a['tail_mean']:.4f}")
        lines.append(
            f"| {label[arm]} | {a['n']} | {auc} | {a['auc_sd']:.4f} | {a['auc_cv']:.2f} "
            f"| {tail} | {a['tail_sd']:.4f} |"
        )
    lines += [
        "",
        "*Caption (draft).* Area under the generation-wise held-out human NLL-regret "
        "curve (nats x generations, lower is better) and end-of-horizon tail retention "
        "(ratio in [0,1], higher is better), each averaged over the frozen seed set with "
        "between-chain SD. Bold marks the best value **among arms whose realised spend "
        f"is within the permitted {permitted:.2f}% spread of one another** "
        f"({', '.join(label[a] for a in comparable)}); the remaining arms received "
        "different amounts of data and are shown but not ranked.",
        "",
        "## Table 3 — Paired contrasts",
        "",
        "| Contrast | ΔAUC ↓ | 95% CI | Relative (%) | Δhuman (%) | Δtotal (%) | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
        "| **Joint − selected baseline** | — | — | — | — | — | baseline not selected |",
    ]
    for c in payload["contrasts"]:
        text, reportable = verdict(c, payload["threshold_percent"], permitted)
        human = "—" if c["human_gap"] != c["human_gap"] else f"{c['human_gap']:.2f}"
        cells = (
            f"{c['mean']:.4f} | [{c['low']:.3f}, {c['high']:.3f}] | {c['relative']:.2f}"
            if reportable else "— | — | —"
        )
        lines.append(
            f"| {label[c['treatment']]} − {label[c['baseline']].lower()} | {cells} | "
            f"{human} | {c['total_gap']:.2f} | {text} |"
        )
    lines += [
        "",
        "*Caption (draft).* Paired-by-seed differences in NLL-regret AUC, with "
        "two-sided 95% intervals over the frozen seeds. A contrast whose arms differ by "
        f"more than {permitted:.2f}% on either budget axis is reported as not "
        "established rather than as a number: unequal data, not allocation strategy, "
        "would explain any difference. The primary row stays empty because the "
        "preregistered baseline is chosen from validation-only screening chains, which "
        "this run does not carry.",
        "",
        "## Figure 1 — Held-out NLL by generation",
        "",
        "![NLL by generation](F1_nll_by_generation.svg)",
        "",
        "*Caption (draft).* Held-out human NLL (nats, lower is better) against "
        "generation, averaged over the frozen seed set. Dashed lines mark arms whose "
        "realised spend places them outside the comparable set, so their separation from "
        "the solid lines cannot be read as an effect of allocation.",
        "",
        "## Appendix tables",
        "",
        "`T4_trajectory.tex` (per-generation means) and `T5_per_chain.tex` (one row per "
        f"chain, {sum(v['n'] for v in arms.values())} rows) are generated alongside "
        "these and are meant for the appendix.",
        "",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    ceiling = config["lifetime_human_budget"]
    threshold = 100 * config["practical_effect_threshold_relative"]
    # P-008: realised spread must sit an order of magnitude below the effect threshold,
    # so the gate is 0.2% at a 2% threshold. Imported, not restated.
    permitted = threshold * SPREAD_MARGIN_BELOW_THRESHOLD
    run_id = config["run_id"]
    source = str(args.run_dir)
    bound = max_candidate_optimizer_tokens(
        config["data"]["manifests"]["rescue_candidates"]["path"]
    )

    by_arm = load_chains(args.run_dir)
    summaries = {arm: arm_summary(chains) for arm, chains in by_arm.items()}
    contrasts = [contrast(by_arm, t, b) for t, b in SECONDARY]

    # Arms that may be ranked against one another: those whose realised spend sits
    # within the permitted spread of the reference arm on both axes. The control is
    # never in this set -- it is the reference point, not a competitor.
    spending = {a: s for a, s in summaries.items() if s["human"] > 0}
    reference = max(spending, key=lambda a: spending[a]["human"])
    comparable = {
        a for a, s in spending.items()
        if abs(pct(s["human"] - spending[reference]["human"], spending[reference]["human"]))
        <= permitted
        and abs(pct(s["total"] - spending[reference]["total"], spending[reference]["total"]))
        <= permitted
    }

    args.outdir.mkdir(parents=True, exist_ok=True)
    write(args.outdir / "T1_budget_realisation.tex",
          table_budget(summaries, ceiling, run_id, source, permitted, bound))
    write(args.outdir / "T2_per_arm_outcomes.tex",
          table_outcomes(summaries, run_id, source, comparable))
    write(args.outdir / "T3_paired_contrasts.tex",
          table_contrasts(contrasts, threshold, permitted, run_id, source))
    write(args.outdir / "T4_trajectory.tex", table_trajectory(by_arm, run_id, source))
    write(args.outdir / "T5_per_chain.tex",
          table_per_chain(by_arm, ceiling, bound, run_id, source))

    payload = {
        "run_id": run_id,
        "source": source,
        "ceiling": ceiling,
        "threshold_percent": threshold,
        "permitted_spread_percent": permitted,
        "indivisibility_bound": bound,
        "comparable_arms": sorted(comparable),
        "arms": {a: summaries[a] for a in ARM_ORDER if a in summaries},
        "contrasts": contrasts,
        "trajectory": {
            a: [st.mean(nll_series(c)[g] for c in by_arm[a])
                for g in range(len(by_arm[a][0]["metrics"]))]
            for a in ARM_ORDER if a in by_arm
        },
    }
    (args.outdir / "table_data.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_svg(payload["trajectory"], comparable, args.outdir / "F1_nll_by_generation.svg")
    write_markdown(payload, args.outdir / "PREVIEW.md")
    print(f"wrote 5 tables, PREVIEW.md, F1_nll_by_generation.svg and table_data.json "
          f"to {args.outdir}")


if __name__ == "__main__":
    main()
