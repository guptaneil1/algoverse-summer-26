"""Displacement: human examples replace synthetic records, they do not add to them.

``DECISIONS.md`` P-011, from ``FAILURE_LOG.md`` F-021 and F-021a. Under the additive
assembly the first pilot ran, an arm that spends its human budget trains on strictly
more data than one that does not, so every contrast confounds allocation strategy with
training volume. The measured consequence was realised totals spanning 2.26% across arms
while human spend matched to 0.04%.

These tests pin the invariant that removes it: with a record budget set, every arm's
assembled corpus holds the same number of records whatever its policy selected.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.data.corpus import CorpusAssemblyError, assemble_training_corpus
from human_data_budget.data.hashing import content_hash
from human_data_budget.data.manifest import Example, PartitionManifest

BUDGET = 100


def manifest(count: int = 40) -> PartitionManifest:
    return PartitionManifest.from_examples(
        "rescue_candidates",
        [
            Example(
                example_id=f"train-{index:04d}",
                text=f"human example {index}",
                origin="human",
                mode="tail" if index % 2 else "common",
                source="wikitext-103-v1",
                source_offset=index,
                token_count=100,
                content_hash=content_hash(f"human example {index}"),
                optimizer_token_count=120,
            )
            for index in range(count)
        ],
    )


@pytest.fixture
def synthetic(tmp_path) -> Path:
    path = tmp_path / "synthetic.json"
    path.write_text(
        json.dumps([{"text": f"synthetic {i}"} for i in range(BUDGET)]), encoding="utf-8"
    )
    return path


def assemble(tmp_path, synthetic, selected, budget=BUDGET, name="out"):
    return assemble_training_corpus(
        synthetic_corpus=synthetic,
        rescue_manifest=manifest(),
        selected_example_ids=selected,
        output_path=tmp_path / f"{name}.json",
        generation=1,
        selection_policy="test",
        resolve_text=lambda example: example.text,
        corpus_record_budget=budget,
    )


def test_corpus_size_is_identical_whatever_the_policy_spent(tmp_path, synthetic):
    """The invariant. Arms that spend differently must still train on the same volume."""
    spends = ([], ["train-0000"], [f"train-{i:04d}" for i in range(10)],
              [f"train-{i:04d}" for i in range(40)])
    sizes = set()
    for index, selected in enumerate(spends):
        result = assemble(tmp_path, synthetic, selected, name=f"arm{index}")
        records = json.loads((tmp_path / f"arm{index}.json").read_text(encoding="utf-8"))
        sizes.add(len(records))
        assert result["total_record_count"] == len(records)
    assert sizes == {BUDGET}, (
        f"assembled corpora differ in size across spend levels: {sorted(sizes)}. "
        "That is the F-021 confound: training volume tracks how much the policy spent"
    )


def test_human_records_are_all_present(tmp_path, synthetic):
    """Displacement must drop synthetic records, never the human ones bought."""
    selected = [f"train-{i:04d}" for i in range(30)]
    assemble(tmp_path, synthetic, selected)
    records = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    texts = {r["text"] for r in records}
    for index in range(30):
        assert f"human example {index}" in texts


def test_displacement_count_is_reported(tmp_path, synthetic):
    """Recorded per generation so the volume path is auditable without a re-run."""
    result = assemble(tmp_path, synthetic, [f"train-{i:04d}" for i in range(25)])
    assert result["displaced_synthetic_records"] == 25
    assert result["synthetic_record_count"] == BUDGET - 25
    assert result["human_record_count"] == 25


def test_budget_smaller_than_the_allocation_is_refused(tmp_path, synthetic):
    """A budget that cannot hold the human data it exists to make room for is an error."""
    with pytest.raises(CorpusAssemblyError, match="cannot displace"):
        assemble(tmp_path, synthetic, [f"train-{i:04d}" for i in range(40)], budget=10)


def test_no_budget_restores_additive_assembly(tmp_path, synthetic):
    """The pilot's artifacts must stay reproducible.

    Passing no budget keeps the behaviour the executed run used, so its corpora can be
    rebuilt byte-for-byte. Displacement is opt-in, not retroactive.
    """
    result = assemble_training_corpus(
        synthetic_corpus=synthetic,
        rescue_manifest=manifest(),
        selected_example_ids=[f"train-{i:04d}" for i in range(10)],
        output_path=tmp_path / "additive.json",
        generation=1,
        selection_policy="test",
        resolve_text=lambda example: example.text,
    )
    records = json.loads((tmp_path / "additive.json").read_text(encoding="utf-8"))
    assert len(records) == BUDGET + 10, "additive path changed; pilot artifacts would not rebuild"
    assert result["displaced_synthetic_records"] == 0
    assert result["corpus_record_budget"] is None


def test_the_control_arm_trains_on_the_same_volume(tmp_path, synthetic):
    """The contrast this fixes that nobody had flagged.

    Under addition the no-rescue control trains on less data than every spending arm,
    so "spending helps" cannot be separated from "more data helps". Under displacement
    the control's corpus is the same size as everyone else's.
    """
    control = assemble(tmp_path, synthetic, [], name="control")
    spender = assemble(tmp_path, synthetic, [f"train-{i:04d}" for i in range(20)],
                       name="spender")
    assert control["total_record_count"] == spender["total_record_count"] == BUDGET
    assert control["human_record_count"] == 0
