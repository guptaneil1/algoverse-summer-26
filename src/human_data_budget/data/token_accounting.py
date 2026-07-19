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
        masks = batch["attention_mask"]
        origins = batch["origins"]
        if len(masks) != len(origins):
            raise ValueError("attention_mask and origins must have the same batch size")
        for mask, example_origin in zip(masks, origins, strict=True):
            if origin is None or example_origin == origin:
                if any(value not in (0, 1) for value in mask):
                    raise ValueError("attention_mask values must be zero or one")
                total += sum(mask)
    return total


def validate_matched_budgets(
    condition_batches: dict[str, Iterable[dict[str, Any]]],
) -> tuple[int, int]:
    """Require every condition to consume equal human and total tokens."""

    counts = {
        condition: (consumed_tokens(batches, origin="human"), consumed_tokens(batches))
        for condition, batches in condition_batches.items()
    }
    unique = set(counts.values())
    if len(unique) != 1:
        raise ValueError(f"budget mismatch across conditions: {counts}")
    return next(iter(unique))
