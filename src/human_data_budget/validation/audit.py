"""Independent validity audit of a completed run directory.

The auditor only reads. It never repairs a run, rewrites a manifest, replaces a
hash, or recomputes a missing scientific choice. Every check is objective and
result-independent: poor NLL or weak tail retention is a scientific outcome, not
a validity failure.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from human_data_budget.validation.classification import (
    LIMITING_CODES,
    AuditReport,
    CheckResult,
    classify,
)

MANIFEST_NAME = "run_manifest.json"
CHAIN_RESULT_NAME = "chain_result.json"
TERMINAL_STATUSES = {"complete", "failed", "invalid"}

FORBIDDEN_PARTITION_PAIRS = (
    ("base_human_train", "final_human_test"),
    ("rescue_candidates", "final_human_test"),
    ("generation_prompts", "final_human_test"),
    ("validation", "final_human_test"),
    ("base_human_train", "rescue_candidates"),
)

REQUIRED_PROVENANCE_FIELDS = ("stable_id", "content_hash", "source_dataset", "origin")


def sha256_file(path: Path) -> str:
    """Hash a file's bytes with SHA-256."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_artifacts(run_directory: Path, manifest: dict[str, Any]) -> list[CheckResult]:
    """Confirm every referenced artifact exists and matches its recorded hash."""
    checks: list[CheckResult] = []

    for name in (MANIFEST_NAME, CHAIN_RESULT_NAME):
        target = run_directory / name
        checks.append(
            CheckResult(
                name=f"artifact_present:{name}",
                passed=target.is_file(),
                code=None if target.is_file() else "ARTIFACT_MISSING",
                detail="" if target.is_file() else f"{name} is absent",
            )
        )

    for reference in manifest.get("artifacts", []):
        relative = reference.get("path", "")
        recorded = reference.get("sha256")
        target = run_directory / relative
        if not target.is_file():
            checks.append(
                CheckResult(
                    name=f"artifact_present:{relative}",
                    passed=False,
                    code="ARTIFACT_MISSING",
                    detail=f"{relative} is referenced but absent",
                )
            )
            continue
        if not recorded:
            checks.append(
                CheckResult(
                    name=f"artifact_hash:{relative}",
                    passed=False,
                    code="LIMIT_MISSING_OPTIONAL_ARTIFACT",
                    detail=f"{relative} has no recorded hash",
                )
            )
            continue
        observed = sha256_file(target)
        checks.append(
            CheckResult(
                name=f"artifact_hash:{relative}",
                passed=observed == recorded,
                code=None if observed == recorded else "ARTIFACT_HASH_MISMATCH",
                detail="" if observed == recorded else f"recorded {recorded}, observed {observed}",
            )
        )

    clean = manifest.get("working_tree_clean")
    checks.append(
        CheckResult(
            name="commit_clean",
            passed=clean is True,
            code=None if clean is True else "COMMIT_DIRTY",
            detail="" if clean is True else f"working_tree_clean={clean!r}",
        )
    )
    return checks


def check_separation(manifest: dict[str, Any]) -> list[CheckResult]:
    """Reject overlap between forbidden partition pairs and missing provenance."""
    checks: list[CheckResult] = []
    partitions = manifest.get("data", {}).get("partitions")

    if not partitions:
        return [
            CheckResult(
                name="separation_partitions_recorded",
                passed=False,
                code="SEPARATION_MISSING_PROVENANCE",
                detail="manifest records no data.partitions block",
            )
        ]

    for left, right in FORBIDDEN_PARTITION_PAIRS:
        left_ids = {item.get("content_hash") for item in partitions.get(left, [])}
        right_ids = {item.get("content_hash") for item in partitions.get(right, [])}
        shared = {value for value in left_ids & right_ids if value is not None}
        checks.append(
            CheckResult(
                name=f"separation_disjoint:{left}|{right}",
                passed=not shared,
                code=None if not shared else "SEPARATION_OVERLAP",
                detail="" if not shared else f"{len(shared)} shared content hashes",
            )
        )

    for partition_name, examples in partitions.items():
        for index, example in enumerate(examples):
            missing = [f for f in REQUIRED_PROVENANCE_FIELDS if not example.get(f)]
            if missing:
                code = (
                    "SEPARATION_MISSING_ID"
                    if "stable_id" in missing
                    else "SEPARATION_MISSING_PROVENANCE"
                )
                checks.append(
                    CheckResult(
                        name=f"provenance_complete:{partition_name}[{index}]",
                        passed=False,
                        code=code,
                        detail=f"missing {sorted(missing)}",
                    )
                )

    checks.append(
        CheckResult(name="provenance_scanned", passed=True, detail=f"{len(partitions)} partitions")
    )
    return checks


def check_budgets(manifest: dict[str, Any], chain_result: dict[str, Any]) -> list[CheckResult]:
    """Compare consumed tokens against the frozen budget declared in the manifest."""
    budget = manifest.get("budget", {})
    planned_human = budget.get("lifetime_human_optimizer_tokens")
    planned_total = budget.get("total_optimizer_tokens")
    consumed_human = chain_result.get("consumed_human_tokens")
    consumed_total = chain_result.get("consumed_total_tokens")

    checks: list[CheckResult] = []

    negative = [
        value for value in (consumed_human, consumed_total) if isinstance(value, int) and value < 0
    ]
    checks.append(
        CheckResult(
            name="budget_non_negative",
            passed=not negative,
            code=None if not negative else "BUDGET_NEGATIVE",
            detail="" if not negative else f"negative token counts {negative}",
        )
    )

    human_ok = planned_human == consumed_human
    checks.append(
        CheckResult(
            name="budget_human_matches_plan",
            passed=human_ok,
            code=None if human_ok else "BUDGET_HUMAN_MISMATCH",
            detail="" if human_ok else f"planned {planned_human}, consumed {consumed_human}",
        )
    )

    total_ok = planned_total == consumed_total
    checks.append(
        CheckResult(
            name="budget_total_matches_plan",
            passed=total_ok,
            code=None if total_ok else "BUDGET_TOTAL_MISMATCH",
            detail="" if total_ok else f"planned {planned_total}, consumed {consumed_total}",
        )
    )
    return checks


def check_protocol(manifest: dict[str, Any], chain_result: dict[str, Any]) -> list[CheckResult]:
    """Confirm seed, horizon, policy, and status agree with the frozen plan."""
    checks: list[CheckResult] = []

    manifest_seed = manifest.get("randomness", {}).get("chain_seed")
    result_seed = chain_result.get("chain_seed")
    seed_ok = manifest_seed == result_seed
    checks.append(
        CheckResult(
            name="protocol_seed_matches",
            passed=seed_ok,
            code=None if seed_ok else "PROTOCOL_SEED_MISMATCH",
            detail="" if seed_ok else f"manifest {manifest_seed}, result {result_seed}",
        )
    )

    horizon = manifest.get("horizon")
    completed = chain_result.get("generations_completed")
    if isinstance(horizon, int) and isinstance(completed, int):
        if completed > horizon:
            checks.append(
                CheckResult(
                    name="protocol_horizon_respected",
                    passed=False,
                    code="PROTOCOL_HORIZON_MISMATCH",
                    detail=f"completed {completed} exceeds horizon {horizon}",
                )
            )
        elif completed < horizon:
            checks.append(
                CheckResult(
                    name="protocol_horizon_respected",
                    passed=False,
                    code="LIMIT_REDUCED_GENERATIONS",
                    detail=f"completed {completed} of {horizon} generations",
                )
            )
        else:
            checks.append(CheckResult(name="protocol_horizon_respected", passed=True))

    manifest_policy = manifest.get("policy", {}).get("name")
    result_policy = chain_result.get("policy")
    policy_ok = manifest_policy == result_policy
    checks.append(
        CheckResult(
            name="protocol_policy_matches",
            passed=policy_ok,
            code=None if policy_ok else "PROTOCOL_POLICY_MISMATCH",
            detail="" if policy_ok else f"manifest {manifest_policy}, result {result_policy}",
        )
    )

    status = manifest.get("status")
    status_ok = status in TERMINAL_STATUSES
    checks.append(
        CheckResult(
            name="protocol_status_terminal",
            passed=status_ok,
            code=None if status_ok else "PROTOCOL_STATUS_NOT_TERMINAL",
            detail="" if status_ok else f"status={status!r}",
        )
    )

    environment = manifest.get("environment", {})
    environment_ok = bool(environment)
    checks.append(
        CheckResult(
            name="environment_recorded",
            passed=environment_ok,
            code=None if environment_ok else "LIMIT_ENVIRONMENT_INCOMPLETE",
            detail="" if environment_ok else "environment block is empty",
        )
    )
    return checks


def check_evaluation(chain_result: dict[str, Any]) -> list[CheckResult]:
    """Check evaluator output is usable. Metric magnitude is never judged."""
    metrics = chain_result.get("metrics") or []
    if not metrics:
        return [
            CheckResult(
                name="evaluation_metrics_present",
                passed=False,
                code="EVALUATION_NO_METRICS",
                detail="chain result records no generation metrics",
            )
        ]

    checks: list[CheckResult] = [CheckResult(name="evaluation_metrics_present", passed=True)]

    bad_nll = [
        entry["generation"]
        for entry in metrics
        if not isinstance(entry.get("human_nll"), (int, float))
        or not math.isfinite(float(entry["human_nll"]))
    ]
    checks.append(
        CheckResult(
            name="evaluation_nll_finite",
            passed=not bad_nll,
            code=None if not bad_nll else "EVALUATION_NLL_NOT_FINITE",
            detail="" if not bad_nll else f"non-finite NLL at generations {bad_nll}",
        )
    )

    bad_tail = [
        entry["generation"]
        for entry in metrics
        if not isinstance(entry.get("tail_retention"), (int, float))
        or not 0.0 <= float(entry["tail_retention"]) <= 1.0
    ]
    checks.append(
        CheckResult(
            name="evaluation_tail_in_range",
            passed=not bad_tail,
            code=None if not bad_tail else "EVALUATION_TAIL_OUT_OF_RANGE",
            detail="" if not bad_tail else f"out-of-range tail retention at {bad_tail}",
        )
    )
    return checks


def audit_run(
    run_directory: Path,
    *,
    validator_commit: str = "unknown",
    audited_at: str = "",
) -> AuditReport:
    """Audit one run directory and return exactly one classification.

    ``audited_at`` is supplied by the caller rather than read from the clock so
    the same inputs always produce the same report.
    """
    run_directory = Path(run_directory)
    manifest_path = run_directory / MANIFEST_NAME
    result_path = run_directory / CHAIN_RESULT_NAME

    if not manifest_path.is_file() or not result_path.is_file():
        missing = [
            name
            for name, path in ((MANIFEST_NAME, manifest_path), (CHAIN_RESULT_NAME, result_path))
            if not path.is_file()
        ]
        failure = CheckResult(
            name="artifact_present:core",
            passed=False,
            code="ARTIFACT_MISSING",
            detail=f"missing {missing}",
        )
        return _build_report(
            run_id=run_directory.name,
            checks=[failure],
            input_hashes={},
            validator_commit=validator_commit,
            audited_at=audited_at,
        )

    try:
        manifest = _load_json(manifest_path)
        chain_result = _load_json(result_path)
    except json.JSONDecodeError as error:
        failure = CheckResult(
            name="artifact_schema:core",
            passed=False,
            code="ARTIFACT_SCHEMA_INVALID",
            detail=str(error),
        )
        return _build_report(
            run_id=run_directory.name,
            checks=[failure],
            input_hashes={},
            validator_commit=validator_commit,
            audited_at=audited_at,
        )

    checks: list[CheckResult] = []
    checks.extend(check_artifacts(run_directory, manifest))
    checks.extend(check_separation(manifest))
    checks.extend(check_budgets(manifest, chain_result))
    checks.extend(check_protocol(manifest, chain_result))
    checks.extend(check_evaluation(chain_result))

    return _build_report(
        run_id=str(chain_result.get("run_id") or manifest.get("run_id") or run_directory.name),
        checks=checks,
        input_hashes={
            "run_manifest": sha256_file(manifest_path),
            "chain_result": sha256_file(result_path),
        },
        validator_commit=validator_commit,
        audited_at=audited_at,
    )


def _build_report(
    *,
    run_id: str,
    checks: Iterable[CheckResult],
    input_hashes: dict[str, str],
    validator_commit: str,
    audited_at: str,
) -> AuditReport:
    checks = list(checks)
    failed = [check for check in checks if not check.passed]

    return AuditReport(
        run_id=run_id,
        classification=classify(checks),
        reason_codes=sorted({check.code for check in failed if check.code is not None}),
        checks_passed=sorted(check.name for check in checks if check.passed),
        checks_failed=sorted(check.name for check in failed),
        limitations=sorted(
            f"{check.code}: {check.detail}" for check in failed if check.code in LIMITING_CODES
        ),
        input_hashes=input_hashes,
        validator_commit=validator_commit,
        audited_at=audited_at,
    )
