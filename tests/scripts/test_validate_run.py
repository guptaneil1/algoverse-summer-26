"""Contract tests for the three-state run validator.

Covers the `docs/weekly/WEEK_3.md` requirement that one command return
``valid``, ``invalid``, or ``valid_with_limitation`` for any run.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "validate_run", ROOT / "scripts" / "validate_run.py"
)
validate_run = importlib.util.module_from_spec(_SPEC)
# Register before exec: @dataclass resolves annotations via sys.modules[cls.__module__],
# which is None for an unregistered module and raises AttributeError on import.
sys.modules[_SPEC.name] = validate_run
_SPEC.loader.exec_module(validate_run)


def manifest(**overrides) -> dict:
    document = {
        "schema_version": "1.0",
        "run_id": "chain-001",
        "stage": "pilot",
        "git_commit": "a" * 40,
        "working_tree_clean": True,
        "model": {
            "identifier": "gpt2",
            "revision": "main",
            "tokenizer_revision": "main",
        },
        "data": {"train_manifest": "manifests/train.json", "train_manifest_sha256": "b" * 64},
        "policy": {
            "name": "joint",
            "config": "configs/policy/joint.json",
            "config_sha256": "c" * 64,
        },
        "budget": {"lifetime_human_optimizer_tokens": 60, "total_optimizer_tokens": 300},
        "randomness": {"chain_seed": 1},
        "environment": {"python": "3.10.0"},
        "horizon": 3,
        "status": "complete",
    }
    document.update(overrides)
    return document


def chain_result(**overrides) -> dict:
    document = {
        "schema_version": "1.0",
        "run_id": "chain-001",
        "policy": "joint",
        "chain_seed": 1,
        "budget_id": "toy-b1",
        "generations_completed": 3,
        "valid": True,
        "metrics": [
            {"generation": 0, "human_nll": 4.0, "tail_retention": 0.9},
            {"generation": 1, "human_nll": 4.2, "tail_retention": 0.85},
            {"generation": 2, "human_nll": 4.4, "tail_retention": 0.8},
        ],
        "consumed_human_tokens": 60,
        "consumed_total_tokens": 300,
        "exclusion_reason": None,
    }
    document.update(overrides)
    return document


def write_run(tmp_path: Path, manifest_doc: dict, result_doc: dict) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir(exist_ok=True)
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest_doc), encoding="utf-8")
    (run_dir / "chain_result.json").write_text(json.dumps(result_doc), encoding="utf-8")
    return run_dir


def test_clean_run_is_valid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(), chain_result())
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.VALID
    assert verdict.blocking == []
    assert verdict.limitations == []


def test_missing_artifact_is_invalid(tmp_path: Path) -> None:
    run_dir = tmp_path / "empty"
    run_dir.mkdir()
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_human_budget_violation_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(), chain_result(consumed_human_tokens=59))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID
    assert any("lifetime human-token budget violated" in reason for reason in verdict.blocking)


def test_total_budget_violation_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(), chain_result(consumed_total_tokens=301))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_human_tokens_exceeding_total_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(
        tmp_path,
        manifest(budget={"lifetime_human_optimizer_tokens": 400, "total_optimizer_tokens": 300}),
        chain_result(consumed_human_tokens=400, consumed_total_tokens=300),
    )
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID
    assert any("impossible accounting" in reason for reason in verdict.blocking)


def test_run_id_mismatch_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(), chain_result(run_id="chain-002"))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_seed_mismatch_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(), chain_result(chain_seed=99))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_self_reported_invalid_without_reason_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(), chain_result(valid=False, exclusion_reason=None))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_self_reported_invalid_with_reason_is_limited(tmp_path: Path) -> None:
    run_dir = write_run(
        tmp_path,
        manifest(),
        chain_result(valid=False, exclusion_reason="evaluator crash at generation 2"),
    )
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.VALID_WITH_LIMITATION


def test_incomplete_chain_is_limited(tmp_path: Path) -> None:
    run_dir = write_run(
        tmp_path,
        manifest(horizon=10),
        chain_result(),
    )
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.VALID_WITH_LIMITATION
    assert any("incomplete chain" in reason for reason in verdict.limitations)


def test_fixture_stage_is_limited(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(stage="fixture"), chain_result())
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.VALID_WITH_LIMITATION
    assert any("fixture" in reason for reason in verdict.limitations)


def test_dirty_working_tree_is_limited(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(working_tree_clean=False), chain_result())
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.VALID_WITH_LIMITATION


def test_incomplete_status_is_invalid(tmp_path: Path) -> None:
    run_dir = write_run(tmp_path, manifest(status="running"), chain_result())
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_non_contiguous_generations_are_invalid(tmp_path: Path) -> None:
    metrics = [
        {"generation": 0, "human_nll": 4.0, "tail_retention": 0.9},
        {"generation": 2, "human_nll": 4.2, "tail_retention": 0.85},
        {"generation": 3, "human_nll": 4.4, "tail_retention": 0.8},
    ]
    run_dir = write_run(tmp_path, manifest(), chain_result(metrics=metrics))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID
    assert any("contiguous" in reason for reason in verdict.blocking)


def test_blocking_failure_outranks_limitation(tmp_path: Path) -> None:
    """A run that is both fixture-staged and budget-violating must be invalid."""
    run_dir = write_run(
        tmp_path,
        manifest(stage="fixture"),
        chain_result(consumed_human_tokens=1),
    )
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


@pytest.mark.parametrize(
    ("state", "code"),
    [
        (validate_run.VALID, 0),
        (validate_run.VALID_WITH_LIMITATION, 2),
        (validate_run.INVALID, 1),
    ],
)
def test_exit_codes_are_distinct(state: str, code: int) -> None:
    assert validate_run._EXIT_CODES[state] == code


# ---------------------------------------------------------------------------
# Regression tests for defects found by adversarial review on 2026-08-15.
# Each pins a hole through which a bad run previously passed as valid.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", ["null", "[]", '"a string"', "42"])
def test_non_object_json_is_invalid(tmp_path: Path, payload: str) -> None:
    """`json.loads("null")` returns None without raising.

    That collided with the load-failure sentinel, so the caller early-returned a
    default verdict whose state was VALID — a null artifact scored a clean pass
    with exit 0.
    """
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "run_manifest.json").write_text(payload, encoding="utf-8")
    (run_dir / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID
    assert verdict.blocking


def test_non_utf8_artifact_is_classified_not_crashed(tmp_path: Path) -> None:
    """`read_text` raises UnicodeDecodeError, which is not a JSONDecodeError."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "run_manifest.json").write_bytes(b"\xff\xfe\x00garbage")
    (run_dir / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_unreadable_artifact_does_not_abort_a_batch(tmp_path: Path) -> None:
    """One bad directory must not discard the verdicts for every other one."""
    good = tmp_path / "good"
    good.mkdir()
    (good / "run_manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")
    (good / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "run_manifest.json").mkdir()  # a directory where a file is expected
    (bad / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    verdicts = [validate_run.validate_run(good), validate_run.validate_run(bad)]
    assert verdicts[0].state == validate_run.VALID
    assert verdicts[1].state == validate_run.INVALID


def test_absent_working_tree_flag_is_treated_as_unknown(tmp_path: Path) -> None:
    """The schema does not require the key, so absence must fail closed."""
    document = manifest()
    del document["working_tree_clean"]
    run_dir = write_run(tmp_path, document, chain_result())

    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.VALID_WITH_LIMITATION
    assert any("unrecorded" in reason for reason in verdict.limitations)


def test_over_running_the_horizon_is_invalid(tmp_path: Path) -> None:
    """Only the under-run direction was previously checked."""
    metrics = [
        {"generation": index, "human_nll": 4.0, "tail_retention": 0.9} for index in range(5)
    ]
    run_dir = write_run(
        tmp_path,
        manifest(horizon=3),
        chain_result(generations_completed=5, metrics=metrics),
    )
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID
    assert any("exceeded its declared horizon" in reason for reason in verdict.blocking)


def test_valid_true_with_exclusion_reason_is_invalid(tmp_path: Path) -> None:
    """An excluded chain claiming validity contradicts itself."""
    run_dir = write_run(
        tmp_path, manifest(), chain_result(valid=True, exclusion_reason="dropped at g2")
    )
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_metric_count_mismatch_is_blocking(tmp_path: Path) -> None:
    """A self-contradicting artifact is refused, not merely annotated."""
    run_dir = write_run(tmp_path, manifest(), chain_result(generations_completed=7))
    verdict = validate_run.validate_run(run_dir)
    assert verdict.state == validate_run.INVALID


def test_usage_error_does_not_masquerade_as_a_limitation() -> None:
    """argparse exits 2, which is the valid_with_limitation code.

    A CI wrapper treating 2 as "limitation acknowledged" would otherwise proceed
    on a validator that never ran.
    """
    assert validate_run.main([]) == validate_run.EXIT_USAGE
    assert validate_run.EXIT_USAGE not in validate_run._EXIT_CODES.values()


def test_main_returns_two_for_a_genuine_limitation(tmp_path: Path) -> None:
    """Exercise main() end to end for the middle state, not just the dict."""
    run_dir = write_run(tmp_path, manifest(stage="fixture"), chain_result())
    assert validate_run.main([str(run_dir)]) == 2


def test_batch_worst_state_includes_the_limitation_case(tmp_path: Path) -> None:
    """valid + valid_with_limitation must report 2, not 0."""
    good = tmp_path / "good"
    good.mkdir()
    (good / "run_manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")
    (good / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    limited = tmp_path / "limited"
    limited.mkdir()
    (limited / "run_manifest.json").write_text(
        json.dumps(manifest(stage="fixture")), encoding="utf-8"
    )
    (limited / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    assert validate_run.main([str(good), str(limited)]) == 2


def test_batch_returns_worst_state(tmp_path: Path, capsys) -> None:
    good = tmp_path / "good"
    good.mkdir()
    (good / "run_manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")
    (good / "chain_result.json").write_text(json.dumps(chain_result()), encoding="utf-8")

    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "run_manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")
    (bad / "chain_result.json").write_text(
        json.dumps(chain_result(consumed_human_tokens=1)), encoding="utf-8"
    )

    assert validate_run.main([str(good), str(bad)]) == 1
    assert validate_run.main([str(good)]) == 0
