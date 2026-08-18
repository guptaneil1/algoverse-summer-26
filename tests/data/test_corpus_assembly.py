"""Tests for assembling a generation's training corpus from synthetic plus rescued text.

This is the join the toy chain never made. The tests below pin the two properties
that make it safe to train on: nothing the policy paid for may be dropped, and the
token ledger must agree with what the policy budgeted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.data.corpus import CorpusAssemblyError, assemble_training_corpus
from human_data_budget.data.manifest import Example, PartitionManifest


def _example(example_id: str, text: str, tokens: int, mode: str = "tail") -> Example:
    return Example(
        example_id=example_id, text=text, origin="human", mode=mode,
        source="wikitext-2-raw-v1", source_offset=0, token_count=tokens,
        content_hash=f"hash-{example_id}", source_revision="rev-abc",
    )


@pytest.fixture
def rescue_manifest() -> PartitionManifest:
    return PartitionManifest.from_examples("rescue_candidates", [
        _example("h-1", "first human passage", 10),
        _example("h-2", "second human passage", 20, mode="common"),
        _example("h-3", "third human passage", 30),
    ])


def _write_synthetic(path: Path, count: int) -> Path:
    path.write_text(json.dumps(
        [{"text": f"synthetic {i}", "cls_score": 0.5} for i in range(count)]
    ), encoding="utf-8")
    return path


def test_generation_zero_is_human_only(tmp_path: Path, rescue_manifest) -> None:
    result = assemble_training_corpus(
        synthetic_corpus=None, rescue_manifest=rescue_manifest,
        selected_example_ids=["h-1", "h-3"], output_path=tmp_path / "data.json",
        generation=0, selection_policy="joint",
    )
    assert result["synthetic_record_count"] == 0
    assert result["human_record_count"] == 2
    assert result["human_token_count"] == 40


def test_later_generations_merge_synthetic_and_rescued(tmp_path: Path, rescue_manifest) -> None:
    synthetic = _write_synthetic(tmp_path / "prev.json", 5)
    result = assemble_training_corpus(
        synthetic_corpus=synthetic, rescue_manifest=rescue_manifest,
        selected_example_ids=["h-2"], output_path=tmp_path / "g3" / "data.json",
        generation=3, selection_policy="selection_only",
    )
    records = json.loads(Path(result["corpus_path"]).read_text(encoding="utf-8"))
    assert len(records) == 6
    assert records[-1]["text"] == "second human passage"
    assert result["human_token_count"] == 20


def test_synthetic_records_keep_their_extra_keys(tmp_path: Path, rescue_manifest) -> None:
    """Detector scores ride along on synthetic records and must survive the join."""
    synthetic = _write_synthetic(tmp_path / "prev.json", 2)
    result = assemble_training_corpus(
        synthetic_corpus=synthetic, rescue_manifest=rescue_manifest,
        selected_example_ids=[], output_path=tmp_path / "data.json",
        generation=1, selection_policy="no_rescue",
    )
    records = json.loads(Path(result["corpus_path"]).read_text(encoding="utf-8"))
    assert records[0]["cls_score"] == 0.5


def test_an_unresolvable_selection_is_an_error_not_a_silent_drop(
    tmp_path: Path, rescue_manifest
) -> None:
    """Spending budget on an example and not training on it voids budget matching."""
    with pytest.raises(CorpusAssemblyError, match="absent from"):
        assemble_training_corpus(
            synthetic_corpus=None, rescue_manifest=rescue_manifest,
            selected_example_ids=["h-1", "h-does-not-exist"],
            output_path=tmp_path / "data.json", generation=0, selection_policy="joint",
        )


def test_textless_manifest_entry_is_an_error(tmp_path: Path) -> None:
    manifest = PartitionManifest.from_examples(
        "rescue_candidates", [_example("h-empty", "", 10)])
    with pytest.raises(CorpusAssemblyError, match="carries no text"):
        assemble_training_corpus(
            synthetic_corpus=None, rescue_manifest=manifest,
            selected_example_ids=["h-empty"], output_path=tmp_path / "data.json",
            generation=0, selection_policy="joint",
        )


def test_provenance_sidecar_carries_the_protocol_fields(
    tmp_path: Path, rescue_manifest
) -> None:
    """PROTOCOL.md section 3 requires each trained-on example to retain provenance."""
    result = assemble_training_corpus(
        synthetic_corpus=None, rescue_manifest=rescue_manifest,
        selected_example_ids=["h-1"], output_path=tmp_path / "data.json",
        generation=2, selection_policy="joint", selection_scores={"h-1": 0.73},
    )
    payload = json.loads(Path(result["provenance_path"]).read_text(encoding="utf-8"))
    record = payload["examples"][0]
    for field in ("example_id", "content_hash", "source", "source_revision", "origin",
                  "mode", "generation", "selection_policy", "selection_score",
                  "selected", "token_count"):
        assert field in record, f"missing provenance field {field}"
    assert record["selection_score"] == 0.73
    assert record["selected"] is True
    assert record["generation"] == 2


def test_corpus_hash_is_recorded_and_stable(tmp_path: Path, rescue_manifest) -> None:
    kwargs = dict(
        synthetic_corpus=None, rescue_manifest=rescue_manifest,
        selected_example_ids=["h-1", "h-2"], generation=0, selection_policy="joint",
    )
    first = assemble_training_corpus(output_path=tmp_path / "a.json", **kwargs)
    second = assemble_training_corpus(output_path=tmp_path / "b.json", **kwargs)
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert len(first["corpus_sha256"]) == 64


def test_malformed_synthetic_corpus_is_rejected(tmp_path: Path, rescue_manifest) -> None:
    bad = tmp_path / "prev.json"
    bad.write_text(json.dumps([{"no_text_key": 1}]), encoding="utf-8")
    with pytest.raises(CorpusAssemblyError, match="no 'text' key"):
        assemble_training_corpus(
            synthetic_corpus=bad, rescue_manifest=rescue_manifest,
            selected_example_ids=[], output_path=tmp_path / "data.json",
            generation=1, selection_policy="joint",
        )
