"""Held-out NLL from already selected target-token log probabilities."""

from collections.abc import Iterable


def negative_log_likelihood(target_log_probabilities: Iterable[float]) -> float:
    values = list(target_log_probabilities)
    if not values:
        raise ValueError("at least one target-token log probability is required")
    if any(value > 0 for value in values):
        raise ValueError("log probabilities cannot be positive")
    return -sum(values) / len(values)
