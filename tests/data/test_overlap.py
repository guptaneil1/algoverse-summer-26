"""Tests for exact and near-duplicate overlap detection across partitions."""

from __future__ import annotations

from pathlib import Path

import pytest

from human_data_budget.data.manifest import PartitionManifest, load_manifest_from_jsonl
from human_data_budget.data.overlap import check_near_duplicate_overlap, find_near_duplicate_pairs
from human_data_budget.data.separation import assert_disjoint

FIXTURES = Path(__file__).parent / "fixtures"


def _load_clean_partitions() -> dict[str, PartitionManifest]:
    return {
        "base_train": load_manifest_from_jsonl(FIXTURES / "base_train.jsonl", "base_train"),
        "rescue_candidates": load_manifest_from_jsonl(
            FIXTURES / "rescue_candidates.jsonl", "rescue_candidates"
        ),
        "prompts": load_manifest_from_jsonl(FIXTURES / "prompts.jsonl", "prompts"),
        "validation": load_manifest_from_jsonl(FIXTURES / "validation.jsonl", "validation"),
        "test": load_manifest_from_jsonl(FIXTURES / "test.jsonl", "test"),
    }


# --- exact overlap ---


def test_clean_partitions_have_no_exact_overlap() -> None:
    manifests = _load_clean_partitions()
    all_ids = {
        partition: [ex.example_id for ex in m.examples]
        for partition, m in manifests.items()
    }
    assert_disjoint(all_ids)  # must not raise


def test_exact_overlap_detected_by_assert_disjoint() -> None:
    a = load_manifest_from_jsonl(FIXTURES / "overlap_partition_a.jsonl", "base_train")
    b = load_manifest_from_jsonl(FIXTURES / "overlap_partition_b.jsonl", "rescue_candidates")
    with pytest.raises(ValueError, match="overlap detected"):
        assert_disjoint(
            {
                "base_train": [ex.example_id for ex in a.examples],
                "rescue_candidates": [ex.example_id for ex in b.examples],
            }
        )


def test_content_hash_overlap_catches_verbatim_copies() -> None:
    """Same text in two partitions is caught via content hash even if IDs differ."""
    a = load_manifest_from_jsonl(FIXTURES / "overlap_partition_a.jsonl", "base_train")
    b = load_manifest_from_jsonl(FIXTURES / "overlap_partition_b.jsonl", "rescue_candidates")
    with pytest.raises(ValueError, match="overlap detected"):
        assert_disjoint(
            {
                "base_train": [ex.content_hash for ex in a.examples],
                "rescue_candidates": [ex.content_hash for ex in b.examples],
            }
        )


def test_test_partition_overlap_blocked() -> None:
    """Overlap between any partition and the test set must be detected."""
    test_m = load_manifest_from_jsonl(FIXTURES / "overlap_partition_a.jsonl", "test")
    rescue_m = load_manifest_from_jsonl(FIXTURES / "overlap_partition_b.jsonl", "rescue_candidates")
    with pytest.raises(ValueError, match="overlap detected"):
        assert_disjoint(
            {
                "test": [ex.example_id for ex in test_m.examples],
                "rescue_candidates": [ex.example_id for ex in rescue_m.examples],
            }
        )


# --- near-duplicate detection ---


def test_near_duplicate_pair_detected() -> None:
    a = load_manifest_from_jsonl(FIXTURES / "near_dup_a.jsonl", "base_train")
    b = load_manifest_from_jsonl(FIXTURES / "near_dup_b.jsonl", "rescue_candidates")
    pairs = find_near_duplicate_pairs(a, b, threshold=0.8)
    assert len(pairs) >= 1
    ids_a = {p[0] for p in pairs}
    assert "nd-a-1" in ids_a


def test_dissimilar_texts_not_flagged() -> None:
    """Clean partitions with unrelated text should produce no near-duplicate pairs."""
    a = load_manifest_from_jsonl(FIXTURES / "base_train.jsonl", "base_train")
    b = load_manifest_from_jsonl(FIXTURES / "rescue_candidates.jsonl", "rescue_candidates")
    pairs = find_near_duplicate_pairs(a, b, threshold=0.8)
    assert pairs == []


def test_check_near_duplicate_overlap_clean_dataset() -> None:
    manifests = _load_clean_partitions()
    results = check_near_duplicate_overlap(manifests, threshold=0.8)
    assert results == []


def test_check_near_duplicate_overlap_finds_near_dups() -> None:
    manifests = {
        "base_train": load_manifest_from_jsonl(FIXTURES / "near_dup_a.jsonl", "base_train"),
        "rescue_candidates": load_manifest_from_jsonl(
            FIXTURES / "near_dup_b.jsonl", "rescue_candidates"
        ),
    }
    results = check_near_duplicate_overlap(manifests, threshold=0.8)
    assert len(results) >= 1
    assert results[0][1] in ("base_train", "rescue_candidates")
    assert results[0][3] in ("base_train", "rescue_candidates")


def test_high_threshold_misses_near_dups() -> None:
    """At threshold=1.0 only identical texts are flagged."""
    a = load_manifest_from_jsonl(FIXTURES / "near_dup_a.jsonl", "base_train")
    b = load_manifest_from_jsonl(FIXTURES / "near_dup_b.jsonl", "rescue_candidates")
    pairs = find_near_duplicate_pairs(a, b, threshold=1.0)
    assert pairs == []
