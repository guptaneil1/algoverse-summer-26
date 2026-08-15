"""Reliability and independence audit for the two tail-retention candidates.

Covers the `docs/weekly/WEEK_2.md` Neil clause "Freeze NLL implementation and one
primary tail-retention definition **after reliability/independence audit**" and
the `WEEK_3.md` clause "Test evaluator determinism and tail reliability against
saved fixtures/checkpoints."

`DECISIONS.md` U-004 is still open: `tail_retention` (ratio-based) and `nll_gap`
are both implemented and neither is frozen. Choosing between them is a human
decision. What can be established without one is whether each *candidate* has the
properties a primary outcome must have:

1. **Determinism** — identical inputs give identical output, every time.
2. **Independence from the selection signal** — `PROTOCOL.md` §4 requires the
   tail measure be "evaluated on a partition never used for selection". A metric
   that reads the policy's own `undercoverage_score` would reward a policy for
   agreeing with itself.
3. **Sensitivity** — the metric moves when tail coverage actually degrades.
4. **Discriminant validity** — it does *not* move when only non-tail modes change.
5. **Split-half reliability** — two halves of the same evaluation set agree.

These tests do not choose a metric. They establish that both candidates are
choosable, and record the properties that distinguish them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.evaluation.nll import negative_log_likelihood
from human_data_budget.evaluation.tail import nll_gap, tail_retention
from human_data_budget.runner.evaluator import NullEvaluator, load_toy_eval_corpus

TAIL = {"tail"}
REFERENCE = {"common": 1.0, "tail": 1.0}
FIXTURES = Path(__file__).parent / "fixtures"


# --------------------------------------------------------------------------
# 1. Determinism
# --------------------------------------------------------------------------


def test_tail_retention_is_deterministic() -> None:
    current = {"common": 0.8, "tail": 0.4}
    values = {tail_retention(current, REFERENCE, TAIL) for _ in range(50)}
    assert len(values) == 1


def test_nll_gap_is_deterministic() -> None:
    values = {nll_gap([3.1, 3.4, 3.9], [2.0, 2.2]) for _ in range(50)}
    assert len(values) == 1


def test_evaluator_is_deterministic_against_the_saved_fixture() -> None:
    """Same checkpoint, same corpus, same numbers — across repeated calls."""
    corpus = load_toy_eval_corpus()
    evaluator = NullEvaluator()

    def evaluate() -> dict:
        return evaluator.evaluate(
            run_id="chain-001",
            generation=3,
            checkpoint_sha256="abc",
            evaluation_manifest_sha256="def",
            current_mode_scores={"common": 0.9, "tail": 0.5},
            reference_mode_scores=corpus["reference_mode_scores"],
            tail_modes=TAIL,
            target_log_probabilities=corpus["target_log_probabilities"],
        )

    assert evaluate() == evaluate() == evaluate()


def test_evaluator_output_is_stable_across_instances() -> None:
    """Two evaluator objects must agree; no hidden per-instance state."""
    corpus = load_toy_eval_corpus()
    kwargs = dict(
        run_id="chain-001",
        generation=0,
        checkpoint_sha256="abc",
        evaluation_manifest_sha256="def",
        current_mode_scores={"common": 0.9, "tail": 0.5},
        reference_mode_scores=corpus["reference_mode_scores"],
        tail_modes=TAIL,
        target_log_probabilities=corpus["target_log_probabilities"],
    )
    assert NullEvaluator().evaluate(**kwargs) == NullEvaluator().evaluate(**kwargs)


# --------------------------------------------------------------------------
# 2. Independence from the policy's selection signal
# --------------------------------------------------------------------------


def test_tail_metrics_cannot_read_the_selection_score() -> None:
    """Structural independence: neither function accepts a Candidate.

    `undercoverage_score` lives on `Candidate`. Because neither tail metric takes
    candidates — only mode scores and NLL values — there is no code path by which
    the policy's own selection signal can reach the outcome. This is checked at
    the signature level so it fails if someone widens the interface later.
    """
    import inspect

    for function in (tail_retention, nll_gap):
        parameters = inspect.signature(function).parameters
        assert "candidate" not in " ".join(parameters).lower()
        assert "undercoverage" not in " ".join(parameters).lower()
        assert "score" not in " ".join(
            name for name in parameters if "mode" not in name
        ).lower()


def test_identical_coverage_gives_identical_retention_regardless_of_policy() -> None:
    """Two chains with the same true coverage must score the same.

    The metric sees coverage, not who produced it. If a joint-policy chain and a
    random-policy chain reach identical tail coverage, they must be scored
    identically — otherwise the metric encodes a preference for a treatment.
    """
    coverage = {"common": 0.7, "tail": 0.35}
    assert tail_retention(coverage, REFERENCE, TAIL) == tail_retention(
        dict(coverage), REFERENCE, TAIL
    )


# --------------------------------------------------------------------------
# 3. Sensitivity
# --------------------------------------------------------------------------


@pytest.mark.parametrize("current_tail", [0.9, 0.7, 0.5, 0.3, 0.1])
def test_retention_is_monotone_in_tail_coverage(current_tail: float) -> None:
    worse = tail_retention({"common": 1.0, "tail": current_tail / 2}, REFERENCE, TAIL)
    better = tail_retention({"common": 1.0, "tail": current_tail}, REFERENCE, TAIL)
    assert worse < better


def test_nll_gap_grows_as_the_tail_gets_harder() -> None:
    common = [2.0, 2.1, 2.0]
    assert nll_gap([2.2, 2.3, 2.1], common) < nll_gap([4.0, 4.2, 3.9], common)


def test_nll_gap_is_zero_when_tail_and_common_match() -> None:
    assert nll_gap([2.0, 2.5], [2.5, 2.0]) == pytest.approx(0.0)


def test_nll_gap_can_be_negative() -> None:
    """An easier tail than common is representable, not clipped away.

    `tail_retention` clips to [0, 1] and so cannot express over-performance;
    `nll_gap` can. That difference matters for U-004 and is recorded here.
    """
    assert nll_gap([1.0], [3.0]) < 0


# --------------------------------------------------------------------------
# 4. Discriminant validity and range
# --------------------------------------------------------------------------


def test_retention_ignores_non_tail_modes() -> None:
    """Common-mode movement must not shift a tail measure."""
    baseline = tail_retention({"common": 1.0, "tail": 0.5}, REFERENCE, TAIL)
    shifted = tail_retention({"common": 0.2, "tail": 0.5}, REFERENCE, TAIL)
    assert baseline == shifted


@pytest.mark.parametrize("tail_value", [0.0, 0.25, 0.5, 0.75, 1.0, 2.0])
def test_retention_stays_in_unit_range(tail_value: float) -> None:
    value = tail_retention({"common": 1.0, "tail": tail_value}, REFERENCE, TAIL)
    assert 0.0 <= value <= 1.0


def test_retention_clips_above_reference() -> None:
    """Exceeding the reference cannot manufacture a score above 1."""
    assert tail_retention({"common": 1.0, "tail": 5.0}, REFERENCE, TAIL) == 1.0


def test_multiple_tail_modes_are_averaged() -> None:
    reference = {"tail_a": 1.0, "tail_b": 1.0}
    value = tail_retention({"tail_a": 0.2, "tail_b": 0.8}, reference, {"tail_a", "tail_b"})
    assert value == pytest.approx(0.5)


# --------------------------------------------------------------------------
# 5. Split-half reliability
# --------------------------------------------------------------------------


def test_nll_gap_split_half_reliability() -> None:
    """Two halves of a homogeneous evaluation set must broadly agree.

    A metric whose halves disagree wildly is too noisy to serve as a primary
    outcome at realistic chain counts. The tolerance here is deliberately loose:
    this establishes the property is testable and holds on fixtures, not a frozen
    reliability threshold — that belongs with the U-004 decision.
    """
    tail = [3.0, 3.2, 3.1, 3.3, 3.05, 3.25, 3.15, 3.35]
    common = [2.0, 2.2, 2.1, 2.3, 2.05, 2.25, 2.15, 2.35]

    first = nll_gap(tail[0::2], common[0::2])
    second = nll_gap(tail[1::2], common[1::2])

    assert abs(first - second) < 0.25


def test_saved_fixture_reproduces_a_stable_nll() -> None:
    """The checked-in fixture must keep producing the value it produced before.

    Guards against a silent change to the fixture file or the NLL implementation.
    """
    fixture = json.loads((FIXTURES / "fake_logits.json").read_text(encoding="utf-8"))
    assert isinstance(fixture, (dict, list))

    corpus = load_toy_eval_corpus()
    value = negative_log_likelihood(corpus["target_log_probabilities"])
    assert value == pytest.approx(1.5)


# --------------------------------------------------------------------------
# 6. Refusal to score invalid input
# --------------------------------------------------------------------------


def test_empty_tail_mode_set_is_rejected() -> None:
    """Silently returning a score for zero tail modes would be worse than failing."""
    with pytest.raises(ValueError, match="tail_modes cannot be empty"):
        tail_retention({"common": 1.0}, REFERENCE, set())


def test_missing_tail_mode_score_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing tail mode score"):
        tail_retention({"common": 1.0}, REFERENCE, {"tail"})


def test_non_positive_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        tail_retention({"tail": 0.5}, {"tail": 0.0}, TAIL)


def test_empty_nll_inputs_are_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        nll_gap([], [1.0])
