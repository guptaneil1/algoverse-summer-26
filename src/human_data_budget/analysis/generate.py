"""Validate fixture chain results and generate analysis outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from human_data_budget.analysis.metrics import (
    mean,
    paired_bootstrap_interval,
    paired_mean_difference,
    regret_auc,
)

FIXTURE_WARNING = "FIXTURE - NOT SCIENTIFIC EVIDENCE"

ChainResult = dict[str, Any]
GroupedResults = dict[str, dict[int, ChainResult]]


def load_results(paths: list[Path]) -> list[ChainResult]:
    """Load chain-result JSON files."""
    results: list[ChainResult] = []

    for path in paths:
        result = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(result, dict):
            raise ValueError(f"{path} does not contain a JSON object")

        results.append(result)

    if not results:
        raise ValueError("at least one chain result is required")

    return results


def chain_nll_auc(result: ChainResult) -> float:
    """Calculate chain-level held-out human NLL AUC."""
    metrics = result.get("metrics")

    if not isinstance(metrics, list) or len(metrics) < 2:
        raise ValueError(
            "each valid chain requires at least two generation metrics"
        )

    try:
        human_nll = [
            float(metric["human_nll"])
            for metric in metrics
        ]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "every generation metric requires numeric human_nll"
        ) from error

    return regret_auc(human_nll)


def group_valid_results(
    results: list[ChainResult],
) -> GroupedResults:
    """Group valid results by policy and chain seed."""
    grouped: GroupedResults = {}

    for result in results:
        if not result.get("valid", False):
            continue

        try:
            policy = str(result["policy"])
            chain_seed = int(result["chain_seed"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "valid results require policy and chain_seed"
            ) from error

        policy_results = grouped.setdefault(policy, {})

        if chain_seed in policy_results:
            raise ValueError(
                f"duplicate result for policy={policy}, "
                f"chain_seed={chain_seed}"
            )

        policy_results[chain_seed] = result

    if not grouped:
        raise ValueError("no valid chain results remain")

    return grouped


def validate_paired_result_sets(
    treatment_results: dict[int, ChainResult],
    baseline_results: dict[int, ChainResult],
) -> tuple[int, ...]:
    """Require identical seeds and exactly matched budgets."""
    treatment_seeds = set(treatment_results)
    baseline_seeds = set(baseline_results)

    if treatment_seeds != baseline_seeds:
        raise ValueError(
            "paired conditions must contain exactly the same chain seeds"
        )

    if not treatment_seeds:
        raise ValueError(
            "paired analysis requires at least one valid chain seed"
        )

    compared_results = [
        *treatment_results.values(),
        *baseline_results.values(),
    ]

    human_budgets = {
        int(result["consumed_human_tokens"])
        for result in compared_results
    }

    if len(human_budgets) != 1:
        raise ValueError(
            "compared policies must consume equal lifetime human tokens"
        )

    total_budgets = {
        int(result["consumed_total_tokens"])
        for result in compared_results
    }

    if len(total_budgets) != 1:
        raise ValueError(
            "compared policies must consume equal total optimizer tokens"
        )

    return tuple(sorted(treatment_seeds))


def aggregate_results(
    results: list[ChainResult],
) -> dict[str, Any]:
    """Produce a policy-level fixture aggregate."""
    grouped = group_valid_results(results)

    policies: dict[str, dict[str, float | int]] = {}

    for policy, by_seed in sorted(grouped.items()):
        auc_values = [
            chain_nll_auc(result)
            for _, result in sorted(by_seed.items())
        ]

        policies[policy] = {
            "chain_count": len(auc_values),
            "mean_nll_auc": mean(auc_values),
        }

    return {
        "schema_version": "1.0",
        "fixture_only": True,
        "scientific_evidence": False,
        "warning": FIXTURE_WARNING,
        "policies": policies,
    }


def aggregate(paths: list[Path]) -> dict[str, Any]:
    """Preserve the original path-based aggregate interface."""
    return aggregate_results(load_results(paths))


def paired_summary(
    results: list[ChainResult],
    *,
    treatment: str = "joint",
    baseline: str = "selection_only",
    confidence: float = 0.95,
    bootstrap_samples: int = 5000,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    """Calculate a paired fixture comparison."""
    grouped = group_valid_results(results)

    if treatment not in grouped:
        raise ValueError(f"missing treatment policy: {treatment}")

    if baseline not in grouped:
        raise ValueError(f"missing baseline policy: {baseline}")

    treatment_results = grouped[treatment]
    baseline_results = grouped[baseline]

    paired_seeds = validate_paired_result_sets(
        treatment_results,
        baseline_results,
    )

    treatment_auc = {
        seed: chain_nll_auc(treatment_results[seed])
        for seed in paired_seeds
    }
    baseline_auc = {
        seed: chain_nll_auc(baseline_results[seed])
        for seed in paired_seeds
    }

    mean_difference = paired_mean_difference(
        treatment_auc,
        baseline_auc,
    )
    interval = paired_bootstrap_interval(
        treatment_auc,
        baseline_auc,
        confidence=confidence,
        bootstrap_samples=bootstrap_samples,
        seed=bootstrap_seed,
    )

    return {
        "schema_version": "1.0",
        "fixture_only": True,
        "scientific_evidence": False,
        "warning": FIXTURE_WARNING,
        "treatment": treatment,
        "baseline": baseline,
        "paired_seeds": list(paired_seeds),
        "human_token_budget": int(
            treatment_results[paired_seeds[0]][
                "consumed_human_tokens"
            ]
        ),
        "total_optimizer_token_budget": int(
            treatment_results[paired_seeds[0]][
                "consumed_total_tokens"
            ]
        ),
        "treatment_mean_nll_auc": mean(
            list(treatment_auc.values())
        ),
        "baseline_mean_nll_auc": mean(
            list(baseline_auc.values())
        ),
        "paired_mean_difference": mean_difference,
        "bootstrap_confidence": confidence,
        "bootstrap_interval": list(interval),
    }


def escape_latex(value: str) -> str:
    """Escape underscores for simple generated LaTeX labels."""
    return value.replace("_", r"\_")


def render_fixture_latex(summary: dict[str, Any]) -> str:
    """Render a clearly labeled fixture-only LaTeX table."""
    treatment = escape_latex(str(summary["treatment"]))
    baseline = escape_latex(str(summary["baseline"]))

    treatment_mean = float(summary["treatment_mean_nll_auc"])
    baseline_mean = float(summary["baseline_mean_nll_auc"])
    difference = float(summary["paired_mean_difference"])

    lower, upper = [
        float(value)
        for value in summary["bootstrap_interval"]
    ]

    lines = [
        f"% {FIXTURE_WARNING}",
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Fixture-only paired NLL-regret analysis.}",
        r"\begin{tabular}{lr}",
        r"\hline",
        r"Quantity & Value \\",
        r"\hline",
        f"{treatment} mean AUC & {treatment_mean:.6f} \\\\",
        f"{baseline} mean AUC & {baseline_mean:.6f} \\\\",
        f"Paired mean difference & {difference:.6f} \\\\",
        f"Bootstrap lower bound & {lower:.6f} \\\\",
        f"Bootstrap upper bound & {upper:.6f} \\\\",
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--latex-output", type=Path)
    parser.add_argument("--treatment", default="joint")
    parser.add_argument("--baseline", default="selection_only")
    args = parser.parse_args()

    results = load_results(args.inputs)
    aggregate_payload = aggregate_results(results)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(aggregate_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.latex_output is not None:
        summary = paired_summary(
            results,
            treatment=args.treatment,
            baseline=args.baseline,
        )

        args.latex_output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        args.latex_output.write_text(
            render_fixture_latex(summary),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()