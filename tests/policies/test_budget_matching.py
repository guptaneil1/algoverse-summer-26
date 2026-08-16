"""Compared conditions must consume exactly equal human-origin and total tokens."""

import pytest

from human_data_budget.data.token_accounting import consumed_tokens, validate_matched_budgets

CONDITIONS = ("random", "schedule_only", "selection_only", "joint")


def batch(human_masks: list[list[int]], synthetic_masks: list[list[int]]) -> dict[str, object]:
    return {
        "attention_mask": [*human_masks, *synthetic_masks],
        "origins": ["human"] * len(human_masks) + ["synthetic"] * len(synthetic_masks),
    }


def matched_batch() -> dict[str, object]:
    return batch([[1, 1, 1, 0]], [[1, 1, 0, 0]])


def test_all_four_conditions_match() -> None:
    conditions = {name: [matched_batch()] for name in CONDITIONS}
    assert validate_matched_budgets(conditions) == (3, 5)


def test_human_token_mismatch_is_rejected() -> None:
    conditions = {name: [matched_batch()] for name in CONDITIONS}
    conditions["joint"] = [batch([[1, 1, 1, 1]], [[1, 0, 0, 0]])]
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets(conditions)


def test_total_token_mismatch_is_rejected() -> None:
    conditions = {name: [matched_batch()] for name in CONDITIONS}
    conditions["schedule_only"] = [batch([[1, 1, 1, 0]], [[1, 1, 1, 0]])]
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets(conditions)


def test_padding_is_never_counted_as_a_consumed_token() -> None:
    padded = batch([[1, 1, 0, 0, 0, 0]], [])
    assert consumed_tokens([padded]) == 2
    assert consumed_tokens([padded], origin="human") == 2


def test_repeated_human_exposure_counts_every_presentation() -> None:
    """The same example shown twice consumes budget twice."""
    once = batch([[1, 1, 1, 0]], [])
    twice = [once, batch([[1, 1, 1, 0]], [])]
    assert consumed_tokens(twice, origin="human") == 2 * consumed_tokens([once], origin="human")


def test_split_batches_accumulate_like_one_batch() -> None:
    """Gradient accumulation must not change the recorded totals."""
    single = batch([[1, 1, 1, 0], [1, 1, 0, 0]], [])
    split = [batch([[1, 1, 1, 0]], []), batch([[1, 1, 0, 0]], [])]
    assert consumed_tokens(split) == consumed_tokens([single])


def test_synthetic_tokens_are_excluded_from_the_human_ledger() -> None:
    mixed = batch([[1, 1, 0, 0]], [[1, 1, 1, 1]])
    assert consumed_tokens([mixed], origin="human") == 2
    assert consumed_tokens([mixed]) == 6


def test_invalid_mask_value_is_rejected() -> None:
    corrupt = {"attention_mask": [[1, 2, 0]], "origins": ["human"]}
    with pytest.raises(ValueError, match="attention_mask values must be zero or one"):
        consumed_tokens([corrupt])


def test_mask_and_origin_length_mismatch_is_rejected() -> None:
    corrupt = {"attention_mask": [[1, 1], [1, 0]], "origins": ["human"]}
    with pytest.raises(ValueError, match="same batch size"):
        consumed_tokens([corrupt])


def test_a_single_condition_is_rejected_rather_than_trivially_matched() -> None:
    """One condition compared nothing, so it must not report success.

    This asserted the opposite — that a lone condition returns `(3, 5)`. That was
    the defect: budget matching is the fairness constraint of `PROTOCOL.md` §4, and
    a check that passes having compared nothing is the shape of a constraint that
    can never fail. `data/token_accounting.py` was fixed to raise, and
    `tests/data/test_token_accounting.py::test_a_single_condition_cannot_match_itself`
    already pins the corrected contract; this test still encoded the old one.
    """
    with pytest.raises(ValueError, match="at least two"):
        validate_matched_budgets({"joint": [matched_batch()]})
