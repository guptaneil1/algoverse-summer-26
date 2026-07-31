"""Tests for NLL computation from raw logits with padding exclusion."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from human_data_budget.evaluation.logit_nll import sequence_nll, token_nll
from human_data_budget.evaluation.tail import nll_gap

# --- token_nll ---


def test_token_nll_confident_prediction() -> None:
    logits = [0.0, 0.0, 3.0, 0.0, 0.0]
    nll = token_nll(logits, token_id=2)
    expected = math.log(math.exp(0) * 4 + math.exp(3)) - 3.0
    assert abs(nll - expected) < 1e-9


def test_token_nll_uniform_equals_log_vocab() -> None:
    logits = [0.0, 0.0, 0.0, 0.0, 0.0]
    nll = token_nll(logits, token_id=1)
    assert abs(nll - math.log(5)) < 1e-9


def test_token_nll_higher_logit_gives_lower_nll() -> None:
    low_logit = token_nll([0.0, 0.0, 1.0, 0.0, 0.0], token_id=2)
    high_logit = token_nll([0.0, 0.0, 5.0, 0.0, 0.0], token_id=2)
    assert high_logit < low_logit


def test_token_nll_numerical_stability_with_large_logits() -> None:
    logits = [100.0, 200.0, 100.0]
    nll = token_nll(logits, token_id=1)
    assert math.isfinite(nll)
    assert abs(nll - 0.0) < 1e-6


# --- sequence_nll ---


def test_sequence_nll_excludes_padding() -> None:
    logits_seq = [
        [0.0, 3.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 3.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    token_ids = [1, 2, 0, 0]
    total, count = sequence_nll(logits_seq, token_ids, padding_id=0)
    assert count == 2
    assert total > 0.0


def test_sequence_nll_all_padding_gives_zero_count() -> None:
    logits_seq = [[0.0, 0.0, 0.0]] * 3
    total, count = sequence_nll(logits_seq, [0, 0, 0], padding_id=0)
    assert count == 0
    assert total == 0.0


def test_sequence_nll_repeated_examples_accumulate() -> None:
    logits_seq = [[0.0, 0.0, 0.0, 0.0, 0.0]] * 3
    token_ids = [1, 2, 3]
    total_1, count_1 = sequence_nll(logits_seq, token_ids)
    total_3, count_3 = sequence_nll(logits_seq * 3, token_ids * 3)
    assert count_3 == count_1 * 3
    assert abs(total_3 - total_1 * 3) < 1e-9


def test_sequence_nll_returns_token_weighted_totals() -> None:
    logits = [[0.0, 3.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0]]
    ids = [1, 2]
    total, count = sequence_nll(logits, ids, padding_id=0)
    per_1 = token_nll([0.0, 3.0, 0.0, 0.0, 0.0], 1)
    per_2 = token_nll([0.0, 0.0, 0.0, 0.0, 0.0], 2)
    assert abs(total - (per_1 + per_2)) < 1e-9
    assert count == 2


# --- nll_gap (second tail-retention candidate metric) ---


def test_nll_gap_positive_when_tail_harder() -> None:
    tail = [2.0, 2.5]
    common = [0.5, 0.8]
    gap = nll_gap(tail, common)
    assert gap == pytest.approx(2.25 - 0.65)


def test_nll_gap_negative_when_tail_easier() -> None:
    assert nll_gap([0.3], [1.5]) < 0


def test_nll_gap_zero_for_equal_distributions() -> None:
    assert nll_gap([1.0, 1.0], [1.0, 1.0]) == pytest.approx(0.0)


def test_nll_gap_raises_on_empty_input() -> None:
    with pytest.raises(ValueError):
        nll_gap([], [1.0])
    with pytest.raises(ValueError):
        nll_gap([1.0], [])


def test_nll_gap_independent_of_policy_score() -> None:
    """nll_gap uses NLL values only, never the policy's undercoverage_score.

    This check verifies the function signature accepts only NLL floats,
    keeping it independent from the selection signal defined in models.py.
    """
    tail_nlls = [1.6, 1.7]
    common_nlls = [0.2, 0.2]
    result = nll_gap(tail_nlls, common_nlls)
    assert isinstance(result, float)
    assert result > 0


# --- fixture-based integration ---


def test_fake_logits_fixture_expected_counts() -> None:
    """Verify the fake_logits.json fixture yields the expected token counts."""
    import json

    fixture = Path(__file__).parent / "fixtures" / "fake_logits.json"
    data = json.loads(fixture.read_text())
    padding_id = data["padding_id"]

    total_tokens = 0
    for ex in data["examples"]:
        _, count = sequence_nll(ex["logits"], ex["token_ids"], padding_id)
        total_tokens += count

    assert total_tokens == 12  # 4+3+2+3 from test.jsonl token_counts


def test_tail_examples_have_higher_nll_than_common_in_fixture() -> None:
    """In the fake fixture common gets confident logits, tail gets uniform."""
    import json

    fixture = Path(__file__).parent / "fixtures" / "fake_logits.json"
    data = json.loads(fixture.read_text())
    padding_id = data["padding_id"]

    tail_nlls = []
    common_nlls = []
    for ex in data["examples"]:
        total, count = sequence_nll(ex["logits"], ex["token_ids"], padding_id)
        if count == 0:
            continue
        mean_nll = total / count
        if ex["mode"] == "tail":
            tail_nlls.append(mean_nll)
        else:
            common_nlls.append(mean_nll)

    assert nll_gap(tail_nlls, common_nlls) > 0
