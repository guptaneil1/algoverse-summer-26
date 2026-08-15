"""The run manifest carries per-example partition provenance (PROTOCOL.md §3).

Audit finding `docs/audits/week3_execution_required.md` §1.2: the toy runner
emitted no `data.partitions` block, so the auditor could not verify partition
disjointness or per-example provenance and classified every run `invalid` with
`SEPARATION_MISSING_PROVENANCE`. These tests pin both directions — the block is
emitted when sources are declared, and its absence is still rejected.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from human_data_budget.data.hashing import content_hash
from human_data_budget.runner.manifest import new_manifest
from human_data_budget.runner.provenance import (
    RUN_MANIFEST_PARTITIONS,
    PartitionSourceError,
    build_partition_provenance,
)
from human_data_budget.runner.schema import validate_json
from human_data_budget.validation.audit import REQUIRED_PROVENANCE_FIELDS, check_separation

ROOT = Path(__file__).resolve().parents[2]

BASE_CONFIG: dict[str, Any] = {
    "run_id": "fixture_provenance_test",
    "horizon": 3,
    "chain_seed": 1,
    "lifetime_human_budget": 60,
    "total_optimizer_tokens": 300,
}

TOY_SOURCES = {
    name: f"data/fixtures/partitions/{name}.jsonl" for name in RUN_MANIFEST_PARTITIONS
}


def _config_with_sources() -> dict[str, Any]:
    config = dict(BASE_CONFIG)
    config["data"] = {
        "train_manifest": "data/fixtures/partitions/base_human_train.jsonl",
        "train_manifest_sha256": "fixture",
        "partition_sources": dict(TOY_SOURCES),
    }
    return config


def _failed_codes(manifest: dict[str, Any]) -> set[str]:
    return {check.code for check in check_separation(manifest) if not check.passed}


# --- the defect this closes -------------------------------------------------


def test_manifest_without_partitions_is_rejected() -> None:
    """The regression guard: no provenance block means the run cannot be certified.

    This is the state the toy runner shipped in, recorded in
    `docs/validity/week3_adversarial_audit.md` §7.
    """
    manifest = new_manifest(BASE_CONFIG, policy_name="joint")

    assert "partitions" not in manifest["data"]
    assert _failed_codes(manifest) == {"SEPARATION_MISSING_PROVENANCE"}


def test_empty_partitions_block_is_also_rejected() -> None:
    """An empty block must not read as 'verified disjoint'."""
    manifest = new_manifest(BASE_CONFIG, policy_name="joint")
    manifest["data"]["partitions"] = {}

    assert _failed_codes(manifest) == {"SEPARATION_MISSING_PROVENANCE"}


def test_config_declaring_no_sources_emits_no_block() -> None:
    """Provenance is never synthesised for data that was not declared."""
    config = dict(BASE_CONFIG)
    config["data"] = {"train_manifest": "x.jsonl", "train_manifest_sha256": "fixture"}

    assert "partitions" not in new_manifest(config, policy_name="joint")["data"]


# --- the fix ----------------------------------------------------------------


def test_declared_sources_produce_a_complete_provenance_block() -> None:
    manifest = new_manifest(_config_with_sources(), policy_name="joint", data_root=ROOT)
    partitions = manifest["data"]["partitions"]

    assert set(partitions) == set(RUN_MANIFEST_PARTITIONS)
    for name in RUN_MANIFEST_PARTITIONS:
        assert partitions[name], f"partition {name} is empty"
        for entry in partitions[name]:
            for field in REQUIRED_PROVENANCE_FIELDS:
                assert entry.get(field), f"{name} entry missing {field}"


def test_toy_manifest_passes_separation_with_no_failed_checks() -> None:
    manifest = new_manifest(_config_with_sources(), policy_name="joint", data_root=ROOT)

    assert _failed_codes(manifest) == set()


def test_manifest_with_partitions_still_validates_against_the_schema() -> None:
    """The schema permits the block (`additionalProperties: true`); no contract change."""
    manifest = new_manifest(_config_with_sources(), policy_name="joint", data_root=ROOT)

    validate_json(manifest, ROOT / "schemas/run_manifest.schema.json")


def test_content_hash_is_recomputed_from_text_not_copied() -> None:
    """A hash is a measurement of the bytes, never a value carried over on trust."""
    partitions = build_partition_provenance(TOY_SOURCES, root=ROOT)

    for entries in partitions.values():
        for entry in entries:
            assert entry["content_hash"] == content_hash(entry["text"])


def test_source_hash_disagreeing_with_its_own_text_is_rejected(tmp_path: Path) -> None:
    """A source claiming a hash its text does not produce must not reach the manifest."""
    record = {
        "example_id": "x-1",
        "text": "Some fixture text.",
        "content_hash": "0" * 64,
        "origin": "human",
        "mode": "common",
        "source": "toy-fixture-corpus/v1",
        "source_offset": 0,
        "token_count": 3,
    }
    path = tmp_path / "validation.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record) + "\n")

    with pytest.raises(ValueError, match="content_hash mismatch"):
        build_partition_provenance({"validation": path}, root=tmp_path)


def test_missing_source_file_is_an_error_not_a_silent_empty_block(tmp_path: Path) -> None:
    with pytest.raises(PartitionSourceError, match="does not exist"):
        build_partition_provenance({"validation": tmp_path / "absent.jsonl"}, root=tmp_path)


def test_unknown_partition_name_is_rejected() -> None:
    with pytest.raises(PartitionSourceError, match="unknown partition"):
        build_partition_provenance({"not_a_partition": "x.jsonl"}, root=ROOT)


def test_provenance_does_not_depend_on_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run's recorded provenance must not change with the directory it was launched from.

    Partition sources are declared repository-relative. Resolving them against
    the process working directory made every chain-running test fail when pytest
    was invoked from anywhere but the repository root, and would have made a real
    run's manifest depend on the operator's shell location.
    """
    from_root = new_manifest(_config_with_sources(), policy_name="joint")

    monkeypatch.chdir(tmp_path)
    from_elsewhere = new_manifest(_config_with_sources(), policy_name="joint")

    assert from_elsewhere["data"]["partitions"] == from_root["data"]["partitions"]
    assert from_root["data"]["partitions"]["final_human_test"]


def test_toy_partition_fixtures_are_mutually_disjoint() -> None:
    """The shipped fixtures must not themselves contain a leak."""
    partitions = build_partition_provenance(TOY_SOURCES, root=ROOT)
    seen: dict[str, str] = {}

    for name, entries in partitions.items():
        for entry in entries:
            digest = entry["content_hash"]
            assert digest not in seen, (
                f"{name} shares content with {seen[digest]}: {entry['stable_id']}"
            )
            seen[digest] = name
