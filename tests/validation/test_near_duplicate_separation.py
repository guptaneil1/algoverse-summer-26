"""Near-duplicate leakage across a partition boundary is rejected.

Blind spot 2 of `docs/validity/week3_adversarial_audit.md` §8: "Near-duplicate
detection is not implemented. Overlap is exact-hash only. Paraphrase or
near-duplicate leakage passes." The detection logic already existed in
`human_data_budget.data.overlap`; the auditor did not call it.

The similarity threshold is a frozen scientific parameter with no freeze record,
so these tests exercise the value already implemented in `overlap.py` (0.8).
They deliberately pin the detector's *limit* as well as its reach — see
`test_semantic_paraphrase_is_not_caught_at_the_frozen_threshold`.
"""

from __future__ import annotations

import hashlib
from typing import Any

from human_data_budget.data.overlap import _jaccard, _shingle
from human_data_budget.validation.audit import (
    NEAR_DUPLICATE_THRESHOLD,
    check_near_duplicate_separation,
    check_separation,
)

# One sentence from the final human test partition, and variants of it.
TEST_TEXT = "Radiolarian microfossils indicate ancient ocean temperatures."
REWORDED_LEAK = "Radiolarian microfossils indicate ancient ocean temperature."
SEMANTIC_PARAPHRASE = (
    "Ancient sea temperatures are revealed by the tiny shells of radiolarians."
)
UNRELATED = "Regional cuisine reflects the produce available each season."


def _entry(stable_id: str, text: str, origin: str = "human") -> dict[str, Any]:
    return {
        "stable_id": stable_id,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_dataset": "toy-fixture-corpus/v1",
        "origin": origin,
        "text": text,
    }


def _partitions(prompt_text: str | None, **overrides: Any) -> dict[str, list[dict[str, Any]]]:
    """Five partitions; ``prompt_text`` seeds generation_prompts with one example."""
    partitions: dict[str, list[dict[str, Any]]] = {
        "base_human_train": [_entry("bht-1", "Ancient trade routes shaped coastal towns.")],
        "rescue_candidates": [_entry("rc-1", "A rare-mode human fixture.")],
        "generation_prompts": [] if prompt_text is None else [_entry("gp-1", prompt_text)],
        "validation": [_entry("val-1", "Municipal archives catalogue property records.")],
        "final_human_test": [_entry("fht-1", TEST_TEXT)],
    }
    partitions.update(overrides)
    return partitions


def _codes(checks: list[Any]) -> set[str]:
    return {check.code for check in checks if not check.passed}


# --- the blind spot, closed -------------------------------------------------


def test_reworded_leak_into_the_test_partition_is_rejected() -> None:
    """A leak reworded just enough to change its hash must not pass as valid.

    This is the attack the exact-hash check cannot see: the two strings differ,
    so their SHA-256 digests differ, and separation looked clean.
    """
    partitions = _partitions(REWORDED_LEAK)

    assert (
        partitions["generation_prompts"][0]["content_hash"]
        != partitions["final_human_test"][0]["content_hash"]
    ), "fixture must not be an exact duplicate, or it would prove nothing new"

    assert "SEPARATION_NEAR_DUPLICATE" in _codes(check_near_duplicate_separation(partitions))


def test_the_auditor_itself_rejects_the_reworded_leak() -> None:
    """Wired into check_separation, not merely available as a helper."""
    manifest = {"data": {"partitions": _partitions(REWORDED_LEAK)}}

    assert "SEPARATION_NEAR_DUPLICATE" in _codes(check_separation(manifest))


def test_exact_duplicate_detection_still_works() -> None:
    """The pre-existing exact-hash check must not regress."""
    manifest = {"data": {"partitions": _partitions(TEST_TEXT)}}
    codes = _codes(check_separation(manifest))

    assert "SEPARATION_OVERLAP" in codes


def test_clean_corpus_is_not_falsely_flagged() -> None:
    """Legitimate, unrelated content across partitions stays valid."""
    manifest = {"data": {"partitions": _partitions(UNRELATED)}}
    codes = _codes(check_separation(manifest))

    assert "SEPARATION_NEAR_DUPLICATE" not in codes
    assert "SEPARATION_OVERLAP" not in codes


def test_every_forbidden_pair_is_scanned_not_just_the_test_partition() -> None:
    """base_human_train|rescue_candidates is a forbidden pair too."""
    partitions = _partitions(UNRELATED)
    partitions["rescue_candidates"] = [_entry("rc-1", "Ancient trade routes shaped coastal town.")]

    assert "SEPARATION_NEAR_DUPLICATE" in _codes(check_near_duplicate_separation(partitions))


# --- "not checked" is never reported as "clean" -----------------------------


def test_partitions_without_text_report_an_explicit_limitation() -> None:
    partitions = _partitions(UNRELATED)
    for entries in partitions.values():
        for entry in entries:
            entry.pop("text")

    codes = _codes(check_near_duplicate_separation(partitions))
    assert codes == {"LIMIT_NEAR_DUPLICATE_NOT_CHECKED"}


def test_partially_missing_text_does_not_silently_pass() -> None:
    """One unreadable example must not yield a confident 'no duplicates found'."""
    partitions = _partitions(REWORDED_LEAK)
    partitions["final_human_test"][0].pop("text")

    codes = _codes(check_near_duplicate_separation(partitions))
    assert "LIMIT_NEAR_DUPLICATE_NOT_CHECKED" in codes
    assert "SEPARATION_NEAR_DUPLICATE" not in codes


def test_blank_text_counts_as_missing_not_as_an_empty_document() -> None:
    partitions = _partitions(REWORDED_LEAK)
    partitions["final_human_test"][0]["text"] = "   "

    assert "LIMIT_NEAR_DUPLICATE_NOT_CHECKED" in _codes(
        check_near_duplicate_separation(partitions)
    )


# --- the residual gap, pinned rather than hidden ----------------------------


def test_the_frozen_threshold_is_the_value_already_in_overlap_py() -> None:
    """No new threshold was chosen; 0.8 is overlap.py's own default."""
    import inspect

    from human_data_budget.data.overlap import find_near_duplicate_pairs

    default = inspect.signature(find_near_duplicate_pairs).parameters["threshold"].default
    assert NEAR_DUPLICATE_THRESHOLD == default == 0.8


def test_semantic_paraphrase_is_not_caught_at_the_frozen_threshold() -> None:
    """A restatement that reuses little surface text is NOT detected. Measured, not assumed.

    Character 5-gram Jaccard is a surface-overlap measure. The reworded leak
    above scores ~0.95 and is caught; this paraphrase carries the same meaning in
    different words and scores ~0.17, far below the frozen 0.8 threshold.

    Wiring `overlap.py` into the auditor therefore closes near-duplicate leakage,
    NOT semantic paraphrase leakage. This test exists so that gap fails visibly
    if anyone later reads the audit as claiming paraphrase coverage. It should be
    replaced — not deleted — if the data owner freezes a semantic detector.
    """
    similarity = _jaccard(_shingle(TEST_TEXT, 5), _shingle(SEMANTIC_PARAPHRASE, 5))

    assert similarity < 0.2
    assert similarity < NEAR_DUPLICATE_THRESHOLD

    partitions = _partitions(SEMANTIC_PARAPHRASE)
    assert "SEPARATION_NEAR_DUPLICATE" not in _codes(
        check_near_duplicate_separation(partitions)
    )


def test_reworded_leak_scores_above_the_threshold_and_paraphrase_below() -> None:
    """The measured separation between what is and is not caught."""
    caught = _jaccard(_shingle(TEST_TEXT, 5), _shingle(REWORDED_LEAK, 5))
    missed = _jaccard(_shingle(TEST_TEXT, 5), _shingle(SEMANTIC_PARAPHRASE, 5))

    assert caught >= NEAR_DUPLICATE_THRESHOLD > missed
