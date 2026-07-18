import pytest

from human_data_budget.analysis.metrics import paired_difference, regret_auc


def test_trapezoidal_auc() -> None:
    assert regret_auc([0.0, 1.0, 2.0]) == 2.0


def test_paired_difference() -> None:
    assert paired_difference({1: 2.0, 2: 4.0}, {1: 1.5, 2: 3.0}) == {1: 0.5, 2: 1.0}


def test_unpaired_seeds_fail() -> None:
    with pytest.raises(ValueError, match="same chain seeds"):
        paired_difference({1: 2.0}, {2: 2.0})
