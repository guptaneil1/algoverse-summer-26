"""Small dependency-free analysis functions used by fixtures and tests."""

from collections.abc import Mapping, Sequence


def regret_auc(regret_by_generation: Sequence[float]) -> float:
    """Trapezoidal area over equally spaced recursive generations."""

    if len(regret_by_generation) < 2:
        raise ValueError("at least two generations are required")
    return sum(
        (left + right) / 2
        for left, right in zip(regret_by_generation[:-1], regret_by_generation[1:], strict=True)
    )


def paired_difference(
    treatment_by_seed: Mapping[int, float], baseline_by_seed: Mapping[int, float]
) -> dict[int, float]:
    if treatment_by_seed.keys() != baseline_by_seed.keys():
        raise ValueError("paired conditions must contain exactly the same chain seeds")
    return {
        seed: treatment_by_seed[seed] - baseline_by_seed[seed]
        for seed in sorted(treatment_by_seed)
    }


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot average an empty sequence")
    return sum(values) / len(values)
