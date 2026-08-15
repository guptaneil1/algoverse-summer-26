"""Tests for the PROTOCOL.md §3 training-time provenance record.

§3 requires every training example to retain, after shuffling and batching:
stable ID, content hash, source dataset **and revision**, human/synthetic origin,
recursive generation, selection policy **and score**, whether it was selected, and
number of optimizer presentations.

Before `validate_training_provenance` existed, `Example` carried only the first
three groups: revision, generation, selection policy/score, selected, and
presentation count had nowhere to live, so the invariant could not be checked.
"""

from __future__ import annotations

import pytest

from human_data_budget.data.manifest import (
    Example,
    PartitionManifest,
    ProvenanceError,
    validate_training_provenance,
)


def partition_record(**overrides) -> dict:
    record = {
        "example_id": "h-001",
        "text": "a human sentence",
        "origin": "human",
        "mode": "tail",
        "source": "wikitext-103-v1",
        "source_offset": 17,
        "token_count": 4,
    }
    record.update(overrides)
    return record


def trained_record(**overrides) -> dict:
    record = partition_record(
        source_revision="b8a3f1c",
        generation=2,
        selection_policy="joint",
        selection_score=0.62,
        selected=True,
        optimizer_presentations=1,
    )
    record.update(overrides)
    return record


def test_partition_example_needs_no_training_provenance() -> None:
    """Reading a frozen partition must not require selection metadata."""
    example = Example.from_dict(partition_record())
    assert example.generation is None
    assert example.selection_policy is None
    assert example.optimizer_presentations == 0


def test_partition_example_is_rejected_at_training_time() -> None:
    example = Example.from_dict(partition_record())
    with pytest.raises(ProvenanceError) as excinfo:
        validate_training_provenance(example)
    message = str(excinfo.value)
    for field in ("source_revision", "generation", "selection_policy", "selection_score"):
        assert field in message


def test_complete_training_provenance_passes() -> None:
    validate_training_provenance(Example.from_dict(trained_record()))


@pytest.mark.parametrize(
    "field",
    ["source_revision", "generation", "selection_policy", "selection_score", "selected"],
)
def test_each_missing_field_is_detected(field: str) -> None:
    """Anchored on the missing-provenance message, not the bare field name.

    Matching on `"selected"` alone passed for the wrong reason: it is a substring
    of `"unselected"`, so the unrelated "marked unselected but records N
    presentations" error satisfied the assertion even when the missing-field
    check had not fired at all.
    """
    record = trained_record()
    record[field] = None
    with pytest.raises(ProvenanceError, match="missing training provenance") as excinfo:
        validate_training_provenance(Example.from_dict(record))
    assert field in str(excinfo.value)


def test_selected_example_must_record_a_presentation() -> None:
    """Selected but never presented is an accounting contradiction."""
    record = trained_record(optimizer_presentations=0)
    with pytest.raises(ProvenanceError, match="zero optimizer presentations"):
        validate_training_provenance(Example.from_dict(record))


def test_unselected_example_must_not_record_presentations() -> None:
    """The inverse contradiction: never selected yet consumed by the optimizer."""
    record = trained_record(selected=False, optimizer_presentations=3)
    with pytest.raises(ProvenanceError, match="unselected"):
        validate_training_provenance(Example.from_dict(record))


def test_negative_presentations_are_rejected() -> None:
    with pytest.raises(Exception, match="must not be negative"):
        Example.from_dict(trained_record(optimizer_presentations=-1))


def test_repeated_presentations_are_retained_exactly() -> None:
    """The count must survive round-tripping; it is the budget's unit."""
    example = Example.from_dict(trained_record(optimizer_presentations=3))
    validate_training_provenance(example)
    assert example.optimizer_presentations == 3


def test_partition_manifest_hash_ignores_training_provenance() -> None:
    """Adding training provenance must not change a frozen partition's identity.

    The manifest hash is the partition's stable identity. If selection metadata
    perturbed it, a partition would appear to change every time a policy touched
    an example, and no frozen data reference would survive a run.
    """
    plain = PartitionManifest.from_examples(
        "rescue_candidates", [Example.from_dict(partition_record())]
    )
    annotated = PartitionManifest.from_examples(
        "rescue_candidates", [Example.from_dict(trained_record())]
    )
    assert plain.manifest_hash == annotated.manifest_hash


def test_training_provenance_is_serialized_when_present() -> None:
    manifest = PartitionManifest.from_examples(
        "rescue_candidates", [Example.from_dict(trained_record())]
    )
    record = manifest.to_dict()["examples"][0]
    assert record["source_revision"] == "b8a3f1c"
    assert record["generation"] == 2
    assert record["selection_policy"] == "joint"
    assert record["selection_score"] == pytest.approx(0.62)
    assert record["selected"] is True
    assert record["optimizer_presentations"] == 1


def test_partition_serialization_stays_minimal() -> None:
    """Unpopulated provenance keys are omitted, not emitted as nulls."""
    manifest = PartitionManifest.from_examples(
        "base_train", [Example.from_dict(partition_record())]
    )
    record = manifest.to_dict()["examples"][0]
    for field in (
        "source_revision",
        "generation",
        "selection_policy",
        "selection_score",
        "selected",
        "optimizer_presentations",
    ):
        assert field not in record


# ---------------------------------------------------------------------------
# Regression tests for defects found by adversarial review on 2026-08-15.
# ---------------------------------------------------------------------------


def test_manifest_survives_its_own_serialization() -> None:
    """A manifest must round-trip without changing identity.

    `to_dict` emits `content_hash` but not `text`, because a manifest references
    a corpus rather than copying it. `from_dict` previously recomputed the hash
    from `record.get("text", "")`, so every reloaded example took the hash of the
    empty string and the partition's identity silently changed.
    """
    original = PartitionManifest.from_examples(
        "base_train", [Example.from_dict(partition_record())]
    )
    serialized = original.to_dict()

    reloaded = PartitionManifest.from_examples(
        "base_train", [Example.from_dict(record) for record in serialized["examples"]]
    )
    assert reloaded.manifest_hash == original.manifest_hash
    assert reloaded.examples[0].content_hash == original.examples[0].content_hash


def test_contradictory_content_hash_is_rejected() -> None:
    """If both text and a hash are supplied, they must agree."""
    record = partition_record()
    record["content_hash"] = "0" * 64
    with pytest.raises(Exception, match="content_hash mismatch"):
        Example.from_dict(record)


def test_record_without_text_or_hash_is_rejected() -> None:
    record = partition_record()
    record.pop("text")
    with pytest.raises(Exception, match="either 'text' or"):
        Example.from_dict(record)


def test_manifest_hash_resists_delimiter_injection() -> None:
    """Unframed `id:hash\\n` concatenation let a crafted id forge boundaries.

    Two structurally different partitions could then hash identically, so one
    could be substituted for the other without changing its recorded identity.
    """
    benign = PartitionManifest.from_examples(
        "base_train",
        [
            Example.from_dict(partition_record(example_id="a", text="one")),
            Example.from_dict(partition_record(example_id="b", text="two")),
        ],
    )
    forged_id = f"a:{benign.examples[0].content_hash}\nb"
    attacker = PartitionManifest.from_examples(
        "base_train", [Example.from_dict(partition_record(example_id=forged_id, text="two"))]
    )
    assert attacker.manifest_hash != benign.manifest_hash


def test_duplicate_example_ids_are_rejected() -> None:
    """A partition with two records sharing an id has no defined membership."""
    with pytest.raises(Exception, match="duplicate example_id"):
        PartitionManifest.from_examples(
            "base_train",
            [
                Example.from_dict(partition_record(example_id="dup", text="one")),
                Example.from_dict(partition_record(example_id="dup", text="two")),
            ],
        )
