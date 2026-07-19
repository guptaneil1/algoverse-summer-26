"""Simple frozen-fixture tail-retention reference metric."""

from collections.abc import Mapping


def tail_retention(
    current_mode_scores: Mapping[str, float],
    reference_mode_scores: Mapping[str, float],
    tail_modes: set[str],
) -> float:
    """Mean clipped current/reference ratio over independently frozen tail modes."""

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
