"""The token ledger is recomputed from realized batches, not taken on trust.

Blind spot 3 of `docs/validity/week3_adversarial_audit.md` §8: "Token accounting
is checked at the total level. The validator compares recorded consumed totals
against the frozen budget; it cannot recompute those totals from realized
batches, so a wrong ledger that is internally consistent would pass."

The accounting rules exercised here are the ones already frozen by
`tests/data/test_token_accounting.py`: padding excluded, repeated presentations
counted once per presentation, gradient accumulation counted per micro-batch,
and resume neither double-counting nor dropping the straddling batch.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from human_data_budget.validation.audit import audit_run, check_token_ledger

# Two human rows (5 + 4 real tokens, padded to width 6) and one synthetic row
# (3 real tokens). Padding zeros must never be counted.
BATCHES: list[dict[str, Any]] = [
    {
        "attention_mask": [[1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 0, 0]],
        "origins": ["human", "human"],
    },
    {
        "attention_mask": [[1, 1, 1, 0, 0, 0]],
        "origins": ["synthetic"],
    },
]
TRUE_HUMAN = 9
TRUE_TOTAL = 12


def _write_batches(directory: Path, batches: list[dict[str, Any]]) -> None:
    path = directory / "batch_records.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for batch in batches:
            handle.write(json.dumps(batch) + "\n")


def _codes(checks: list[Any]) -> set[str]:
    return {check.code for check in checks if not check.passed}


def _ledger_codes(
    tmp_path: Path,
    *,
    batches: list[dict[str, Any]] | None = BATCHES,
    human: int = TRUE_HUMAN,
    total: int = TRUE_TOTAL,
) -> set[str]:
    run = tmp_path / "run"
    run.mkdir(parents=True, exist_ok=True)
    if batches is not None:
        _write_batches(run, batches)
    chain_result = {"consumed_human_tokens": human, "consumed_total_tokens": total}
    return _codes(check_token_ledger(run, {}, chain_result))


def test_the_expected_totals_match_the_fixture_they_describe() -> None:
    """Guard against TRUE_HUMAN/TRUE_TOTAL drifting away from BATCHES.

    Counted here by plain arithmetic over the mask rows, deliberately NOT via
    ``consumed_tokens``: deriving the expected value from the function under test
    would make every assertion below tautological. These are hand-countable
    constants describing a literal three lines above them, not measurements.
    """
    human = sum(
        sum(mask)
        for batch in BATCHES
        for mask, origin in zip(batch["attention_mask"], batch["origins"], strict=True)
        if origin == "human"
    )
    total = sum(sum(mask) for batch in BATCHES for mask in batch["attention_mask"])

    assert (human, total) == (TRUE_HUMAN, TRUE_TOTAL) == (9, 12)


# --- the blind spot, closed -------------------------------------------------


def test_internally_consistent_but_wrong_ledger_is_rejected(tmp_path: Path) -> None:
    """The exact attack: the declared ledger agrees with itself and with the budget.

    Both the manifest budget and the chain result say 40/50, so every
    declaration-versus-declaration check passes. Only recomputation from the
    realized batches shows the run actually consumed 9/12.
    """
    codes = _ledger_codes(tmp_path, human=40, total=50)

    assert codes == {"BUDGET_LEDGER_MISMATCH"}


def test_a_correct_ledger_passes(tmp_path: Path) -> None:
    assert _ledger_codes(tmp_path) == set()


def test_human_only_understatement_is_caught(tmp_path: Path) -> None:
    """Understating human tokens is the budget-relevant direction of the lie."""
    assert _ledger_codes(tmp_path, human=TRUE_HUMAN - 1) == {"BUDGET_LEDGER_MISMATCH"}


def test_total_only_overstatement_is_caught(tmp_path: Path) -> None:
    assert _ledger_codes(tmp_path, total=TRUE_TOTAL + 1) == {"BUDGET_LEDGER_MISMATCH"}


# --- insufficient artifacts say so, and never pass --------------------------


def test_absent_batch_records_produce_an_explicit_cannot_recompute(tmp_path: Path) -> None:
    codes = _ledger_codes(tmp_path, batches=None, human=40, total=50)

    assert codes == {"LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE"}
    assert "BUDGET_LEDGER_MISMATCH" not in codes


def test_empty_batch_records_are_not_a_zero_token_run(tmp_path: Path) -> None:
    """An empty file must not recompute to 0 and then 'disagree' or 'agree'."""
    assert _ledger_codes(tmp_path, batches=[]) == {"LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE"}


def test_malformed_batch_records_are_invalid_not_a_limitation(tmp_path: Path) -> None:
    """A mask value that is neither 0 nor 1 must block, not downgrade to 'unknown'."""
    corrupt = [{"attention_mask": [[1, 7]], "origins": ["human"]}]
    assert _ledger_codes(tmp_path, batches=corrupt) == {"ARTIFACT_SCHEMA_INVALID"}


def test_unparseable_batch_records_are_invalid(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "batch_records.jsonl").write_text("{not json\n", encoding="utf-8")

    codes = _codes(check_token_ledger(run, {}, {"consumed_human_tokens": 1}))
    assert codes == {"ARTIFACT_SCHEMA_INVALID"}


def test_cannot_recompute_is_a_limitation_not_a_clean_pass(tmp_path: Path) -> None:
    """The whole point: silence must degrade the classification, not be ignored."""
    run = tmp_path / "run"
    run.mkdir()
    checks = check_token_ledger(run, {}, {"consumed_human_tokens": 1})

    assert checks, "an unrecomputable ledger must emit a check, not nothing"
    assert all(not check.passed for check in checks)


# --- bypasses found by adversarial review ------------------------------------


def test_a_manifest_declared_ledger_path_is_honoured(tmp_path: Path) -> None:
    """Records declared away from the default location are still read.

    Mutation testing found this branch dead: replacing the declared path with the
    default name unconditionally broke no test, so nothing established that a
    non-default declaration was honoured at all.
    """
    run = tmp_path / "run"
    (run / "ledger").mkdir(parents=True)
    _write_batches(run / "ledger", BATCHES)
    manifest = {"artifacts": [{"path": "ledger/batch_records.jsonl", "sha256": "x"}]}

    correct = {"consumed_human_tokens": TRUE_HUMAN, "consumed_total_tokens": TRUE_TOTAL}
    assert _codes(check_token_ledger(run, manifest, correct)) == set()

    wrong = {"consumed_human_tokens": 40, "consumed_total_tokens": 50}
    assert _codes(check_token_ledger(run, manifest, wrong)) == {"BUDGET_LEDGER_MISMATCH"}


def test_a_declared_ledger_is_not_confused_with_a_missing_one(tmp_path: Path) -> None:
    """Declaring a path that does not exist must not silently read the default."""
    run = tmp_path / "run"
    run.mkdir()
    manifest = {"artifacts": [{"path": "ledger/batch_records.jsonl", "sha256": "x"}]}

    assert _codes(check_token_ledger(run, manifest, {"consumed_human_tokens": 1})) == {
        "LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE"
    }


def test_two_contradictory_ledgers_are_ambiguous_not_silently_resolved(
    tmp_path: Path,
) -> None:
    """The manifest must not choose which evidence the auditor is allowed to see.

    A run previously could keep truthful records at the default location and
    declare a hash-correct decoy elsewhere; the decoy alone was read and the run
    certified valid.
    """
    run = tmp_path / "run"
    (run / "decoy").mkdir(parents=True)
    _write_batches(run, BATCHES)
    _write_batches(run / "decoy", [{"attention_mask": [[1] * 40], "origins": ["human"]}])

    manifest = {"artifacts": [{"path": "decoy/batch_records.jsonl", "sha256": "x"}]}
    chain_result = {"consumed_human_tokens": 40, "consumed_total_tokens": 40}

    assert _codes(check_token_ledger(run, manifest, chain_result)) == {
        "ARTIFACT_SCHEMA_INVALID"
    }


def test_the_batch_records_hash_is_recorded_in_the_report(
    make_run: Callable[..., Path],
) -> None:
    """The evidence that decided the ledger verdict must be identifiable."""
    run = make_run()
    _write_batches(run, BATCHES)

    assert "batch_records" in audit_run(run).input_hashes


def test_deleting_the_records_still_downgrades_rather_than_certifies(
    tmp_path: Path,
) -> None:
    """Documented escape hatch: deleting evidence cannot yield a clean pass.

    It does move a wrong ledger from `invalid` to `valid_with_limitation`, which
    is the strongest the auditor can do — it cannot compel an artifact to exist.
    That residual weakness is recorded here rather than hidden.
    """
    wrong_with_evidence = _ledger_codes(tmp_path, human=40, total=50)
    assert wrong_with_evidence == {"BUDGET_LEDGER_MISMATCH"}

    wrong_without_evidence = _ledger_codes(
        tmp_path / "b", batches=None, human=40, total=50
    )
    assert wrong_without_evidence == {"LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE"}


# --- the frozen accounting rules ---------------------------------------------


def _rule(tmp_path: Path, name: str, batches: list[dict[str, Any]], human: int, total: int) -> None:
    run = tmp_path / name
    run.mkdir()
    _write_batches(run, batches)
    correct = {"consumed_human_tokens": human, "consumed_total_tokens": total}
    assert _codes(check_token_ledger(run, {}, correct)) == set(), f"{name}: correct ledger rejected"
    wrong = {"consumed_human_tokens": human + 1, "consumed_total_tokens": total}
    assert _codes(check_token_ledger(run, {}, wrong)) == {"BUDGET_LEDGER_MISMATCH"}, (
        f"{name}: wrong ledger accepted"
    )


def test_padding_is_excluded_from_the_recomputed_ledger(tmp_path: Path) -> None:
    padded = [{"attention_mask": [[1, 1, 1, 0, 0, 0, 0]], "origins": ["human"]}]
    _rule(tmp_path, "padding", padded, human=3, total=3)


def test_each_repeated_presentation_is_counted_again(tmp_path: Path) -> None:
    """Replaying a small human archive must cost the budget every time."""
    single = {"attention_mask": [[1] * 10], "origins": ["human"]}
    _rule(tmp_path, "replay", [single, single, single], human=30, total=30)


def test_every_gradient_accumulation_micro_batch_is_counted(tmp_path: Path) -> None:
    """Accumulation changes when the optimizer steps, not how many tokens it saw."""
    micro = {"attention_mask": [[1] * 8], "origins": ["human"]}
    _rule(tmp_path, "accumulation", [micro] * 4, human=32, total=32)


def test_resume_counts_the_straddling_batch_exactly_once(tmp_path: Path) -> None:
    resumed = [
        {"attention_mask": [[1] * 5], "origins": ["human"]},
        {"attention_mask": [[1] * 6], "origins": ["human"]},
        {"attention_mask": [[1] * 2], "origins": ["human"]},
    ]
    _rule(tmp_path, "resume", resumed, human=13, total=13)


def test_resume_that_replays_a_batch_is_rejected_against_the_true_ledger(
    tmp_path: Path,
) -> None:
    """A resumed run that re-presents the checkpoint batch consumed more, not the same."""
    double_counted = [
        {"attention_mask": [[1] * 5], "origins": ["human"]},
        {"attention_mask": [[1] * 6], "origins": ["human"]},
        {"attention_mask": [[1] * 6], "origins": ["human"]},
        {"attention_mask": [[1] * 2], "origins": ["human"]},
    ]
    run = tmp_path / "replayed"
    run.mkdir()
    _write_batches(run, double_counted)

    # The uninterrupted run's ledger (13) no longer describes this run (19).
    uninterrupted = {"consumed_human_tokens": 13, "consumed_total_tokens": 13}
    assert _codes(check_token_ledger(run, {}, uninterrupted)) == {"BUDGET_LEDGER_MISMATCH"}


def test_resume_that_drops_a_batch_is_rejected(tmp_path: Path) -> None:
    dropped = [
        {"attention_mask": [[1] * 5], "origins": ["human"]},
        {"attention_mask": [[1] * 2], "origins": ["human"]},
    ]
    run = tmp_path / "dropped"
    run.mkdir()
    _write_batches(run, dropped)

    uninterrupted = {"consumed_human_tokens": 13, "consumed_total_tokens": 13}
    assert _codes(check_token_ledger(run, {}, uninterrupted)) == {"BUDGET_LEDGER_MISMATCH"}


# --- end to end through audit_run -------------------------------------------


def test_audit_run_surfaces_a_wrong_ledger_as_invalid(
    make_run: Callable[..., Path],
) -> None:
    """The check must reach the classification, not stop at the helper."""
    run = make_run()
    _write_batches(run, BATCHES)

    report = audit_run(run)
    assert "BUDGET_LEDGER_MISMATCH" in report.reason_codes
    assert report.classification == "invalid"


def test_audit_run_without_batch_records_is_limited_never_plainly_valid(
    make_run: Callable[..., Path],
) -> None:
    """An otherwise-spotless run whose ledger cannot be recomputed is not `valid`."""
    report = audit_run(make_run(batch_records=False))

    assert "LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE" in report.reason_codes
    assert report.classification == "valid_with_limitation"


def test_audit_run_accepts_a_ledger_matching_its_batches(
    make_run: Callable[..., Path],
) -> None:
    def true_ledger(result: dict[str, Any]) -> None:
        result["consumed_human_tokens"] = TRUE_HUMAN
        result["consumed_total_tokens"] = TRUE_TOTAL

    def matching_budget(manifest: dict[str, Any]) -> None:
        manifest["budget"] = {
            "lifetime_human_optimizer_tokens": TRUE_HUMAN,
            "total_optimizer_tokens": TRUE_TOTAL,
        }

    run = make_run(matching_budget, true_ledger)
    _write_batches(run, BATCHES)

    report = audit_run(run)
    assert "BUDGET_LEDGER_MISMATCH" not in report.reason_codes
    assert "LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE" not in report.reason_codes
