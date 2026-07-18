import pytest

from human_data_budget.data.token_accounting import consumed_tokens, validate_matched_budgets


def batch() -> dict[str, object]:
    return {
        "attention_mask": [[1, 1, 1, 0], [1, 1, 0, 0]],
        "origins": ["human", "synthetic"],
    }


def test_counts_realized_non_padding_tokens() -> None:
    assert consumed_tokens([batch()]) == 5
    assert consumed_tokens([batch()], origin="human") == 3


def test_matched_conditions_pass() -> None:
    assert validate_matched_budgets({"joint": [batch()], "random": [batch()]}) == (3, 5)


def test_mismatched_conditions_fail() -> None:
    short = {"attention_mask": [[1]], "origins": ["human"]}
    with pytest.raises(ValueError, match="budget mismatch"):
        validate_matched_budgets({"joint": [batch()], "random": [short]})
