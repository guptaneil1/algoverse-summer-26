"""Tail-retention metrics: ratio-based primary and NLL-gap secondary candidate."""

from collections.abc import Mapping, Sequence


def tail_retention(
    current_mode_scores: Mapping[str, float],
    reference_mode_scores: Mapping[str, float],
    tail_modes: set[str],
) -> float:
    """Mean clipped current/reference ratio over independently frozen tail modes.

    Range [0, 1]. 1.0 means the model preserves all tail coverage relative to the
    reference. Independent of the policy's undercoverage_score selection signal.
    """
    if not tail_modes:
        raise ValueError("tail_modes cannot be empty")
    ratios: list[float] = []
    for mode in sorted(tail_modes):
        reference = reference_mode_scores.get(mode)
        current = current_mode_scores.get(mode)
        if reference is None or current is None:
            raise ValueError(f"missing tail mode score: {mode}")
        if reference <= 0:
            raise ValueError("reference tail scores must be positive")
        ratios.append(min(1.0, max(0.0, current / reference)))
    return sum(ratios) / len(ratios)


def nll_gap(tail_nlls: Sequence[float], common_nlls: Sequence[float]) -> float:
    """Mean per-example NLL on tail examples minus mean on common examples.

    Positive values mean the model finds tail text harder than common text.
    Computed directly from held-out NLL values; never reads the policy's
    undercoverage_score, so it is independent of the selection signal.
    """
    if not tail_nlls or not common_nlls:
        raise ValueError("both tail_nlls and common_nlls must be non-empty")
    return sum(tail_nlls) / len(tail_nlls) - sum(common_nlls) / len(common_nlls)
