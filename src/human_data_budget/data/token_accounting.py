"""Exact optimizer-consumed token accounting from realized batch records."""

from collections.abc import Iterable
from typing import Any


def consumed_tokens(
    batches: Iterable[dict[str, Any]], *, origin: str | None = None
) -> int:
    """Count non-padding optimizer-consumed tokens, optionally by origin.

    Each batch record contains parallel ``attention_mask`` and ``origins``
    rows. Values of one in the attention mask count as consumed tokens.
    """

    total = 0
    for batch in batches:
        masks = list(batch["attention_mask"])
        origins = list(batch["origins"])
        if len(masks) != len(origins):
            raise ValueError("attention_mask and origins must have the same batch size")
        for mask, example_origin in zip(masks, origins, strict=True):
            # Validate every row, not only rows matching the origin filter.
            # Previously this lived inside the filter, so a malformed mask on a
            # synthetic row was invisible to a human-origin count.
            if any(value not in (0, 1) for value in mask):
                raise ValueError("attention_mask values must be zero or one")
            if origin is None or example_origin == origin:
                total += sum(mask)
    return total


def validate_matched_budgets(
    condition_batches: dict[str, Iterable[dict[str, Any]]],
) -> tuple[int, int]:
    """Require every condition to consume equal human and total tokens.

    This is the fairness constraint of ``PROTOCOL.md`` §4, so it must fail loudly
    rather than pass vacuously. Two ways it previously could not:

    - Each condition was iterated **twice** (once for human tokens, once for the
      total). A generator or any other single-pass iterable was exhausted by the
      first call, so the second counted zero — and two conditions with different
      real budgets both reported ``(n, 0)`` and compared equal.
    - A single condition trivially "matched", having compared nothing.
    """

    if len(condition_batches) < 2:
        raise ValueError(
            "budget matching compares conditions against each other and needs at "
            f"least two; got {len(condition_batches)}: {sorted(condition_batches)}"
        )

    # Materialize once so each condition can be counted twice.
    materialized = {
        condition: list(batches) for condition, batches in condition_batches.items()
    }
    counts = {
        condition: (consumed_tokens(batches, origin="human"), consumed_tokens(batches))
        for condition, batches in materialized.items()
    }
    unique = set(counts.values())
    if len(unique) != 1:
        raise ValueError(f"budget mismatch across conditions: {counts}")
    return next(iter(unique))
