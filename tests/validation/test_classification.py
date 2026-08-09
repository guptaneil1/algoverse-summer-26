"""Each adversarial fixture must deterministically yield one frozen classification."""

from collections.abc import Callable
from pathlib import Path

import pytest

from human_data_budget.validation.audit import audit_run
from human_data_budget.validation.classification import (
    INVALID,
    LIMITING_CODES,
    VALID,
    VALID_WITH_LIMITATION,
    CheckResult,
    classify,
    describe,
)


def test_clean_run_is_valid(valid_run: Path) -> None:
    report = audit_run(valid_run)
    assert report.classification == VALID
    assert report.reason_codes == []
    assert report.checks_failed == []


def test_classification_is_deterministic(valid_run: Path) -> None:
    first = audit_run(valid_run, audited_at="2026-08-09T00:00:00+00:00")
    second = audit_run(valid_run, audited_at="2026-08-09T00:00:00+00:00")
    assert first.to_dict() == second.to_dict()


def test_prompt_to_final_test_overlap_is_invalid(make_run: Callable[..., Path]) -> None:
    def leak(manifest: dict) -> None:
        partitions = manifest["data"]["partitions"]
        partitions["generation_prompts"] = list(partitions["final_human_test"])

    report = audit_run(make_run(leak))
    assert report.classification == INVALID
    assert "SEPARATION_OVERLAP" in report.reason_codes


def test_rescue_candidate_to_final_test_overlap_is_invalid(make_run: Callable[..., Path]) -> None:
    def leak(manifest: dict) -> None:
        partitions = manifest["data"]["partitions"]
        partitions["rescue_candidates"].append(partitions["final_human_test"][0])

    report = audit_run(make_run(leak))
    assert report.classification == INVALID
    assert "SEPARATION_OVERLAP" in report.reason_codes


def test_missing_stable_id_is_invalid(make_run: Callable[..., Path]) -> None:
    def strip_id(manifest: dict) -> None:
        manifest["data"]["partitions"]["base_human_train"][0]["stable_id"] = ""

    report = audit_run(make_run(strip_id))
    assert report.classification == INVALID
    assert "SEPARATION_MISSING_ID" in report.reason_codes


def test_missing_provenance_field_is_invalid(make_run: Callable[..., Path]) -> None:
    def strip_source(manifest: dict) -> None:
        del manifest["data"]["partitions"]["base_human_train"][0]["source_dataset"]

    report = audit_run(make_run(strip_source))
    assert report.classification == INVALID
    assert "SEPARATION_MISSING_PROVENANCE" in report.reason_codes


def test_human_budget_mismatch_is_invalid(make_run: Callable[..., Path]) -> None:
    def overspend(result: dict) -> None:
        result["consumed_human_tokens"] = 250

    report = audit_run(make_run(None, overspend))
    assert report.classification == INVALID
    assert "BUDGET_HUMAN_MISMATCH" in report.reason_codes


def test_total_budget_mismatch_is_invalid(make_run: Callable[..., Path]) -> None:
    def overspend(result: dict) -> None:
        result["consumed_total_tokens"] = 1200

    report = audit_run(make_run(None, overspend))
    assert report.classification == INVALID
    assert "BUDGET_TOTAL_MISMATCH" in report.reason_codes


def test_seed_mismatch_is_invalid(make_run: Callable[..., Path]) -> None:
    def reseed(result: dict) -> None:
        result["chain_seed"] = 99

    report = audit_run(make_run(None, reseed))
    assert report.classification == INVALID
    assert "PROTOCOL_SEED_MISMATCH" in report.reason_codes


def test_policy_mismatch_is_invalid(make_run: Callable[..., Path]) -> None:
    def swap(result: dict) -> None:
        result["policy"] = "random"

    report = audit_run(make_run(None, swap))
    assert report.classification == INVALID
    assert "PROTOCOL_POLICY_MISMATCH" in report.reason_codes


def test_horizon_exceeded_is_invalid(make_run: Callable[..., Path]) -> None:
    def overrun(result: dict) -> None:
        result["generations_completed"] = 5

    report = audit_run(make_run(None, overrun))
    assert report.classification == INVALID
    assert "PROTOCOL_HORIZON_MISMATCH" in report.reason_codes


def test_dirty_working_tree_is_invalid(make_run: Callable[..., Path]) -> None:
    def dirty(manifest: dict) -> None:
        manifest["working_tree_clean"] = False

    report = audit_run(make_run(dirty))
    assert report.classification == INVALID
    assert "COMMIT_DIRTY" in report.reason_codes


def test_non_terminal_status_is_invalid(make_run: Callable[..., Path]) -> None:
    def running(manifest: dict) -> None:
        manifest["status"] = "running"

    report = audit_run(make_run(running))
    assert report.classification == INVALID
    assert "PROTOCOL_STATUS_NOT_TERMINAL" in report.reason_codes


def test_out_of_range_tail_retention_is_invalid(make_run: Callable[..., Path]) -> None:
    def impossible(result: dict) -> None:
        result["metrics"][1]["tail_retention"] = 1.4

    report = audit_run(make_run(None, impossible))
    assert report.classification == INVALID
    assert "EVALUATION_TAIL_OUT_OF_RANGE" in report.reason_codes


def test_non_finite_nll_is_invalid(make_run: Callable[..., Path]) -> None:
    def broken(result: dict) -> None:
        result["metrics"][0]["human_nll"] = float("inf")

    report = audit_run(make_run(None, broken))
    assert report.classification == INVALID
    assert "EVALUATION_NLL_NOT_FINITE" in report.reason_codes


def test_reduced_generations_is_valid_with_limitation(make_run: Callable[..., Path]) -> None:
    def short(result: dict) -> None:
        result["generations_completed"] = 1
        result["metrics"] = result["metrics"][:1]

    report = audit_run(make_run(None, short))
    assert report.classification == VALID_WITH_LIMITATION
    assert "LIMIT_REDUCED_GENERATIONS" in report.reason_codes
    assert report.limitations


def test_empty_environment_is_valid_with_limitation(make_run: Callable[..., Path]) -> None:
    def blank(manifest: dict) -> None:
        manifest["environment"] = {}

    report = audit_run(make_run(blank))
    assert report.classification == VALID_WITH_LIMITATION
    assert "LIMIT_ENVIRONMENT_INCOMPLETE" in report.reason_codes


def test_poor_scientific_outcome_stays_valid(make_run: Callable[..., Path]) -> None:
    """A bad result is a finding, not a validity failure."""

    def unfavourable(result: dict) -> None:
        result["metrics"] = [
            {"generation": 0, "human_nll": 99.0, "tail_retention": 0.0},
            {"generation": 1, "human_nll": 480.0, "tail_retention": 0.0},
        ]

    report = audit_run(make_run(None, unfavourable))
    assert report.classification == VALID


def test_invalidating_code_outranks_limiting_code(make_run: Callable[..., Path]) -> None:
    def both(manifest: dict) -> None:
        manifest["environment"] = {}
        manifest["working_tree_clean"] = False

    report = audit_run(make_run(both))
    assert report.classification == INVALID


def test_classify_rejects_unknown_reason_code() -> None:
    with pytest.raises(ValueError, match="unknown reason code"):
        CheckResult(name="bogus", passed=False, code="NOT_A_REAL_CODE")


def test_failed_check_requires_a_code() -> None:
    with pytest.raises(ValueError, match="must carry a reason code"):
        CheckResult(name="bogus", passed=False)


def test_classify_of_all_passing_checks_is_valid() -> None:
    assert classify([CheckResult(name="a", passed=True)]) == VALID


def test_every_limiting_code_has_a_description() -> None:
    for code in LIMITING_CODES:
        assert describe(code)
