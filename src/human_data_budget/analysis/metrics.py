"""Small dependency-free analysis functions used by fixtures and tests."""

import random
from collections.abc import Mapping, Sequence


def regret_auc(regret_by_generation: Sequence[float]) -> float:
    """Calculate trapezoidal area over equally spaced generations."""
    if len(regret_by_generation) < 2:
        raise ValueError("at least two generations are required")

    return sum(
        (left + right) / 2
        for left, right in zip(
            regret_by_generation[:-1],
            regret_by_generation[1:],
            strict=True,
        )
    )


def paired_difference(
    treatment_by_seed: Mapping[int, float],
    baseline_by_seed: Mapping[int, float],
) -> dict[int, float]:
    """Calculate treatment-minus-baseline differences by paired seed."""
    validate_paired_seeds(treatment_by_seed, baseline_by_seed)

    return {
        seed: treatment_by_seed[seed] - baseline_by_seed[seed]
        for seed in sorted(treatment_by_seed)
    }


def mean(values: Sequence[float]) -> float:
    """Calculate the arithmetic mean."""
    if not values:
        raise ValueError("cannot average an empty sequence")

    return sum(values) / len(values)


def validate_paired_seeds(
    treatment_by_seed: Mapping[int, float],
    baseline_by_seed: Mapping[int, float],
) -> tuple[int, ...]:
    """Require treatment and baseline to use identical chain seeds."""
    treatment_seeds = set(treatment_by_seed)
    baseline_seeds = set(baseline_by_seed)

    if treatment_seeds != baseline_seeds:
        missing_from_treatment = sorted(
            baseline_seeds - treatment_seeds
        )
        missing_from_baseline = sorted(
            treatment_seeds - baseline_seeds
        )

        raise ValueError(
            "paired conditions must contain exactly the same chain seeds; "
            f"missing_from_treatment={missing_from_treatment}, "
            f"missing_from_baseline={missing_from_baseline}"
        )

    if not treatment_seeds:
        raise ValueError(
            "paired analysis requires at least one chain seed"
        )

    return tuple(sorted(treatment_seeds))


def paired_mean_difference(
    treatment_by_seed: Mapping[int, float],
    baseline_by_seed: Mapping[int, float],
) -> float:
    """Average the treatment-minus-baseline paired differences."""
    differences = paired_difference(
        treatment_by_seed,
        baseline_by_seed,
    )

    return mean(list(differences.values()))


def paired_bootstrap_interval(
    treatment_by_seed: Mapping[int, float],
    baseline_by_seed: Mapping[int, float],
    *,
    confidence: float = 0.95,
    bootstrap_samples: int = 5000,
    seed: int = 0,
) -> tuple[float, float]:
    """Bootstrap an interval over complete paired recursive chains."""
    paired_seeds = validate_paired_seeds(
        treatment_by_seed,
        baseline_by_seed,
    )

    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    if bootstrap_samples <= 0:
        raise ValueError("bootstrap_samples must be positive")

    differences = [
        treatment_by_seed[chain_seed]
        - baseline_by_seed[chain_seed]
        for chain_seed in paired_seeds
    ]

    rng = random.Random(seed)
    bootstrap_means: list[float] = []

    for _ in range(bootstrap_samples):
        sample = [
            differences[rng.randrange(len(differences))]
            for _ in differences
        ]
        bootstrap_means.append(mean(sample))

    bootstrap_means.sort()

    alpha = 1.0 - confidence
    lower_index = int(
        (alpha / 2.0) * bootstrap_samples
    )
    upper_index = int(
        (1.0 - alpha / 2.0) * bootstrap_samples
    ) - 1

    lower_index = max(
        0,
        min(lower_index, bootstrap_samples - 1),
    )
    upper_index = max(
        0,
        min(upper_index, bootstrap_samples - 1),
    )

    return (
        bootstrap_means[lower_index],
        bootstrap_means[upper_index],
    )