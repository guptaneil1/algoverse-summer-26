"""``--only-seeds`` restricts a run to part of the frozen seed set.

Added to finish a grid that infrastructure stopped (FAILURE_LOG.md F-026) one
seed block at a time, so that every point at which the money runs out is a fully
crossed design rather than a ragged set of arms.

The property worth guarding is not the filtering, which is obvious, but the
*order*. Chains are dealt to shards positionally, so a seed list that honoured
command-line order would move chains between shards depending on how the operator
typed the argument -- and two shards would then run the same chain, or neither
would.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from run_pilot import select_seeds  # noqa: E402

FROZEN = [101, 202, 303, 404, 505]
ARMS = ["no_rescue", "random", "schedule_only", "selection_only", "joint"]


def _shard(arms: list[str], seeds: list[int], index: int, count: int) -> list[tuple]:
    grid = [(a, s) for a in arms for s in seeds]
    return [c for i, c in enumerate(grid, 1) if (i - 1) % count == index]


def test_absent_argument_leaves_the_frozen_set_untouched() -> None:
    assert select_seeds(FROZEN, None) == FROZEN
    assert select_seeds(FROZEN, "") == FROZEN


def test_a_subset_is_returned_in_config_order_not_command_line_order() -> None:
    """The guard that makes sharding safe."""
    assert select_seeds(FROZEN, "505,303,404") == [303, 404, 505]
    assert select_seeds(FROZEN, "404,505,303") == [303, 404, 505]
    assert select_seeds(FROZEN, "303,404,505") == [303, 404, 505]


def test_shards_still_partition_the_reduced_grid_exactly_once() -> None:
    seeds = select_seeds(FROZEN, "303,404,505")
    for count in (1, 2, 3, 4):
        claimed = [c for k in range(count) for c in _shard(ARMS, seeds, k, count)]
        assert sorted(claimed) == sorted((a, s) for a in ARMS for s in seeds)
        assert len(claimed) == len(set(claimed)), "a chain was dealt to two shards"


def test_every_arm_survives_a_seed_subset() -> None:
    """A seed subset must reduce chains per arm, never drop an arm."""
    seeds = select_seeds(FROZEN, "404")
    grid = [(a, s) for a in ARMS for s in seeds]
    assert {a for a, _ in grid} == set(ARMS)
    assert len(grid) == len(ARMS)


def test_whitespace_and_trailing_commas_are_tolerated() -> None:
    assert select_seeds(FROZEN, " 404 , 505 ,") == [404, 505]


@pytest.mark.parametrize("bad", ["606", "101,606", "0"])
def test_a_seed_outside_the_frozen_set_is_refused(bad: str) -> None:
    with pytest.raises(SystemExit) as caught:
        select_seeds(FROZEN, bad)
    assert "does not" in str(caught.value)


def test_an_empty_seed_list_is_refused_rather_than_running_everything() -> None:
    """`--only-seeds ,` must not silently mean `--only-seeds` absent."""
    with pytest.raises(SystemExit):
        select_seeds(FROZEN, ",")


# --- shard summary naming -------------------------------------------------
#
# The failure this guards is silent. Phases of a block-by-block run share a shard
# index, so a name that ignores the seed subset makes phase 2 overwrite phase 1,
# and --check-only reads summaries -- the whole-grid verdict would then cover only
# the last block while still printing a chain count that looked plausible.

from run_pilot import summary_name  # noqa: E402


def test_a_full_run_keeps_its_historical_summary_names() -> None:
    assert summary_name(None, 0, 1) == "pilot_summary.json"
    assert summary_name(None, 0, 2) == "pilot_summary_shard0of2.json"
    assert summary_name(None, 3, 4) == "pilot_summary_shard3of4.json"


def test_a_seed_subset_gets_its_own_summary_name() -> None:
    assert summary_name([404], 0, 2) == "pilot_summary_seeds404_shard0of2.json"
    assert summary_name([303, 404, 505], 1, 2) == (
        "pilot_summary_seeds303-404-505_shard1of2.json")


def test_successive_phases_never_collide() -> None:
    """Phase 1, 2 and 3 on the same shard must write three distinct files."""
    names = [summary_name([s], 0, 2) for s in (404, 505, 303)]
    assert len(set(names)) == 3


def test_every_name_still_matches_the_reassembly_glob() -> None:
    """load_grid_chains globs pilot_summary*.json; a name it misses loses chains."""
    import fnmatch

    for name in (summary_name(None, 0, 1), summary_name(None, 1, 2),
                 summary_name([404], 0, 2), summary_name([303, 404, 505], 1, 2)):
        assert fnmatch.fnmatch(name, "pilot_summary*.json"), name
