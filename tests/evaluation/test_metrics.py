import pytest

from human_data_budget.evaluation.nll import negative_log_likelihood
from human_data_budget.evaluation.tail import tail_retention


def test_nll() -> None:
    assert negative_log_likelihood([-1.0, -2.0, -3.0]) == 2.0


def test_positive_log_probability_rejected() -> None:
    with pytest.raises(ValueError):
        negative_log_likelihood([-1.0, 0.1])


def test_tail_retention() -> None:
    value = tail_retention({"rare": 0.5}, {"rare": 1.0}, {"rare"})
    assert value == 0.5
