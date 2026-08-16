"""The four treatment families are observationally distinguishable.

Replaces `tests/policies/test_joint_degeneracy.py`, which pinned the opposite.

That file was written on 2026-08-15 to record `FAILURE_LOG.md` F-001: "JointPolicy
is observationally identical to SelectionOnlyPolicy, and RandomPolicy to
ScheduleOnlyPolicy". F-001 says of those tests: *"Those tests are expected to fail
when the real rule lands, and should be deleted then."*

The real rule had already landed. Aarav implemented it at `46d2cbf` (2026-07-31),
and commit `243f58b` reverted `policies/joint.py` to the Week-1 scaffold
(byte-identical to `c7eee5c`) hours before F-001 was written. The degeneracy was a
property of the scaffold, not of the method. With the frozen implementation
restored, all four families separate — measured here rather than asserted.

The frozen method these tests hold the code to is `docs/method/week2_method_freeze.md`,
which the clobber never touched: thresholds 0.25/0.50, desired spend 0/10/20, and a
feasibility clamp.

**This is a structural claim, not a scientific one.** The simulator's degradation
and rescue rates are chosen constants, so the *magnitudes* below are properties of
those constants. What is established is only that the four families are
distinguishable at all — the precondition C-002 needs, and which F-001 reported as
absent.
"""

from __future__ import annotations

import pytest

from human_data_budget.analysis.simulator import simulate_policy

HORIZON = 10
FAMILIES = ("random", "schedule_only", "selection_only", "joint")


def trajectory(policy: str, *, seed: int = 1) -> list[float]:
    run = simulate_policy(policy, chain_seed=seed, horizon=HORIZON)
    return [metric["human_nll"] for metric in run["chain_result"]["metrics"]]


def test_all_four_families_are_distinguishable() -> None:
    """The precondition for C-002. F-001 reported this as false."""
    trajectories = {policy: tuple(trajectory(policy)) for policy in FAMILIES}

    assert len(set(trajectories.values())) == len(FAMILIES), (
        "two or more treatment families collapsed together: "
        f"{ {k: v[:3] for k, v in trajectories.items()} }"
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [("random", "schedule_only"), ("selection_only", "joint")],
)
def test_the_pairs_f001_called_identical_are_not(left: str, right: str) -> None:
    """The two specific equalities F-001 asserted, now false."""
    assert trajectory(left) != trajectory(right)


def test_the_time_axis_is_not_inert() -> None:
    """F-001: "The time-allocation axis is inert."

    schedule_only differs from random only in *when* it spends — same lifetime
    budget, same selection rule. A difference between them is a difference the
    time axis alone produced.
    """
    assert trajectory("random") != trajectory("schedule_only")


def test_the_selection_axis_is_not_inert() -> None:
    """selection_only differs from random only in *what* it rescues."""
    assert trajectory("random") != trajectory("selection_only")


def test_joint_differs_from_both_single_axis_baselines() -> None:
    """C-002 requires joint to be comparable against the strongest of each axis.

    A joint policy that reduced to either one could not test the hypothesis.
    """
    joint = trajectory("joint")

    assert joint != trajectory("schedule_only")
    assert joint != trajectory("selection_only")


def test_distinguishability_holds_across_seeds() -> None:
    """Not an artifact of one seed."""
    for seed in (1, 7, 101):
        trajectories = {tuple(trajectory(policy, seed=seed)) for policy in FAMILIES}
        assert len(trajectories) == len(FAMILIES), f"families collapsed at seed {seed}"
