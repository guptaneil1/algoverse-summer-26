"""Tests for rehydrating manifest text from the pinned corpus.

The offline paths are tested here. Actually resolving text needs the pinned
WikiText-103 download, so that test skips unless the manifests are present and
the build-time extras are installed -- CI has neither.
"""

from __future__ import annotations

import pytest

from human_data_budget.data.hashing import content_hash
from human_data_budget.data.manifest import Example
from human_data_budget.data.wikitext_source import SourceUnavailableError, split_for

MANIFEST = "data/manifests/rescue_candidates.jsonl"


def _example(example_id: str) -> Example:
    return Example(
        example_id=example_id, text="", origin="human", mode="tail",
        source="wikitext-103-v1", source_offset=1, token_count=10,
        content_hash="0" * 64,
    )


@pytest.mark.parametrize("example_id,expected", [
    ("train-77f0ac40398e1a78", "train"),
    ("validation-abc123", "validation"),
    ("test-def456", "test"),
])
def test_split_is_read_from_the_stable_id_prefix(example_id: str, expected: str) -> None:
    assert split_for(_example(example_id)) == expected


def test_an_unrecognised_prefix_is_refused() -> None:
    """Better to fail than to guess a split and resolve the wrong article."""
    with pytest.raises(SourceUnavailableError, match="cannot infer source split"):
        split_for(_example("holdout-abc123"))


@pytest.mark.skipif(
    not __import__("pathlib").Path(MANIFEST).is_file(),
    reason="needs the built partition manifests; run scripts/build_wikitext103_manifests.py",
)
def test_resolved_text_matches_the_frozen_hash() -> None:
    """The property the whole rehydration path exists to guarantee."""
    pytest.importorskip("huggingface_hub")
    pytest.importorskip("pyarrow")
    from human_data_budget.data.manifest import load_manifest_from_jsonl
    from human_data_budget.data.wikitext_source import resolve_text

    manifest = load_manifest_from_jsonl(MANIFEST, "rescue_candidates")
    for example in list(manifest.examples)[:3]:
        assert content_hash(resolve_text(example)) == example.content_hash
