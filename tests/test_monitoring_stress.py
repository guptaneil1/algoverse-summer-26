"""Monitoring-omission stress test on fixtures.

Implements the `docs/weekly/WEEK_3.md` Aarav clause "Run monitoring-bias stress
test", at the only level currently possible: the fixture simulator. Before this
file, ``hidden_modes`` had no call site anywhere outside its own definition in
``analysis/simulator.py`` — the C-003 intervention was implemented but never
exercised.

**This is not evidence for C-003.** No language model is trained here. The
simulator's degradation and rescue rates are chosen constants, so the effect size
below is a property of those constants, not of language. What these tests
establish is narrower and still worth having: the intervention is wired
end-to-end, it moves outcomes in the predicted direction, and it does so without
breaking budget matching — so the real experiment can use it.

C-003 states: *the advantage of targeted allocation decreases or reverses when
the monitoring reference omits globally important modes.* In this fixture the
effect is a reversal, not merely a decrease.
"""

from __future__ import annotations

import pytest

from human_data_budget.analysis.metrics import regret_auc
from human_data_budget.analysis.simulator import POLICY_NAMES, simulate_policy

HIDE_TAIL = frozenset({"tail"})

# Policies that read mode_statistics to choose *what* to rescue. These are the
# ones a biased monitor can mislead.
TARGETING_POLICIES = ("selection_only", "joint")
# Policies that ignore mode identity. A biased monitor cannot reach them.
UNTARGETED_POLICIES = ("random", "schedule_only")


def auc(policy: str, hidden: frozenset[str], seed: int = 1) -> float:
    run = simulate_policy(policy, chain_seed=seed, hidden_modes=hidden)
    return regret_auc([metric["human_nll"] for metric in run["chain_result"]["metrics"]])


def test_hidden_mode_is_removed_from_policy_visible_state() -> None:
    """The omitted mode must not appear in any allocation the policy made."""
    run = simulate_policy("joint", chain_seed=1, hidden_modes=HIDE_TAIL)
    assert run["hidden_modes"] == ["tail"]
    for step in run["allocations"]:
        assert "tail" not in step["mode_allocations"], (
            "a hidden mode was still allocated to, so the monitor was not actually blinded"
        )


def test_hidden_mode_still_degrades_in_the_true_state() -> None:
    """Hiding a mode from the monitor must not hide it from reality.

    If omission also removed the mode from evaluation, the stress test would be
    measuring nothing — the policy would be rewarded for ignoring it.
    """
    blinded = simulate_policy("joint", chain_seed=1, hidden_modes=HIDE_TAIL)
    retention = [metric["tail_retention"] for metric in blinded["chain_result"]["metrics"]]
    assert retention[-1] < retention[0], "tail must still decay when unmonitored"


@pytest.mark.parametrize("policy", UNTARGETED_POLICIES)
def test_untargeted_policies_are_unaffected_by_monitor_bias(policy: str) -> None:
    """Policies that ignore mode identity cannot be misled by an omission."""
    assert auc(policy, frozenset()) == auc(policy, HIDE_TAIL)


@pytest.mark.parametrize("policy", TARGETING_POLICIES)
def test_targeting_policies_are_harmed_by_monitor_bias(policy: str) -> None:
    """The C-003 direction: omission makes targeted allocation worse."""
    assert auc(policy, HIDE_TAIL) > auc(policy, frozenset()), (
        f"{policy} should lose regret advantage when the tail mode is unmonitored"
    )


def test_advantage_reverses_rather_than_merely_shrinking() -> None:
    """Under omission, targeting is beaten by the untargeted baseline.

    Visible monitor: targeting wins. Biased monitor: targeting loses. That
    crossover is the failure boundary the intervention is designed to expose.
    """
    targeted_visible = auc("joint", frozenset())
    untargeted_visible = auc("schedule_only", frozenset())
    targeted_blinded = auc("joint", HIDE_TAIL)
    untargeted_blinded = auc("schedule_only", HIDE_TAIL)

    assert targeted_visible < untargeted_visible, "targeting should win with a full monitor"
    assert targeted_blinded > untargeted_blinded, "targeting should lose with a biased monitor"


@pytest.mark.parametrize("policy", POLICY_NAMES)
def test_budget_matching_survives_monitoring_omission(policy: str) -> None:
    """Omission must change *where* tokens go, never *how many* are spent.

    If a biased monitor also changed the lifetime spend, the stress test would
    confound monitor quality with budget size and could not isolate either.
    """
    visible = simulate_policy(policy, chain_seed=1)["chain_result"]
    blinded = simulate_policy(policy, chain_seed=1, hidden_modes=HIDE_TAIL)["chain_result"]

    assert visible["consumed_human_tokens"] == blinded["consumed_human_tokens"]
    assert visible["consumed_total_tokens"] == blinded["consumed_total_tokens"]


def test_omission_effect_is_stable_across_seeds() -> None:
    """The direction must not depend on one lucky seed."""
    for seed in range(1, 6):
        assert auc("joint", HIDE_TAIL, seed=seed) > auc("joint", frozenset(), seed=seed)
