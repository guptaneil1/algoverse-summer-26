"""The frozen tail metric is deterministic, directional, and selection-independent."""

import pytest

from human_data_budget.evaluation.tail import nll_gap, tail_retention

REFERENCE = {"tail_a": 1.0, "tail_b": 2.0, "common": 8.0}
TAIL_MODES = {"tail_a", "tail_b"}


def test_full_coverage_scores_one() -> None:
    assert tail_retention(REFERENCE, REFERENCE, TAIL_MODES) == 1.0


def test_total_loss_scores_zero() -> None:
    collapsed = {"tail_a": 0.0, "tail_b": 0.0, "common": 8.0}
    assert tail_retention(collapsed, REFERENCE, TAIL_MODES) == 0.0


def test_metric_is_deterministic() -> None:
    current = {"tail_a": 0.5, "tail_b": 1.0, "common": 8.0}
    first = tail_retention(current, REFERENCE, TAIL_MODES)
    second = tail_retention(current, REFERENCE, TAIL_MODES)
    assert first == second


def test_metric_is_directional_on_controlled_fixtures() -> None:
    worse = {"tail_a": 0.2, "tail_b": 0.4, "common": 8.0}
    better = {"tail_a": 0.8, "tail_b": 1.6, "common": 8.0}
    assert tail_retention(worse, REFERENCE, TAIL_MODES) < tail_retention(
        better, REFERENCE, TAIL_MODES
    )


def test_result_stays_within_unit_interval() -> None:
    overshoot = {"tail_a": 50.0, "tail_b": 50.0, "common": 8.0}
    assert tail_retention(overshoot, REFERENCE, TAIL_MODES) == 1.0


def test_common_modes_do_not_affect_the_tail_score() -> None:
    """The metric must read only the frozen tail modes."""
    shifted = {"tail_a": 0.5, "tail_b": 1.0, "common": 0.0001}
    baseline = {"tail_a": 0.5, "tail_b": 1.0, "common": 8.0}
    assert tail_retention(shifted, REFERENCE, TAIL_MODES) == tail_retention(
        baseline, REFERENCE, TAIL_MODES
    )


def test_mode_ordering_does_not_change_the_score() -> None:
    current = {"tail_b": 1.0, "tail_a": 0.5, "common": 8.0}
    reversed_reference = {"tail_b": 2.0, "tail_a": 1.0, "common": 8.0}
    assert tail_retention(current, reversed_reference, TAIL_MODES) == pytest.approx(0.5)


def test_empty_tail_modes_is_rejected() -> None:
    with pytest.raises(ValueError, match="tail_modes cannot be empty"):
        tail_retention(REFERENCE, REFERENCE, set())


def test_missing_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing tail mode score"):
        tail_retention({"tail_a": 1.0}, REFERENCE, TAIL_MODES)


def test_non_positive_reference_is_rejected() -> None:
    zero_reference = {"tail_a": 0.0, "tail_b": 2.0}
    with pytest.raises(ValueError, match="reference tail scores must be positive"):
        tail_retention({"tail_a": 1.0, "tail_b": 1.0}, zero_reference, TAIL_MODES)


def test_nll_gap_is_positive_when_tail_is_harder() -> None:
    assert nll_gap([5.0, 5.0], [2.0, 2.0]) == pytest.approx(3.0)


def test_nll_gap_is_negative_when_tail_is_easier() -> None:
    assert nll_gap([1.0], [4.0]) == pytest.approx(-3.0)


def test_nll_gap_rejects_empty_inputs() -> None:
    with pytest.raises(ValueError, match="must be non-empty"):
        nll_gap([], [1.0])
