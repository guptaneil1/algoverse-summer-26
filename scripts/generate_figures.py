#!/usr/bin/env python3
"""Generate final-format figures from fake schema-valid chain results.

Implements the `docs/weekly/WEEK_2.md` Aarav deliverable: "Generate final-format
tables and figures from fake schema-valid results."

**These figures contain no experimental evidence.** They are produced by
``analysis.simulator``, which does not train a language model. Every figure is
watermarked accordingly, and the watermark is not optional — it is the mechanism
that stops a fixture plot being mistaken for a result if it escapes into a slide
deck. The purpose of generating them now is to freeze the *format* — axes,
labels, captions, ordering, colour assignment — so that when real chain results
exist the only thing that changes is the input path.

Determinism: figure bytes are stable across runs on the same matplotlib version,
so the emitted SHA-256 digests are meaningful (``PROTOCOL.md`` §3 requires
generated figures to carry content hashes). A matplotlib upgrade will change the
digests; that is expected and is why the version is recorded alongside them.

Dependency note: this script needs ``matplotlib``, which is deliberately **not**
a core dependency — the core package stays dependency-light apart from
``jsonschema``. Install it in the analysis environment only.

Usage
-----
    python scripts/generate_figures.py --output-dir results/figures --seeds 5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import matplotlib
except ModuleNotFoundError:  # pragma: no cover - environment guard
    sys.exit(
        "matplotlib is required for figure generation and is not installed.\n"
        "It is intentionally not a core dependency. Install it in the analysis\n"
        "environment: python -m pip install matplotlib"
    )

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from human_data_budget.analysis.metrics import (  # noqa: E402
    mean,
    paired_bootstrap_interval,
    paired_mean_difference,
    regret_auc,
)
from human_data_budget.analysis.simulator import (  # noqa: E402
    POLICY_NAMES,
    simulate_all_policies,
)

WATERMARK = "FIXTURE DATA — NOT SCIENTIFIC EVIDENCE — NO MODEL WAS TRAINED"

# Frozen colour assignment so policy identity is stable across every figure and
# across the eventual switch from fixture data to real results.
POLICY_COLOURS = {
    "random": "#8c8c8c",
    "schedule_only": "#1f77b4",
    "selection_only": "#ff7f0e",
    "joint": "#d62728",
}

POLICY_LABELS = {
    "random": "Fresh random rescue",
    "schedule_only": "Schedule-only",
    "selection_only": "Selection-only",
    "joint": "Joint (time × mode)",
}

# Stable PNG bytes: drop matplotlib's version banner and creation timestamp.
_PNG_METADATA = {"Software": None, "Creation Time": None}


def _stamp(figure: Any) -> None:
    """Apply the non-evidence watermark to a figure."""
    figure.text(
        0.5,
        0.5,
        "FIXTURE",
        fontsize=64,
        color="red",
        alpha=0.10,
        ha="center",
        va="center",
        rotation=30,
        zorder=10,
    )
    figure.text(
        0.5,
        0.005,
        WATERMARK,
        fontsize=7,
        color="red",
        ha="center",
        va="bottom",
    )


def _save(figure: Any, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Reserve footer space before stamping. bbox_inches="tight" is deliberately not
    # used: it re-crops after layout, which drops the watermark onto the x label.
    figure.subplots_adjust(bottom=0.22)
    _stamp(figure)
    figure.savefig(path, dpi=150, metadata=_PNG_METADATA)
    plt.close(figure)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simulate(seeds: list[int]) -> dict[int, dict[str, dict[str, Any]]]:
    """Run every policy on every seed, paired by construction."""
    return {seed: simulate_all_policies(chain_seed=seed) for seed in seeds}


def _series(runs: dict[int, dict[str, dict[str, Any]]], policy: str, key: str) -> list[float]:
    """Mean of ``key`` at each generation, averaged across chains."""
    per_seed = [
        [metric[key] for metric in runs[seed][policy]["chain_result"]["metrics"]]
        for seed in sorted(runs)
    ]
    return [
        mean([chain[generation] for chain in per_seed])
        for generation in range(len(per_seed[0]))
    ]


def figure_nll(runs: dict[int, dict[str, dict[str, Any]]], output: Path) -> str:
    figure, axes = plt.subplots(figsize=(7, 4.2))
    for policy in POLICY_NAMES:
        values = _series(runs, policy, "human_nll")
        axes.plot(
            range(len(values)),
            values,
            label=POLICY_LABELS[policy],
            color=POLICY_COLOURS[policy],
            marker="o",
            markersize=3.5,
            linewidth=1.6,
        )
    axes.set_xlabel("Recursive generation")
    axes.set_ylabel("Held-out human NLL")
    axes.set_title("Generation-wise held-out human NLL by treatment family")
    axes.legend(frameon=False, fontsize=8)
    axes.grid(alpha=0.25, linewidth=0.5)
    return _save(figure, output / "nll_by_generation.png")


def figure_tail(runs: dict[int, dict[str, dict[str, Any]]], output: Path) -> str:
    figure, axes = plt.subplots(figsize=(7, 4.2))
    for policy in POLICY_NAMES:
        values = _series(runs, policy, "tail_retention")
        axes.plot(
            range(len(values)),
            values,
            label=POLICY_LABELS[policy],
            color=POLICY_COLOURS[policy],
            marker="s",
            markersize=3.5,
            linewidth=1.6,
        )
    axes.set_ylim(0.0, 1.0)
    axes.set_xlabel("Recursive generation")
    axes.set_ylabel("Tail retention")
    axes.set_title("Tail retention by treatment family")
    axes.legend(frameon=False, fontsize=8)
    axes.grid(alpha=0.25, linewidth=0.5)
    return _save(figure, output / "tail_retention_by_generation.png")


def figure_allocation(runs: dict[int, dict[str, dict[str, Any]]], output: Path) -> str:
    """Per-policy allocation of the lifetime budget across generations and modes."""
    reference_seed = sorted(runs)[0]
    figure, axes_grid = plt.subplots(1, len(POLICY_NAMES), figsize=(12, 3.2), sharey=True)

    for axes, policy in zip(axes_grid, POLICY_NAMES, strict=True):
        allocations = runs[reference_seed][policy]["allocations"]
        generations = list(range(len(allocations)))
        modes = sorted({mode for step in allocations for mode in step["mode_allocations"]})
        bottom = [0.0] * len(generations)
        for index, mode in enumerate(modes):
            heights = [float(step["mode_allocations"].get(mode, 0)) for step in allocations]
            axes.bar(
                generations,
                heights,
                bottom=bottom,
                label=mode,
                color=["#4c72b0", "#dd8452"][index % 2],
                edgecolor="white",
                linewidth=0.4,
            )
            bottom = [carry + height for carry, height in zip(bottom, heights, strict=True)]
        axes.set_title(POLICY_LABELS[policy], fontsize=9)
        axes.set_xlabel("Generation", fontsize=8)
        axes.tick_params(labelsize=7)

    axes_grid[0].set_ylabel("Human tokens allocated", fontsize=8)
    axes_grid[-1].legend(frameon=False, fontsize=7, title="Mode", title_fontsize=7)
    figure.suptitle(
        "Lifetime human-token allocation across generations and modes "
        f"(chain seed {reference_seed}; every policy consumes an identical lifetime total)",
        fontsize=9,
    )
    return _save(figure, output / "allocation_by_generation.png")


def figure_paired_difference(
    runs: dict[int, dict[str, dict[str, Any]]], output: Path
) -> tuple[str, dict[str, Any]]:
    """Joint minus each non-joint baseline, with a paired bootstrap interval."""
    auc_by_policy = {
        policy: {
            seed: regret_auc(
                [m["human_nll"] for m in runs[seed][policy]["chain_result"]["metrics"]]
            )
            for seed in sorted(runs)
        }
        for policy in POLICY_NAMES
    }

    baselines = [policy for policy in POLICY_NAMES if policy != "joint"]
    contrasts: dict[str, Any] = {}
    centres, lowers, uppers = [], [], []

    for baseline in baselines:
        difference = paired_mean_difference(auc_by_policy["joint"], auc_by_policy[baseline])
        low, high = paired_bootstrap_interval(
            auc_by_policy["joint"], auc_by_policy[baseline], seed=0
        )
        contrasts[baseline] = {"mean_difference": difference, "interval": [low, high]}
        centres.append(difference)
        lowers.append(difference - low)
        uppers.append(high - difference)

    figure, axes = plt.subplots(figsize=(7, 3.4))
    # Policy labels are long; reserve left margin so they are not clipped.
    # _save only adjusts `bottom`, so this survives.
    figure.subplots_adjust(left=0.30)
    positions = range(len(baselines))
    axes.errorbar(
        centres,
        positions,
        xerr=[lowers, uppers],
        fmt="o",
        color="#d62728",
        capsize=4,
        linewidth=1.4,
    )
    axes.axvline(0.0, color="black", linewidth=0.9, linestyle="--")
    axes.set_yticks(list(positions))
    axes.set_yticklabels([POLICY_LABELS[baseline] for baseline in baselines], fontsize=8)
    axes.set_xlabel("Joint − baseline NLL regret AUC (negative favours joint)")
    axes.set_title("Paired chain-level contrast with bootstrap interval")
    axes.grid(alpha=0.25, axis="x", linewidth=0.5)
    return _save(figure, output / "paired_difference.png"), contrasts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output-dir", type=Path, default=Path("results/figures"))
    parser.add_argument(
        "--mirror-dir",
        type=Path,
        default=None,
        help=(
            "optional second location to write identical figures. Deliberately NOT "
            "defaulted to paper/figures: fixture output must not sit in the manuscript "
            "directory, where a stray \\includegraphics would pull a simulated figure "
            "into the PDF. Point this at paper/figures only when the inputs are real "
            "chain artifacts."
        ),
    )
    parser.add_argument("--seeds", type=int, default=5, help="number of paired chain seeds")
    args = parser.parse_args(argv)

    seeds = list(range(1, args.seeds + 1))
    runs = simulate(seeds)

    digests = {
        "nll_by_generation.png": figure_nll(runs, args.output_dir),
        "tail_retention_by_generation.png": figure_tail(runs, args.output_dir),
        "allocation_by_generation.png": figure_allocation(runs, args.output_dir),
    }
    paired_digest, contrasts = figure_paired_difference(runs, args.output_dir)
    digests["paired_difference.png"] = paired_digest

    if args.mirror_dir is not None:
        args.mirror_dir.mkdir(parents=True, exist_ok=True)
        for name in digests:
            (args.mirror_dir / name).write_bytes((args.output_dir / name).read_bytes())

    provenance = {
        "schema_version": "1.0",
        "fixture_only": True,
        "scientific_evidence": False,
        "warning": (
            "Figures generated from analysis.simulator. No language model was trained. "
            "These files must be regenerated from immutable chain artifacts before any "
            "figure appears in the manuscript as a result."
        ),
        "generator": "scripts/generate_figures.py",
        "matplotlib_version": matplotlib.__version__,
        "chain_seeds": seeds,
        "policies": list(POLICY_NAMES),
        "figure_sha256": digests,
        "paired_contrasts_joint_minus_baseline": contrasts,
    }
    provenance_path = args.output_dir / "figure_provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    for name, digest in digests.items():
        print(f"{digest}  {name}")
    print(f"provenance written to {provenance_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
