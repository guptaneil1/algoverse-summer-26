"""Tests for the pilot driver: sharding, config expansion, and the freeze guard.

Sharding is where a silent bug would be worst. A partition that drops a chain
yields a pilot with 24 of 25 chains that still reports success, and the missing
chain is invisible unless someone counts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from run_pilot import chain_config  # noqa: E402

ARMS = ["no_rescue", "random", "schedule_only", "selection_only", "joint"]
SEEDS = [101, 202, 303, 404, 505]


def _shard(index: int, count: int) -> list[int]:
    grid = [(a, s) for a in ARMS for s in SEEDS]
    return [i for i, _ in enumerate(grid, 1) if (i - 1) % count == index]


@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 7])
def test_every_chain_is_claimed_exactly_once(count: int) -> None:
    claimed = sorted(i for k in range(count) for i in _shard(k, count))
    assert claimed == list(range(1, len(ARMS) * len(SEEDS) + 1))


@pytest.mark.parametrize("count", [2, 4])
def test_shards_are_balanced_within_one_chain(count: int) -> None:
    sizes = [len(_shard(k, count)) for k in range(count)]
    assert max(sizes) - min(sizes) <= 1


def test_each_shard_gets_a_mix_of_arms() -> None:
    """Arms differ in cost, so a shard holding one arm would finish out of step."""
    grid = [(a, s) for a in ARMS for s in SEEDS]
    for k in range(4):
        arms = {grid[i - 1][0] for i in _shard(k, 4)}
        assert len(arms) >= 4, f"shard {k} covers only {arms}"


def _pilot() -> dict:
    return {
        "run_id": "p", "budget_id": "b", "stage": "pilot", "horizon": 10,
        "lifetime_human_budget": 750_000, "per_generation_human_budget": 75_000,
        "maximum_generation_human_budget": 150_000,
        "total_optimizer_tokens": 16_100_000, "tail_modes": ["tail"],
        "model": {"identifier": "gpt2"}, "training": {"block_size": 512},
        "decoding": {"top_k": 50}, "detector": {"model_path": "d"},
        "data": {
            "manifests": {
                "rescue_candidates": {"path": "r.jsonl"},
                "validation": {"path": "v.jsonl"},
            },
            "corpora": {"base_corpus": "b.json", "prompt_corpus": "p.json",
                        "test_corpus": "t.json"},
        },
    }


def test_expansion_carries_the_shared_budget_to_every_arm() -> None:
    """Budget matching starts here: one lifetime figure, identical across arms."""
    budgets = {chain_config(_pilot(), arm, 101)["lifetime_human_budget"]
               for arm in ARMS}
    assert budgets == {750_000}


def test_expansion_gives_each_chain_a_distinct_run_id() -> None:
    ids = {chain_config(_pilot(), arm, seed)["run_id"]
           for arm in ARMS for seed in SEEDS}
    assert len(ids) == len(ARMS) * len(SEEDS)


def test_schedule_only_receives_a_back_loaded_schedule() -> None:
    """ScheduleOnlyPolicy cannot be built without one; the frozen shape is back-loaded."""
    schedule = chain_config(_pilot(), "schedule_only", 101)["schedule"]
    assert [schedule[str(g)] for g in range(10)] == [0] * 5 + [150_000] * 5


def test_other_arms_get_no_schedule() -> None:
    for arm in ("no_rescue", "random", "selection_only", "joint"):
        assert "schedule" not in chain_config(_pilot(), arm, 101)


def test_the_frozen_primary_configs_are_still_refused_by_the_driver() -> None:
    """Nothing in the pilot work may have quietly unfrozen a primary configuration."""
    import subprocess

    for name in ("primary_no_rescue", "primary_fresh_random"):
        path = ROOT / "configs" / "experiment" / f"{name}.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("_freeze_status") != "AWAITING_JULY_31_FREEZE":
            continue
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_pilot.py"),
             "--config", str(path), "--dry-run"],
            capture_output=True, text=True, cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
        )
        assert result.returncode != 0
        assert "refusing to launch" in (result.stdout + result.stderr)
