"""CPU tests for the real held-out evaluator.

Scoring needs a checkpoint and a model stack, so only the pure paths run here.
The orientation test is the important one: it pins the direction the frozen
tail-retention metric depends on, which F-011 records as currently inconsistent
between tail.py's semantics and the metric freeze document.
"""

from __future__ import annotations

import pytest

from human_data_budget.evaluation.real import mode_nll_to_retention_scores
from human_data_budget.evaluation.tail import tail_retention


def test_worse_nll_yields_a_lower_score() -> None:
    scores = mode_nll_to_retention_scores({"tail": 2.0, "common": 4.0})
    assert scores["tail"] > scores["common"]


def test_a_degraded_model_scores_below_one_after_transform() -> None:
    """The property the transform exists to restore.

    Feeding NLL straight into tail_retention gives current/reference above 1 for a
    degraded model, which clips to 1.0 and reports perfect retention for the worst
    case. Transformed first, degradation lands below 1.0 as intended.
    """
    reference_nll, degraded_nll = {"tail": 2.0}, {"tail": 4.0}

    naive = tail_retention(degraded_nll, reference_nll, {"tail"})
    assert naive == 1.0, "raw NLL clips to 1.0 for a degraded model -- see F-011"

    corrected = tail_retention(
        mode_nll_to_retention_scores(degraded_nll),
        mode_nll_to_retention_scores(reference_nll),
        {"tail"},
    )
    assert corrected == pytest.approx(0.5)


def test_an_improved_model_is_capped_at_one() -> None:
    reference, improved = {"tail": 4.0}, {"tail": 2.0}
    value = tail_retention(
        mode_nll_to_retention_scores(improved),
        mode_nll_to_retention_scores(reference),
        {"tail"},
    )
    assert value == 1.0


def test_zero_nll_does_not_divide_by_zero() -> None:
    assert mode_nll_to_retention_scores({"tail": 0.0})["tail"] == pytest.approx(1e6)


def test_scoring_rejects_an_empty_example_set() -> None:
    from human_data_budget.evaluation.real import score_examples
    with pytest.raises(ValueError, match="no examples"):
        score_examples("/nonexistent/checkpoint", [])
