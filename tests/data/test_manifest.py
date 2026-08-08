"""Tests for manifest loading, stable IDs, content hashing, and provenance validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from human_data_budget.data.manifest import (
    Example,
    ManifestError,
    PartitionManifest,
    ProvenanceError,
    load_manifest_from_jsonl,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _example(**kwargs) -> Example:
    defaults = {
        "example_id": "x-1",
        "text": "Some sample text.",
        "origin": "human",
        "mode": "common",
        "source": "wikitext-103-v1",
        "source_offset": 0,
        "token_count": 3,
    }
    defaults.update(kwargs)
    return Example.from_dict(defaults)


# --- content hashing ---


def test_content_hash_is_deterministic() -> None:
    ex1 = _example(example_id="x-1", text="hello world")
    ex2 = _example(example_id="x-2", text="hello world")
    assert ex1.content_hash == ex2.content_hash


def test_content_hash_matches_normalized_sha256() -> None:
    text = "hello   world"
    ex = _example(text=text)
    import unicodedata

    normalized = " ".join(unicodedata.normalize("NFKC", text).split()).strip()
    expected = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    assert ex.content_hash == expected


def test_different_texts_give_different_hashes() -> None:
    assert _example(text="hello").content_hash != _example(text="world").content_hash


# --- partition manifest hash ---


def test_manifest_hash_is_deterministic() -> None:
    m1 = load_manifest_from_jsonl(FIXTURES / "base_train.jsonl", "base_train")
    m2 = load_manifest_from_jsonl(FIXTURES / "base_train.jsonl", "base_train")
    assert m1.manifest_hash == m2.manifest_hash


def test_different_manifests_have_different_hashes() -> None:
    m1 = load_manifest_from_jsonl(FIXTURES / "base_train.jsonl", "base_train")
    m2 = load_manifest_from_jsonl(FIXTURES / "rescue_candidates.jsonl", "rescue_candidates")
    assert m1.manifest_hash != m2.manifest_hash


# --- loading all five partitions ---


@pytest.mark.parametrize(
    ("fname", "partition", "min_examples"),
    [
        ("base_train.jsonl", "base_train", 5),
        ("rescue_candidates.jsonl", "rescue_candidates", 3),
        ("prompts.jsonl", "prompts", 2),
        ("validation.jsonl", "validation", 2),
        ("test.jsonl", "test", 4),
    ],
)
def test_load_clean_manifest(fname: str, partition: str, min_examples: int) -> None:
    m = load_manifest_from_jsonl(FIXTURES / fname, partition)
    assert m.partition == partition
    assert len(m.examples) >= min_examples
    assert m.manifest_hash


# --- provenance validation ---


def test_missing_source_raises_provenance_error() -> None:
    with pytest.raises(ProvenanceError):
        load_manifest_from_jsonl(FIXTURES / "corrupt_missing_source.jsonl", "base_train")


def test_missing_source_offset_raises_provenance_error() -> None:
    with pytest.raises(ProvenanceError):
        Example.from_dict(
            {
                "example_id": "x",
                "text": "t",
                "origin": "human",
                "mode": "common",
                "source": "wikitext-103-v1",
                "token_count": 1,
            }
        )


def test_missing_example_id_raises_manifest_error() -> None:
    with pytest.raises(ManifestError):
        Example.from_dict(
            {
                "text": "t",
                "origin": "human",
                "mode": "common",
                "source": "wikitext-103-v1",
                "source_offset": 0,
                "token_count": 1,
            }
        )


def test_invalid_partition_name_raises_manifest_error() -> None:
    examples = [_example()]
    with pytest.raises(ManifestError, match="Unknown partition"):
        PartitionManifest.from_examples("bad_partition", examples)


# --- incomplete provenance in file ---


def test_incomplete_provenance_blocked_at_load_time() -> None:
    """The corrupt fixture is rejected during JSONL loading, not silently accepted."""
    with pytest.raises(ProvenanceError):
        load_manifest_from_jsonl(FIXTURES / "corrupt_missing_source.jsonl", "base_train")


# --- mode and origin fields preserved ---


def test_modes_and_origins_preserved() -> None:
    m = load_manifest_from_jsonl(FIXTURES / "base_train.jsonl", "base_train")
    modes = {ex.mode for ex in m.examples}
    assert "common" in modes
    assert "tail" in modes
    assert all(ex.origin == "human" for ex in m.examples)


# --- frozen, text-free manifest records (immutable manifests; raw text is never committed) ---


def test_hash_only_record_preserves_precomputed_hash() -> None:
    """A frozen record with content_hash and no text must not be re-hashed from empty text."""
    real_hash = _example(text="the quick brown fox").content_hash
    record = {
        "example_id": "frozen-1",
        "content_hash": real_hash,
        "origin": "human",
        "mode": "common",
        "source": "wikitext-103-v1",
        "source_offset": 0,
        "token_count": 4,
    }
    ex = Example.from_dict(record)
    assert ex.content_hash == real_hash
    assert ex.text == ""


def test_hash_only_record_round_trips_through_to_dict() -> None:
    real_hash = _example(text="round trip check").content_hash
    record = {
        "example_id": "frozen-2",
        "content_hash": real_hash,
        "origin": "human",
        "mode": "tail",
        "source": "wikitext-103-v1",
        "source_offset": 5,
        "token_count": 3,
    }
    manifest = PartitionManifest.from_examples("base_train", [Example.from_dict(record)])
    assert manifest.to_dict()["examples"][0]["content_hash"] == real_hash


def test_record_without_text_or_hash_rejected() -> None:
    with pytest.raises(ManifestError, match="either 'text' or a precomputed 'content_hash'"):
        Example.from_dict(
            {
                "example_id": "x",
                "origin": "human",
                "mode": "common",
                "source": "wikitext-103-v1",
                "source_offset": 0,
                "token_count": 1,
            }
        )


def test_mismatched_text_and_content_hash_rejected() -> None:
    """A record cannot carry text and a content_hash that disagree with each other."""
    with pytest.raises(ManifestError, match="content_hash mismatch"):
        Example.from_dict(
            {
                "example_id": "x",
                "text": "actual text",
                "content_hash": "0" * 64,
                "origin": "human",
                "mode": "common",
                "source": "wikitext-103-v1",
                "source_offset": 0,
                "token_count": 2,
            }
        )
