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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from human_data_budget.data.overlap import find_near_duplicate_pairs
from human_data_budget.data.token_accounting import consumed_tokens
from human_data_budget.validation.classification import (
    LIMITING_CODES,
    AuditReport,
    CheckResult,
    classify,
)

MANIFEST_NAME = "run_manifest.json"
CHAIN_RESULT_NAME = "chain_result.json"
BATCH_RECORDS_NAME = "batch_records.jsonl"
TERMINAL_STATUSES = {"complete", "failed", "invalid"}

# The threshold value 0.8 is taken from ``human_data_budget.data.overlap``'s own
# default; no new value was chosen here.
#
# UNRESOLVED, needs the data owner (@Neil) before any primary chain is certified:
# the repository contains two different operating points that share the number
# 0.8 but not the metric. ``docs/data/overlap_report.md`` §3 records the
# corpus-scale scan as **word-8-gram** Jaccard with a ±20% length band
# (``scripts/build_wikitext103_manifests.py``: NEAR_DUP_SHINGLE_WORDS = 8), while
# ``data/overlap.py`` — the fixture-scale logic this auditor reuses — is
# **character-5-gram**. They disagree sharply: the reworded leak pinned in
# ``tests/validation/test_near_duplicate_separation.py`` scores 0.9483 as
# char-5-gram and 0.0 as word-8-gram. Whichever is the intended audit-time
# definition, both should not ship.
#
# Reach of the char-5-gram detector at 0.8, measured by the tests in that file:
# it catches near-identical restatements and misses semantic paraphrase. It also
# misses a *verbatim* copy that has been padded with surrounding text, because
# Jaccard is symmetric and measures no containment.
NEAR_DUPLICATE_THRESHOLD = 0.8

FORBIDDEN_PARTITION_PAIRS = (
    ("base_human_train", "final_human_test"),
    ("rescue_candidates", "final_human_test"),
    ("generation_prompts", "final_human_test"),
    ("validation", "final_human_test"),
    ("base_human_train", "rescue_candidates"),
)

REQUIRED_PROVENANCE_FIELDS = ("stable_id", "content_hash", "source_dataset", "origin")

# The five partitions PROTOCOL.md §3 requires to be disjoint. All five must be
# present and non-empty: a truthy-but-meaningless block (an unrecognised key, or
# the right keys mapped to empty lists) previously satisfied the provenance guard
# and certified the run with zero reason codes.
#
# OPEN QUESTION for the validator owner, recorded rather than decided here: does
# any legitimate arm ship an *empty* partition? The `no_rescue` reference arm
# spends nothing (`configs/experiment/primary_no_rescue.json` sets
# `per_generation_human_budget: 0`), which would make an empty `rescue_candidates`
# plausible — and this rule would then classify every no-rescue chain `invalid`.
# Two things say otherwise today: that config's own `_required_from_freeze` lists
# "the five partition manifests", and `rescue_candidates` is the candidate *pool*,
# not the selected set, so a chain that never draws from it still has one. The
# question is also not live yet: `runner.chain.policy_from_config` cannot build a
# `no_rescue` policy at all (`unknown policy: no_rescue`), so no such run exists
# to misclassify. Erring strict is deliberate — a false `invalid` is visible and
# fixable, a false `valid` is not — but confirm before the first reference run.
REQUIRED_PARTITIONS = (
    "base_human_train",
    "rescue_candidates",
    "generation_prompts",
    "validation",
    "final_human_test",
)


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


@dataclass(frozen=True)
class _TextExample:
    """The two attributes ``find_near_duplicate_pairs`` reads from an example.

    A full ``human_data_budget.data.manifest.Example`` is deliberately not built
    here: it requires ``mode``, ``source_offset``, and ``token_count``, none of
    which the manifest provenance record carries. Supplying placeholder values
    for them would put invented numbers into the audit path, so the auditor
    adapts the record it actually has and reuses the frozen detection logic
    unchanged.
    """

    example_id: str
    text: str


@dataclass(frozen=True)
class _TextPartition:
    examples: tuple[_TextExample, ...]


def _text_partition(entries: list[dict[str, Any]]) -> tuple[_TextPartition, list[str]]:
    """Adapt a partition's provenance entries for near-duplicate comparison.

    Returns the readable examples **and** the stable IDs that carried no text.

    Comparison proceeds over whatever text is present rather than being skipped
    wholesale. An earlier all-or-nothing rule made the missing-text path a
    cheaper bypass than the leak it guarded: blanking ``text`` on a single
    innocuous decoy example disabled near-duplicate checking for every pair
    touching that partition, so a genuine reworded leak elsewhere in the same
    partition downgraded from ``invalid`` to ``valid_with_limitation``. Skipped
    IDs are now reported by name, so a blinded entry is visible in the report
    instead of silently suppressing the check.
    """

    examples: list[_TextExample] = []
    skipped: list[str] = []
    for entry in entries:
        stable_id = str(entry.get("stable_id", ""))
        text = entry.get("text")
        if not isinstance(text, str) or not text.strip():
            skipped.append(stable_id)
            continue
        examples.append(_TextExample(example_id=stable_id, text=text))
    return _TextPartition(examples=tuple(examples)), skipped


def check_near_duplicate_separation(
    partitions: dict[str, list[dict[str, Any]]],
    *,
    threshold: float = NEAR_DUPLICATE_THRESHOLD,
) -> list[CheckResult]:
    """Reject near-duplicate text across forbidden partition pairs.

    Closes blind spot 2 of ``docs/validity/week3_adversarial_audit.md`` §8: the
    auditor previously compared exact content hashes only, so a leak that had
    been reworded even trivially passed as valid. Detection is delegated to
    ``human_data_budget.data.overlap.find_near_duplicate_pairs``.

    A pair whose text is unavailable produces an explicit
    ``LIMIT_NEAR_DUPLICATE_NOT_CHECKED`` limitation rather than an unqualified
    pass, so "not checked" is never recorded as "checked and clean".
    """

    checks: list[CheckResult] = []
    adapted = {name: _text_partition(entries) for name, entries in partitions.items()}
    blinded = sorted(
        f"{name}:{stable_id}" for name, (_, skipped) in adapted.items() for stable_id in skipped
    )
    unchecked: list[str] = []

    for left, right in FORBIDDEN_PARTITION_PAIRS:
        if left not in partitions or right not in partitions:
            # Absent, not clean. Silently skipping reported "not checked" as
            # "checked and clean" — the failure mode this function exists to
            # avoid — for a manifest that simply omitted a partition.
            unchecked.append(f"{left}|{right}")
            continue
        left_partition, _ = adapted[left]
        right_partition, _ = adapted[right]
        if not left_partition.examples or not right_partition.examples:
            unchecked.append(f"{left}|{right}")
            continue

        pairs = find_near_duplicate_pairs(left_partition, right_partition, threshold)
        checks.append(
            CheckResult(
                name=f"separation_near_duplicate:{left}|{right}",
                passed=not pairs,
                code=None if not pairs else "SEPARATION_NEAR_DUPLICATE",
                detail=(
                    ""
                    if not pairs
                    else (
                        f"{len(pairs)} near-duplicate pair(s) at threshold "
                        f"{threshold}: {sorted(pairs)[:5]}"
                    )
                ),
            )
        )

    if unchecked:
        checks.append(
            CheckResult(
                name="separation_near_duplicate_scanned",
                passed=False,
                code="LIMIT_NEAR_DUPLICATE_NOT_CHECKED",
                detail=f"no example text at all for partition pair(s) {sorted(unchecked)}",
            )
        )
    if blinded:
        checks.append(
            CheckResult(
                name="separation_near_duplicate_coverage",
                passed=False,
                code="LIMIT_NEAR_DUPLICATE_NOT_CHECKED",
                detail=(
                    f"{len(blinded)} example(s) carried no text and were not "
                    f"compared: {blinded[:10]}"
                ),
            )
        )
    return checks


def check_separation(manifest: dict[str, Any]) -> list[CheckResult]:
    """Reject overlap between forbidden partition pairs and missing provenance."""
    checks: list[CheckResult] = []
    partitions = manifest.get("data", {}).get("partitions")

    if not isinstance(partitions, dict) or not partitions:
        return [
            CheckResult(
                name="separation_partitions_recorded",
                passed=False,
                code="SEPARATION_MISSING_PROVENANCE",
                detail="manifest records no data.partitions block",
            )
        ]

    # A truthy block is not evidence of provenance. Require the five named
    # partitions to be present and populated, and reject unrecognised names,
    # otherwise `{"junk": []}` certifies a run with no provenance at all.
    absent = [name for name in REQUIRED_PARTITIONS if not partitions.get(name)]
    if absent:
        checks.append(
            CheckResult(
                name="separation_partitions_recorded",
                passed=False,
                code="SEPARATION_MISSING_PROVENANCE",
                detail=f"partition(s) absent or empty: {sorted(absent)}",
            )
        )

    unexpected = sorted(set(partitions) - set(REQUIRED_PARTITIONS))
    if unexpected:
        checks.append(
            CheckResult(
                name="separation_partitions_recognised",
                passed=False,
                code="SEPARATION_MISSING_PROVENANCE",
                detail=f"unrecognised partition name(s): {unexpected}",
            )
        )

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

    checks.extend(check_near_duplicate_separation(partitions))

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


def _load_batch_records(path: Path) -> list[dict[str, Any]]:
    """Read realized batch records from JSONL, one record per line."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"line {lineno} is not a JSON object")
            records.append(record)
    return records


def check_token_ledger(
    run_directory: Path, manifest: dict[str, Any], chain_result: dict[str, Any]
) -> list[CheckResult]:
    """Recompute the token ledger from realized batches instead of trusting it.

    Closes blind spot 3 of ``docs/validity/week3_adversarial_audit.md`` §8. The
    auditor previously compared the declared consumed totals against the frozen
    budget, so a ledger that was wrong but internally consistent — the same wrong
    number in the manifest and the chain result — passed every check.

    Recomputation delegates to
    ``human_data_budget.data.token_accounting.consumed_tokens``, which already
    enforces the accounting rules tested in
    ``tests/data/test_token_accounting.py``: padding excluded via the attention
    mask, each presentation of a repeated example counted again, every
    gradient-accumulation micro-batch counted, and a resumed run counted exactly
    once per realized batch.

    When no batch records exist the auditor says so with
    ``LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE``. It never falls back silently to
    comparison, because "the ledger agrees with itself" is precisely the
    evidence this check exists to distinguish from "the ledger is correct".
    """

    declared_paths = sorted(
        {
            str(reference.get("path", ""))
            for reference in manifest.get("artifacts", [])
            if str(reference.get("path", "")).endswith(BATCH_RECORDS_NAME)
        }
    )
    default_present = (run_directory / BATCH_RECORDS_NAME).is_file()

    # The manifest is the artifact under audit, so it does not get to choose which
    # evidence the auditor is allowed to see. Previously the first declared path
    # won outright: a run could keep truthful records at the default location and
    # declare a hash-correct decoy elsewhere, and the decoy alone was read.
    ambiguous = list(declared_paths)
    if default_present and BATCH_RECORDS_NAME not in declared_paths:
        ambiguous.append(BATCH_RECORDS_NAME)
    if len(ambiguous) > 1:
        return [
            CheckResult(
                name="token_ledger_recomputed",
                passed=False,
                code="ARTIFACT_SCHEMA_INVALID",
                detail=(
                    "run carries more than one batch-record ledger "
                    f"({sorted(ambiguous)}); which one realized the run is ambiguous"
                ),
            )
        ]

    relative = Path(declared_paths[0]) if declared_paths else Path(BATCH_RECORDS_NAME)

    # The evidence must live inside the run being audited. `run_directory / p`
    # collapses to `p` when p is absolute, so a manifest could name any file on
    # the machine — including one written specifically to match a false ledger —
    # and the auditor would recompute from it and certify. `..` escapes the same
    # way. Neither is a path within the run, so neither is admissible evidence.
    if relative.is_absolute() or ".." in relative.parts:
        return [
            CheckResult(
                name="token_ledger_recomputed",
                passed=False,
                code="ARTIFACT_SCHEMA_INVALID",
                detail=(
                    f"batch-record path {str(relative)!r} points outside the run "
                    "directory; ledger evidence must be contained by the run"
                ),
            )
        ]
    candidate = run_directory / relative

    if not candidate.is_file():
        # A run that never emitted batch records and a run whose records were
        # removed after the fact both land here, but they are not the same claim:
        # the second declared the artifact and then failed to produce it, which
        # is the shape of evidence deleted to escape BUDGET_LEDGER_MISMATCH.
        # Recording the declaration state lets a reader tell them apart.
        if declared_paths:
            return [
                CheckResult(
                    name="token_ledger_recomputed",
                    passed=False,
                    code="ARTIFACT_MISSING",
                    detail=(
                        f"manifest declares batch records at {str(relative)!r} but the "
                        "file is absent; a declared ledger artifact must be present"
                    ),
                )
            ]
        return [
            CheckResult(
                name="token_ledger_recomputed",
                passed=False,
                code="LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE",
                detail=(
                    f"no realized batch records at {candidate.name} and none declared "
                    "in the manifest; the declared ledger was compared against the "
                    "frozen budget but not recomputed"
                ),
            )
        ]

    try:
        records = _load_batch_records(candidate)
    except (OSError, ValueError) as error:
        return [
            CheckResult(
                name="token_ledger_recomputed",
                passed=False,
                code="ARTIFACT_SCHEMA_INVALID",
                detail=f"{candidate.name} could not be read as batch records: {error}",
            )
        ]

    if not records:
        return [
            CheckResult(
                name="token_ledger_recomputed",
                passed=False,
                code="LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE",
                detail=f"{candidate.name} contains no batch records",
            )
        ]

    try:
        recomputed_total = consumed_tokens(records)
        recomputed_human = consumed_tokens(records, origin="human")
    except (KeyError, TypeError, ValueError) as error:
        return [
            CheckResult(
                name="token_ledger_recomputed",
                passed=False,
                code="ARTIFACT_SCHEMA_INVALID",
                detail=f"{candidate.name} holds malformed batch records: {error}",
            )
        ]

    checks: list[CheckResult] = []
    for label, recomputed, declared in (
        ("human", recomputed_human, chain_result.get("consumed_human_tokens")),
        ("total", recomputed_total, chain_result.get("consumed_total_tokens")),
    ):
        # `declared == recomputed` alone would accept True for 1: bool subclasses
        # int, so a chain result carrying `"consumed_human_tokens": true` would
        # certify against a recomputed value of one.
        agrees = type(declared) is int and declared == recomputed
        checks.append(
            CheckResult(
                name=f"token_ledger_recomputed:{label}",
                passed=agrees,
                code=None if agrees else "BUDGET_LEDGER_MISMATCH",
                detail=(
                    ""
                    if agrees
                    else (
                        f"chain result declares {declared} {label} tokens; "
                        f"{len(records)} realized batch records total {recomputed}"
                    )
                ),
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
    checks.extend(check_token_ledger(run_directory, manifest, chain_result))

    # The batch records decide the ledger verdict, so the report records their
    # hash alongside the manifest's and the chain result's. Without it the
    # verdict is not reproducible against the evidence that produced it.
    input_hashes = {
        "run_manifest": sha256_file(manifest_path),
        "chain_result": sha256_file(result_path),
    }
    batch_path = run_directory / BATCH_RECORDS_NAME
    if batch_path.is_file():
        input_hashes["batch_records"] = sha256_file(batch_path)
    checks.extend(check_protocol(manifest, chain_result))
    checks.extend(check_evaluation(chain_result))

    return _build_report(
        run_id=str(chain_result.get("run_id") or manifest.get("run_id") or run_directory.name),
        checks=checks,
        input_hashes=input_hashes,
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
