"""Tests for the preflight budget-equality checker."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "preflight_budget", ROOT / "scripts" / "preflight_budget.py"
)
preflight = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = preflight
_SPEC.loader.exec_module(preflight)


def config(**overrides) -> dict:
    document = {
        "run_id": "chain-001",
        "policy": "joint",
        "horizon": 3,
        "lifetime_human_budget": 60,
        "per_generation_human_budget": 20,
        "total_optimizer_tokens": 300,
        "candidates": [
            {"example_id": "c1", "human_token_count": 10, "mode": "common"},
            {"example_id": "c2", "human_token_count": 10, "mode": "common"},
            {"example_id": "t1", "human_token_count": 10, "mode": "tail"},
            {"example_id": "t2", "human_token_count": 10, "mode": "tail"},
        ],
    }
    document.update(overrides)
    return document


def write(tmp_path: Path, name: str, document: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_shipped_toy_config_passes() -> None:
    """The config actually in the repo must pass its own preflight."""
    assert preflight.main([str(ROOT / "configs" / "experiment" / "toy_cpu.json")]) == 0


def test_consistent_config_passes(tmp_path: Path) -> None:
    assert preflight.check_internal(config(), Path("c.json")) == []


def test_budget_arithmetic_mismatch_is_caught() -> None:
    """per_generation x horizon must equal the lifetime budget."""
    failures = preflight.check_internal(
        config(per_generation_human_budget=25), Path("c.json")
    )
    assert any("does not equal" in failure for failure in failures)


def test_human_budget_exceeding_total_is_caught() -> None:
    failures = preflight.check_internal(
        config(
            lifetime_human_budget=600,
            per_generation_human_budget=200,
            total_optimizer_tokens=300,
        ),
        Path("c.json"),
    )
    assert any("exceeds" in failure for failure in failures)


def test_unspendable_budget_is_caught() -> None:
    """A budget larger than the candidate pool causes silent underspend."""
    failures = preflight.check_internal(
        config(
            candidates=[
                {"example_id": "c1", "human_token_count": 5, "mode": "common"},
                {"example_id": "t1", "human_token_count": 5, "mode": "tail"},
            ]
        ),
        Path("c.json"),
    )
    assert any("unspendable" in failure for failure in failures)


def test_single_mode_pool_is_caught() -> None:
    """Mode allocation is untestable when every candidate shares one mode."""
    failures = preflight.check_internal(
        config(
            candidates=[
                {"example_id": "c1", "human_token_count": 20, "mode": "common"},
                {"example_id": "c2", "human_token_count": 20, "mode": "common"},
            ]
        ),
        Path("c.json"),
    )
    assert any("mode(s)" in failure for failure in failures)


def test_placeholder_value_blocks_launch() -> None:
    failures = preflight.check_internal(
        config(per_generation_human_budget="TBD_BEFORE_PRIMARY_RUNS"), Path("c.json")
    )
    assert any("placeholder" in failure for failure in failures)


def test_missing_field_is_caught() -> None:
    document = config()
    del document["total_optimizer_tokens"]
    failures = preflight.check_internal(document, Path("c.json"))
    assert any("missing required field" in failure for failure in failures)


def test_matched_comparison_set_passes(tmp_path: Path) -> None:
    paths = [
        write(tmp_path, f"{policy}.json", config(policy=policy))
        for policy in ("random", "schedule_only", "selection_only", "joint")
    ]
    assert preflight.main([str(path) for path in paths] + ["--compare"]) == 0


def test_mismatched_human_budget_fails_comparison(tmp_path: Path) -> None:
    """The core fairness violation: one policy gets more human tokens."""
    good = write(tmp_path, "joint.json", config(policy="joint"))
    cheat = write(
        tmp_path,
        "random.json",
        config(policy="random", lifetime_human_budget=90, per_generation_human_budget=30),
    )
    assert preflight.main([str(good), str(cheat), "--compare"]) == 1


def test_mismatched_total_budget_fails_comparison(tmp_path: Path) -> None:
    good = write(tmp_path, "joint.json", config(policy="joint"))
    cheat = write(tmp_path, "random.json", config(policy="random", total_optimizer_tokens=600))
    assert preflight.main([str(good), str(cheat), "--compare"]) == 1


def test_duplicate_policy_fails_comparison(tmp_path: Path) -> None:
    a = write(tmp_path, "a.json", config(policy="joint"))
    b = write(tmp_path, "b.json", config(policy="joint"))
    assert preflight.main([str(a), str(b), "--compare"]) == 1


def test_comparison_checks_are_opt_in(tmp_path: Path) -> None:
    """Without --compare, mismatched budgets across configs are not an error."""
    good = write(tmp_path, "joint.json", config(policy="joint"))
    other = write(tmp_path, "random.json", config(policy="random", total_optimizer_tokens=600))
    assert preflight.main([str(good), str(other)]) == 0
