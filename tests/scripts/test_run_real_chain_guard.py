"""The real chain launcher must refuse unfrozen scientific values.

Mirrors ``tests/scripts/test_run_chain_guard.py`` for the real runner. A chain
launched against a config still awaiting the results freeze produces numbers
nobody can certify, and refusing costs nothing next to the run.

The screening exemption is tested too, because it is the loophole: if it were
wider than intended, a primary config could slip through by relabelling.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_real_chain.py"

sys.path.insert(0, str(SCRIPT.parent))


def _load(config: dict, tmp_path: Path):
    from run_real_chain import load_config  # noqa: PLC0415 - script, not a package

    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return load_config(path)


def test_an_unfrozen_pilot_config_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="refusing to launch"):
        _load({"_freeze_status": "AWAITING_JULY_31_FREEZE", "stage": "pilot",
               "run_id": "x"}, tmp_path)


@pytest.mark.parametrize("stage", ["pilot", "confirmation", "positive_control", None])
def test_no_stage_other_than_screening_or_fixture_is_exempt(stage, tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="refusing to launch"):
        _load({"_freeze_status": "AWAITING_JULY_31_FREEZE", "stage": stage,
               "run_id": "x"}, tmp_path)


@pytest.mark.parametrize("stage", ["screening", "fixture"])
def test_screening_and_fixture_run_without_a_freeze(stage, tmp_path: Path) -> None:
    """A pipeline-validation run is explicitly not a primary result."""
    config = _load({"_freeze_status": "AWAITING_JULY_31_FREEZE", "stage": stage,
                    "run_id": "x"}, tmp_path)
    assert config["stage"] == stage


def test_a_config_with_unset_values_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="unset values"):
        _load({"stage": "screening", "run_id": "x", "horizon": None}, tmp_path)


def test_the_committed_screening_config_passes_its_own_guard() -> None:
    from run_real_chain import load_config  # noqa: PLC0415

    config = load_config(
        ROOT / "configs" / "experiment" / "screening_pipeline_validation.json")
    assert config["stage"] == "screening"
    assert config["chain_seed"] not in {101, 202, 303, 404, 505}, (
        "a screening chain must not reuse a frozen primary seed"
    )


def test_the_unfrozen_primary_configs_are_still_refused() -> None:
    """primary_pilot was frozen deliberately (P-003..P-007); these were not.

    A config must never become launchable by accident, so the two reference
    conditions are checked explicitly rather than by globbing.
    """
    for name in ("primary_no_rescue", "primary_fresh_random"):
        path = ROOT / "configs" / "experiment" / f"{name}.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--config", str(path), "--dry-run"],
            capture_output=True, text=True, cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
        )
        assert result.returncode != 0, f"{name} launched without a freeze"
        assert "refusing to launch" in (result.stdout + result.stderr)
