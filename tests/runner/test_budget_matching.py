"""Realised budget-matching check.

The property under test is the one FAILURE_LOG.md F-016 records as unguarded: the
earlier check demanded exact equality across every chain, which no configuration
containing a control arm could satisfy, and nothing asserted that it could ever
pass. These tests pin both directions -- the frozen grid's realised spread holds,
and F-015's historical numbers still fail.
"""

from __future__ import annotations

import json

import pytest

from human_data_budget.policies import spends_human_tokens
from human_data_budget.runner.budget_matching import (
    SPREAD_MARGIN_BELOW_THRESHOLD,
    check_realised_budget_matching,
    max_candidate_optimizer_tokens,
)

CEILING = 750_000
THRESHOLD = 0.02
# The pilot's frozen rescue pool: 4,235 candidates, largest 26,902 optimizer tokens.
BOUND = 26_902


def check(chains, *, bound=BOUND, ceiling=CEILING, threshold=THRESHOLD):
    return check_realised_budget_matching(
        chains,
        lifetime_human_budget=ceiling,
        indivisibility_bound=bound,
        practical_effect_threshold_relative=threshold,
        is_spending_arm=spends_human_tokens,
    )


def chain(arm, seed, spent):
    return {"arm": arm, "seed": seed, "consumed_human_tokens": spent, "status": "complete"}


# The realised spend of the frozen pilot grid, measured by a dry run of
# configs/experiment/primary_pilot.json on 2026-08-18.
FROZEN_GRID = (
    [chain("no_rescue", seed, 0) for seed in (101, 202, 303, 404, 505)]
    + [chain("random", seed, spent) for seed, spent in
       ((101, 749_757), (202, 749_915), (303, 749_873), (404, 749_830), (505, 749_970))]
    + [chain("schedule_only", seed, spent) for seed, spent in
       ((101, 749_913), (202, 749_709), (303, 749_890), (404, 749_995), (505, 749_882))]
    + [chain("selection_only", seed, 749_866) for seed in (101, 202, 303, 404, 505)]
    + [chain("joint", seed, 749_844) for seed in (101, 202, 303, 404, 505)]
)


def test_frozen_pilot_grid_holds():
    """The grid the pilot will actually launch must pass, or it cannot launch."""
    report = check(FROZEN_GRID)
    assert report.ok, report.render()
    assert report.spending_spread_relative == pytest.approx(0.000381, abs=1e-5)


def test_control_arm_zero_does_not_violate():
    """no_rescue spends nothing by construction; that is the reference, not a defect.

    The earlier guard compared the control's zero against the spending arms and so
    could never pass. This is the regression that matters.
    """
    report = check([chain("no_rescue", 101, 0), chain("joint", 101, 749_844)])
    assert report.ok, report.render()


def test_f015_historical_spread_still_fails():
    """F-015's realised numbers must not pass the replacement check.

    Re-specifying the constraint is only defensible if it still rejects what it was
    written to reject. These are the values FAILURE_LOG.md F-015 recorded.
    """
    report = check([
        chain("no_rescue", 101, 0),
        chain("schedule_only", 101, 517_000),
        chain("selection_only", 101, 574_731),
        chain("random", 101, 580_000),
        chain("joint", 101, 641_002),
    ])
    assert not report.ok
    assert any("short of the" in failure for failure in report.failures)
    assert any("not separable from the effect" in failure for failure in report.failures)


def test_shortfall_within_one_candidate_passes():
    """A gap indivisibility explains is not a violation."""
    report = check([chain("joint", 101, CEILING - BOUND)])
    assert report.ok, report.render()


def test_shortfall_beyond_one_candidate_fails():
    """A gap one candidate cannot explain is."""
    report = check([chain("joint", 101, CEILING - BOUND - 1)])
    assert not report.ok
    assert "short of the" in report.failures[0]


def test_overspend_is_a_hard_failure():
    """Exceeding the ceiling is never rounding."""
    report = check([chain("joint", 101, CEILING + 1)])
    assert not report.ok
    assert "over the" in report.failures[0]


def test_control_arm_that_spends_is_a_failure():
    """A control that started spending has stopped being a control."""
    report = check([chain("no_rescue", 101, 12)])
    assert not report.ok
    assert "spends nothing by construction" in report.failures[0]


def test_spread_at_the_permitted_margin_passes():
    """The boundary is inclusive, and tied to the config's own threshold."""
    permitted = THRESHOLD * SPREAD_MARGIN_BELOW_THRESHOLD
    low = round(CEILING * (1 - permitted))
    report = check([chain("joint", 101, CEILING), chain("random", 101, low)],
                   bound=CEILING)
    assert report.ok, report.render()


def test_spread_beyond_the_permitted_margin_fails():
    """Two arms can each sit within one candidate of the ceiling and still differ too
    much, if the pool's largest candidate is itself large relative to the budget."""
    permitted = THRESHOLD * SPREAD_MARGIN_BELOW_THRESHOLD
    low = round(CEILING * (1 - permitted)) - 500
    report = check([chain("joint", 101, CEILING), chain("random", 101, low)],
                   bound=CEILING)
    assert not report.ok
    assert any("not separable" in failure for failure in report.failures)


def test_no_completed_chains_is_a_failure():
    """An empty grid must not read as a clean pass."""
    assert not check([]).ok


def test_unknown_arm_is_refused():
    """An unclassified policy must not be silently exempted or silently held."""
    with pytest.raises(ValueError, match="unknown policy"):
        check([chain("mystery_policy", 101, 749_844)])


def test_indivisibility_bound_matches_the_frozen_manifest():
    """The bound is read from the frozen pool, not hardcoded in the checker."""
    bound = max_candidate_optimizer_tokens("data/manifests/rescue_candidates.jsonl")
    assert bound == BOUND


def test_bound_refuses_a_manifest_without_token_counts(tmp_path):
    """F-010b: a manifest counting words yields a bound in the wrong currency."""
    path = tmp_path / "no_tokens.jsonl"
    path.write_text(
        json.dumps({"example_id": "x", "token_count": 3772}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="optimizer_token_count"):
        max_candidate_optimizer_tokens(path)
