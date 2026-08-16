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
import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from human_data_budget.data.overlap import _jaccard, _shingle
from human_data_budget.validation.audit import (
    FORBIDDEN_PARTITION_PAIRS,
    NEAR_DUPLICATE_THRESHOLD,
    audit_run,
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


def _load_corpus_scanner() -> Any:
    """Load the real corpus-scale scanner so its metric is used, not a copy of it.

    Importing the shipped `_word_shingles` rather than reimplementing it is the
    point: a hand-copied version could drift and the comparison below would then
    prove nothing about the operating point the data workstream actually froze.
    """
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "build_wikitext103_manifests", root / "scripts" / "build_wikitext103_manifests.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


@pytest.mark.parametrize(("left", "right"), FORBIDDEN_PARTITION_PAIRS)
def test_a_reworded_leak_is_caught_in_every_forbidden_pair(left: str, right: str) -> None:
    """Each of the five pairs, individually — not one representative pair.

    An earlier version of this test claimed to scan every forbidden pair while
    exercising exactly one, leaving the central train/test constraint uncovered.
    """
    seed = "Radiolarian microfossils indicate ancient ocean temperatures."
    variant = "Radiolarian microfossils indicate ancient ocean temperature."

    partitions = _partitions(UNRELATED)
    partitions[left] = [_entry(f"{left}-1", seed)]
    partitions[right] = [_entry(f"{right}-1", variant)]

    assert partitions[left][0]["content_hash"] != partitions[right][0]["content_hash"]
    codes = _codes(check_near_duplicate_separation(partitions))
    assert "SEPARATION_NEAR_DUPLICATE" in codes, f"{left}|{right} not scanned"


@pytest.mark.parametrize(("left", "right"), FORBIDDEN_PARTITION_PAIRS)
def test_an_exact_duplicate_is_caught_in_every_forbidden_pair(left: str, right: str) -> None:
    shared = "Radiolarian microfossils indicate ancient ocean temperatures."
    partitions = _partitions(UNRELATED)
    partitions[left] = [_entry(f"{left}-1", shared)]
    partitions[right] = [_entry(f"{right}-1", shared)]

    assert "SEPARATION_OVERLAP" in _codes(check_separation({"data": {"partitions": partitions}}))


def test_a_clean_corpus_is_checked_not_merely_unflagged() -> None:
    """Asserting the absence of a code cannot distinguish clean from never-checked."""
    checks = check_near_duplicate_separation(_partitions(UNRELATED))
    scanned = [c for c in checks if c.name.startswith("separation_near_duplicate:") and c.passed]

    assert len(scanned) == len(FORBIDDEN_PARTITION_PAIRS)


def test_a_near_duplicate_leak_makes_the_whole_run_invalid(
    make_run: Callable[..., Path],
) -> None:
    """End to end through audit_run, not just the helper."""

    def leak(manifest: dict[str, Any]) -> None:
        # The shared conftest fixture uses one-word texts ("alpha", "beta"),
        # which are too short for character-5-gram similarity to mean anything.
        # Both sides are replaced with sentence-length text here.
        partitions = manifest["data"]["partitions"]
        partitions["final_human_test"] = [_entry("fht-1", TEST_TEXT)]
        partitions["generation_prompts"] = [_entry("gp-leak", REWORDED_LEAK)]

    report = audit_run(make_run(leak))
    assert "SEPARATION_NEAR_DUPLICATE" in report.reason_codes
    assert report.classification == "invalid"


# --- "not checked" is never reported as "clean" -----------------------------


# --- bypasses found by adversarial review, now closed ----------------------


def test_a_junk_partitions_block_does_not_certify_a_run() -> None:
    """`{"junk": []}` is truthy and previously passed the provenance guard outright."""
    codes = _codes(check_separation({"data": {"partitions": {"junk": []}}}))

    assert "SEPARATION_MISSING_PROVENANCE" in codes


def test_the_five_real_names_mapped_to_empty_lists_do_not_certify_a_run() -> None:
    empty = {name: [] for name in _partitions(UNRELATED)}
    codes = _codes(check_separation({"data": {"partitions": empty}}))

    assert "SEPARATION_MISSING_PROVENANCE" in codes


def test_an_unrecognised_partition_name_is_rejected_even_when_all_five_are_valid() -> None:
    """A complete, valid block plus one junk key must not certify.

    Distinct from the all-junk case above, which is caught by the
    absent-partition rule. Nothing else covers the unrecognised-name rule.
    """
    partitions = _partitions(UNRELATED)
    partitions["junk"] = [_entry("junk-1", "Smuggled content nobody declared.")]

    assert "SEPARATION_MISSING_PROVENANCE" in _codes(
        check_separation({"data": {"partitions": partitions}})
    )


def test_a_missing_partition_is_rejected() -> None:
    partitions = _partitions(UNRELATED)
    del partitions["final_human_test"]

    assert "SEPARATION_MISSING_PROVENANCE" in _codes(
        check_separation({"data": {"partitions": partitions}})
    )


def test_blanking_one_decoy_entry_no_longer_disables_the_whole_pair() -> None:
    """The all-or-nothing text rule was a cheaper bypass than the leak it guarded.

    Blanking `text` on one innocuous example used to suppress near-duplicate
    checking for every pair touching that partition, downgrading a real leak from
    `invalid` to `valid_with_limitation`.
    """
    partitions = _partitions(REWORDED_LEAK)
    partitions["final_human_test"].append(_entry("fht-decoy", "An unrelated decoy sentence."))
    partitions["final_human_test"][-1].pop("text")

    codes = _codes(check_near_duplicate_separation(partitions))
    assert "SEPARATION_NEAR_DUPLICATE" in codes
    assert "LIMIT_NEAR_DUPLICATE_NOT_CHECKED" in codes


def test_a_blinded_entry_is_named_in_the_report() -> None:
    partitions = _partitions(UNRELATED)
    partitions["validation"][0].pop("text")

    detail = " ".join(
        check.detail for check in check_near_duplicate_separation(partitions) if not check.passed
    )
    assert "validation:val-1" in detail


# --- text must be the text the hash identifies ------------------------------


def test_substituted_text_with_a_truthful_hash_is_rejected() -> None:
    """The round-2 fix presumed `text` was trustworthy evidence. It was not.

    Deleting text costs a limitation. Substituting it cost nothing: a run could
    declare the true stable_id, content_hash, source_dataset and origin — all
    verifiable against hashed artifacts — and swap only `text` for a decoy. Near
    duplicate detection then compared decoys, found nothing, and certified a real
    cross-partition leak with zero reason codes.
    """
    partitions = _partitions(None)
    partitions["base_human_train"] = [_entry("bht-1", REWORDED_LEAK)]
    partitions["final_human_test"] = [_entry("fht-1", TEST_TEXT)]
    partitions["generation_prompts"] = [_entry("gp-1", UNRELATED)]

    # Hashes still describe the real (leaking) text; only the text is swapped.
    partitions["base_human_train"][0]["text"] = "An innocuous decoy sentence here."
    partitions["final_human_test"][0]["text"] = "Another wholly unrelated decoy line."

    codes = _codes(check_separation({"data": {"partitions": partitions}}))
    assert "SEPARATION_PROVENANCE_INCONSISTENT" in codes


def test_matching_text_and_hash_raise_no_consistency_complaint() -> None:
    assert "SEPARATION_PROVENANCE_INCONSISTENT" not in _codes(
        check_separation({"data": {"partitions": _partitions(UNRELATED)}})
    )


def test_an_entry_without_text_is_not_treated_as_inconsistent() -> None:
    """Absent text is a coverage limitation, not a hash contradiction."""
    partitions = _partitions(UNRELATED)
    partitions["validation"][0].pop("text")

    assert "SEPARATION_PROVENANCE_INCONSISTENT" not in _codes(
        check_separation({"data": {"partitions": partitions}})
    )


def test_a_blinded_counterpart_does_not_yield_a_passing_pair_check() -> None:
    """Finding nothing is only 'clean' if everything was compared.

    Blinding the leak's counterpart while leaving a second entry readable kept the
    partition non-empty, so the pair was compared over the remainder and recorded
    as a PASSING check — 'not checked' reported as 'checked and clean', the exact
    failure the surrounding code claims to prevent.
    """
    partitions = _partitions(None)
    partitions["base_human_train"] = [_entry("bht-1", REWORDED_LEAK)]
    partitions["final_human_test"] = [
        _entry("fht-1", TEST_TEXT),
        _entry("fht-2", "A perfectly ordinary held-out sentence."),
    ]
    partitions["final_human_test"][0].pop("text")
    partitions["generation_prompts"] = [_entry("gp-1", UNRELATED)]

    checks = check_near_duplicate_separation(partitions)
    pair = next(
        c
        for c in checks
        if c.name == "separation_near_duplicate:base_human_train|final_human_test"
    )
    assert not pair.passed
    assert pair.code == "LIMIT_NEAR_DUPLICATE_NOT_CHECKED"


# --- residual gap: Jaccard measures no containment --------------------------


def test_a_padded_verbatim_leak_is_not_caught_and_that_gap_is_documented() -> None:
    """A verbatim copy of a test example, padded with filler, evades the check.

    `_jaccard` is symmetric set overlap, so surrounding a stolen example with
    unrelated text collapses the score even though the example is present
    character for character. No paraphrasing skill is required — padding suffices.

    Closing this needs an asymmetric containment measure, which would be new
    detection logic rather than a wiring-in of what exists, so it is pinned here
    and left to the data owner. Expected to fail when containment lands; delete
    it then.
    """
    filler = (
        "This introductory sentence is entirely unrelated to the held-out material. "
        "It exists only to dilute the surface overlap of what follows. "
    )
    padded = filler + TEST_TEXT + " " + filler

    assert TEST_TEXT in padded, "the leak must remain verbatim"
    similarity = _jaccard(_shingle(TEST_TEXT, 5), _shingle(padded, 5))
    assert similarity < NEAR_DUPLICATE_THRESHOLD

    partitions = _partitions(UNRELATED)
    partitions["base_human_train"] = [_entry("bht-1", padded)]
    codes = _codes(check_separation({"data": {"partitions": partitions}}))
    assert "SEPARATION_NEAR_DUPLICATE" not in codes
    assert "SEPARATION_OVERLAP" not in codes


def test_the_two_shipped_operating_points_disagree() -> None:
    """0.8 is shared; the metric is not. Pins the contradiction for the data owner.

    `docs/data/overlap_report.md` §3 records the corpus-scale scan as word-8-gram
    Jaccard; `data/overlap.py`, which the auditor reuses, is character-5-gram.

    The texts here are deliberately 16 words long. The short sentences used
    elsewhere in this file fall into `_word_shingles`' `len(words) < n` fallback,
    which collapses the whole string into one shingle and reduces word-8-gram to
    exact-string equality — that would show a disagreement produced by the
    degenerate path rather than by 8-gram overlap. The shingle-count assertion
    below pins that the real path ran.
    """
    _word_shingles = _load_corpus_scanner()._word_shingles

    long_a = (
        "Radiolarian microfossils recovered from deep ocean sediment cores "
        "indicate ancient sea surface temperatures across long intervals."
    )
    long_b = long_a.replace("temperatures", "temperature")

    real_shingles = _word_shingles(long_a)
    assert len(real_shingles) > 1, "fallback path taken; the comparison would be degenerate"

    char_5 = _jaccard(_shingle(long_a, 5), _shingle(long_b, 5))
    word_8 = _jaccard(real_shingles, _word_shingles(long_b))

    # One word changed: caught by the auditor's metric, missed by the corpus scan's.
    assert char_5 >= NEAR_DUPLICATE_THRESHOLD
    assert word_8 < NEAR_DUPLICATE_THRESHOLD


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


def test_only_five_of_ten_partition_pairs_are_checked_at_all() -> None:
    """Pins a pre-existing gap this task inherits rather than introduces.

    `PROTOCOL.md` §3 lists five partitions and requires them to be disjoint,
    which is ten pairs. `FORBIDDEN_PARTITION_PAIRS` enumerates five, so the other
    five are checked for neither exact nor near-duplicate overlap — the
    near-duplicate wiring reuses the same list and inherits the same reach.

    Widening the list would reclassify runs, so it is the validator owner's
    decision, not a side effect of closing this blind spot. Pinned in the style
    of `FAILURE_LOG.md` F-001: this test is expected to fail when the list is
    widened, and should be deleted then.
    """
    from itertools import combinations

    from human_data_budget.runner.provenance import RUN_MANIFEST_PARTITIONS
    from human_data_budget.validation.audit import FORBIDDEN_PARTITION_PAIRS

    checked = {frozenset(pair) for pair in FORBIDDEN_PARTITION_PAIRS}
    every_pair = {frozenset(pair) for pair in combinations(RUN_MANIFEST_PARTITIONS, 2)}

    assert len(every_pair) == 10
    assert len(checked) == 5
    assert {tuple(sorted(pair)) for pair in every_pair - checked} == {
        ("base_human_train", "generation_prompts"),
        ("base_human_train", "validation"),
        ("generation_prompts", "rescue_candidates"),
        ("generation_prompts", "validation"),
        ("rescue_candidates", "validation"),
    }


def test_an_unchecked_pair_leaks_verbatim_without_detection() -> None:
    """Demonstrates the consequence: an identical copy in an unchecked pair passes."""
    shared = "Municipal archives catalogue property records."
    partitions = _partitions(UNRELATED)
    partitions["base_human_train"] = [_entry("bht-1", shared)]
    partitions["validation"] = [_entry("val-1", shared)]

    codes = _codes(check_separation({"data": {"partitions": partitions}}))
    assert "SEPARATION_OVERLAP" not in codes
    assert "SEPARATION_NEAR_DUPLICATE" not in codes


def test_reworded_leak_scores_above_the_threshold_and_paraphrase_below() -> None:
    """The measured separation between what is and is not caught."""
    caught = _jaccard(_shingle(TEST_TEXT, 5), _shingle(REWORDED_LEAK, 5))
    missed = _jaccard(_shingle(TEST_TEXT, 5), _shingle(SEMANTIC_PARAPHRASE, 5))

    assert caught >= NEAR_DUPLICATE_THRESHOLD > missed
