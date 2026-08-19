"""A frozen, executable config must produce a certifiable manifest.

FAILURE_LOG.md F-019, which is F-004 recurring on the real-chain path. The pilot
config names its five partitions under ``data.manifests``; ``build_partitions`` knew
only ``partitions`` and ``partition_manifests``, so it returned ``None`` and every
chain emitted a manifest with no ``data.partitions``. The validator then classified
each one ``invalid`` with ``SEPARATION_MISSING_PROVENANCE``.

Nothing caught it because every existing manifest test supplied its own fixture data
block. No test asked the question that matters before spending: does *the config we
are about to launch* yield a manifest that can be certified?

That is what this file asks, of every executable config in the repository.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from human_data_budget.runner.manifest import (
    MANIFEST_PARTITIONS,
    build_partitions,
    new_manifest,
)

CONFIG_DIR = Path("configs/experiment")
UNFROZEN = "AWAITING_JULY_31_FREEZE"


#: Stages held to the five-partition provenance contract. ``positive_control`` is
#: deliberately absent: Stage A drives a different upstream pipeline (GPT-2 over
#: WikiText-2) whose data block names a preparation command and a test manifest, not
#: Neil's partitions, and it is certified through
#: ``runner/positive_control_adapter.py`` rather than this path. Holding it to a
#: contract its design does not use would fail a stage that has already reproduced
#: twice with verifying hashes.
PARTITIONED_STAGES = {"pilot", "primary", "screening"}


def executable_configs() -> list[Path]:
    """Every experiment config a launcher would accept and this contract governs."""
    found = []
    for path in sorted(CONFIG_DIR.glob("*.json")):
        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("_freeze_status") == UNFROZEN:
            continue
        if config.get("stage") not in PARTITIONED_STAGES:
            continue
        if not isinstance(config.get("data"), dict):
            continue
        found.append(path)
    return found


def test_the_pilot_config_is_actually_covered() -> None:
    """Guard the guard: a filter that silently excluded everything would pass."""
    covered = {path.stem for path in executable_configs()}
    assert "primary_pilot" in covered, (
        f"the config the pilot launches is not covered by this file; covered: {covered}"
    )


@pytest.mark.parametrize("path", executable_configs(), ids=lambda p: p.stem)
def test_executable_config_resolves_partition_provenance(path: Path) -> None:
    """The check the validator will apply, applied before any compute is spent."""
    config = json.loads(path.read_text(encoding="utf-8"))
    partitions = build_partitions(config["data"])

    assert partitions is not None, (
        f"{path.name} declares no partition provenance the manifest builder "
        "recognises, so every chain it launches classifies invalid with "
        "SEPARATION_MISSING_PROVENANCE. This is F-019."
    )
    assert set(partitions) == set(MANIFEST_PARTITIONS), (
        f"{path.name} resolved {sorted(partitions)}, expected all of "
        f"{sorted(MANIFEST_PARTITIONS)}"
    )
    for name, records in partitions.items():
        assert records, f"{path.name}: partition {name} resolved to zero records"


def test_pilot_manifest_carries_partitions() -> None:
    """End to end: the manifest a pilot chain writes must carry provenance."""
    config = json.loads(
        (CONFIG_DIR / "primary_pilot.json").read_text(encoding="utf-8")
    )
    config = dict(config, run_id="test_probe", chain_seed=101)
    manifest = new_manifest(config, policy_name="no_rescue")

    partitions = manifest["data"].get("partitions")
    assert partitions is not None, "run_manifest.json would omit data.partitions"
    assert set(partitions) == set(MANIFEST_PARTITIONS)

    # The frozen partition sizes, from the manifests Neil built. A silent change here
    # means the manifest builder resolved something other than the frozen partitions.
    assert len(partitions["base_human_train"]) == 22_637
    assert len(partitions["rescue_candidates"]) == 4_235
    assert len(partitions["generation_prompts"]) == 1_359
    assert len(partitions["validation"]) == 60
    assert len(partitions["final_human_test"]) == 60


def test_the_launcher_passes_provenance_through_to_the_manifest() -> None:
    """The config a chain actually receives, not the one on disk.

    This is the gap that made the first F-019 fix ineffective. ``build_partitions``
    was corrected and verified against ``primary_pilot.json`` directly, but
    ``run_pilot.chain_config`` flattens the pilot config into per-chain keys and did
    not carry ``data`` at all, so ``new_manifest`` fell back to its default and wrote
    no provenance. Verifying the config on disk proved nothing about the config the
    runner is handed.
    """
    spec = importlib.util.spec_from_file_location(
        "run_pilot_under_test", Path("scripts/run_pilot.py")
    )
    run_pilot = importlib.util.module_from_spec(spec)
    sys.modules["run_pilot_under_test"] = run_pilot
    spec.loader.exec_module(run_pilot)

    pilot = json.loads((CONFIG_DIR / "primary_pilot.json").read_text(encoding="utf-8"))
    for arm in pilot["arms"]:
        config = run_pilot.chain_config(pilot, arm, pilot["seeds"][0])
        manifest = run_pilot_manifest(config, arm)
        partitions = manifest["data"].get("partitions")
        assert partitions is not None, (
            f"the config run_pilot hands the {arm} arm produces a manifest with no "
            "provenance, so every chain of that arm certifies invalid"
        )
        assert set(partitions) == set(MANIFEST_PARTITIONS)


def run_pilot_manifest(config: dict, policy_name: str) -> dict:
    """Build the manifest a chain would write from a flattened chain config."""
    return new_manifest(dict(config, chain_seed=config["chain_seed"]),
                        policy_name=policy_name)


def test_no_declared_provenance_still_returns_none() -> None:
    """The contract build_partitions is required to keep.

    A config with no provenance source must keep classifying invalid rather than
    silently passing. Deriving from `manifests` adds a source; it must not invent one.
    """
    assert build_partitions({"dataset": "wikitext-103-v1"}) is None
    assert build_partitions({"manifests": {}}) is None
    assert build_partitions({"manifests": {"not_a_partition": {"path": "x"}}}) is None


def test_explicit_partition_manifests_take_precedence() -> None:
    """An explicit declaration must not be overridden by the derived one."""
    data = {
        "partition_manifests": {
            name: f"data/manifests/{module}.jsonl"
            for name, module in (
                ("base_human_train", "base_train"),
                ("rescue_candidates", "rescue_candidates"),
                ("generation_prompts", "prompts"),
                ("validation", "validation"),
                ("final_human_test", "test"),
            )
        },
        # A manifests block naming nothing resolvable; if it were consulted the call
        # would resolve no partitions at all.
        "manifests": {"not_a_partition": {"path": "does/not/exist.jsonl"}},
    }
    partitions = build_partitions(data)
    assert partitions is not None
    assert set(partitions) == set(MANIFEST_PARTITIONS)
