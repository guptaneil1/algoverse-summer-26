"""Provenance emission in the run manifest.

`validation/audit.py` requires `data.partitions` to verify partition disjointness and
per-example provenance; without it a run classifies `invalid` no matter how well the
chain ran. These tests pin the emission, the loud-failure cases that must fire before
compute is spent, and — most importantly — that a run with no provenance source still
classifies `invalid` rather than silently passing.
"""

from pathlib import Path

import pytest

from human_data_budget.runner.manifest import (
    MANIFEST_PARTITIONS,
    PROVENANCE_FIELDS,
    ManifestProvenanceError,
    build_partitions,
    new_manifest,
)
from human_data_budget.runner.schema import validate_json
from human_data_budget.validation.audit import check_separation
from human_data_budget.validation.classification import INVALID, classify

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "src/human_data_budget/runner/fixtures/partitions"

BASE_CONFIG = {
    "run_id": "fixture_provenance_test",
    "horizon": 3,
    "chain_seed": 1,
    "lifetime_human_budget": 60,
    "total_optimizer_tokens": 300,
}


def _example(stable_id: str, content_hash: str) -> dict[str, str]:
    return {
        "stable_id": stable_id,
        "content_hash": content_hash,
        "source_dataset": "test/v1",
        "origin": "human",
    }


def _inline_partitions() -> dict[str, list[dict[str, str]]]:
    return {
        name: [_example(f"{name}-1", f"hash-{name}")] for name in MANIFEST_PARTITIONS
    }


def _manifest_sources() -> dict[str, str]:
    return {name: str(FIXTURES / f"{name}.jsonl") for name in MANIFEST_PARTITIONS}


def _data(**extra: object) -> dict[str, object]:
    """A schema-complete data block; the schema requires the train manifest fields."""

    return {
        "train_manifest": "data/fixtures/toy_corpus.jsonl",
        "train_manifest_sha256": "fixture",
        **extra,
    }


# --- the guard that matters ------------------------------------------------


def test_no_provenance_source_still_classifies_invalid() -> None:
    """A config declaring no provenance must not silently gain a passing manifest."""

    manifest = new_manifest(BASE_CONFIG, policy_name="random")

    assert "partitions" not in manifest["data"]
    assert classify(check_separation(manifest)) == INVALID


# --- inline source ---------------------------------------------------------


def test_inline_partitions_are_emitted_and_pass_separation() -> None:
    config = {**BASE_CONFIG, "data": _data(partitions=_inline_partitions())}

    manifest = new_manifest(config, policy_name="random")

    assert set(manifest["data"]["partitions"]) == set(MANIFEST_PARTITIONS)
    validate_json(manifest, ROOT / "schemas/run_manifest.schema.json")
    assert classify(check_separation(manifest)) != INVALID


# --- JSONL source, through Neil's loader -----------------------------------


def test_partition_manifests_load_and_translate_vocabulary() -> None:
    """The canonical names and fields are produced from data/manifest.py records."""

    config = {**BASE_CONFIG, "data": _data(partition_manifests=_manifest_sources())}

    manifest = new_manifest(config, policy_name="random")
    partitions = manifest["data"]["partitions"]

    assert set(partitions) == set(MANIFEST_PARTITIONS)
    for records in partitions.values():
        for record in records:
            assert all(record.get(field) for field in PROVENANCE_FIELDS)
    # source -> source_dataset translation survived the round trip.
    assert partitions["base_human_train"][0]["source_dataset"] == "runner-fixture/toy-v1"
    # example_id -> stable_id translation survived the round trip.
    assert partitions["base_human_train"][0]["stable_id"] == "toy-train-1"

    validate_json(manifest, ROOT / "schemas/run_manifest.schema.json")
    assert classify(check_separation(manifest)) != INVALID


def test_partition_manifests_block_is_not_leaked_into_the_manifest() -> None:
    config = {**BASE_CONFIG, "data": _data(partition_manifests=_manifest_sources())}

    manifest = new_manifest(config, policy_name="random")

    assert "partition_manifests" not in manifest["data"]


# --- loud failures, all before a chain launches ----------------------------


def test_missing_manifest_file_raises() -> None:
    sources = _manifest_sources()
    sources["validation"] = str(FIXTURES / "does_not_exist.jsonl")

    with pytest.raises(ManifestProvenanceError, match="does not exist"):
        build_partitions({"partition_manifests": sources})


def test_unknown_partition_name_raises() -> None:
    with pytest.raises(ManifestProvenanceError, match="unknown partition"):
        build_partitions({"partition_manifests": {"train": "ignored.jsonl"}})


def test_incomplete_provenance_raises() -> None:
    partitions = _inline_partitions()
    del partitions["base_human_train"][0]["source_dataset"]

    with pytest.raises(ManifestProvenanceError, match="source_dataset"):
        build_partitions({"partitions": partitions})


def test_empty_partition_raises() -> None:
    partitions = _inline_partitions()
    partitions["validation"] = []

    with pytest.raises(ManifestProvenanceError, match="zero examples"):
        build_partitions({"partitions": partitions})


def test_declaring_both_sources_raises() -> None:
    data = {"partitions": _inline_partitions(), "partition_manifests": _manifest_sources()}

    with pytest.raises(ManifestProvenanceError, match="single origin"):
        build_partitions(data)


def test_forbidden_overlap_fails_before_launch() -> None:
    """A leaked test example must stop the run at manifest creation, not at audit."""

    partitions = _inline_partitions()
    partitions["rescue_candidates"] = list(partitions["final_human_test"])

    with pytest.raises(ValueError, match="overlap detected"):
        build_partitions({"partitions": partitions})
