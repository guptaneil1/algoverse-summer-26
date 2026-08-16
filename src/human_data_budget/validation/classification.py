"""Deterministic validity classification and frozen reason codes.

The classification rule is intentionally mechanical: a check either passes or it
does not, and the mapping from failed checks to a classification is fixed before
any run is audited. No threshold here may depend on an observed result.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

VALID = "valid"
VALID_WITH_LIMITATION = "valid_with_limitation"
INVALID = "invalid"

CLASSIFICATIONS = (VALID, VALID_WITH_LIMITATION, INVALID)

# Reason codes are frozen before batch audit. A code is either invalidating or
# limiting; nothing decides which at audit time.
INVALIDATING_CODES = {
    "SEPARATION_OVERLAP": "A forbidden partition pair shares at least one example.",
    "SEPARATION_NEAR_DUPLICATE": (
        "A forbidden partition pair shares near-duplicate text above the frozen "
        "similarity threshold."
    ),
    "SEPARATION_PROVENANCE_INCONSISTENT": (
        "An example's recorded content hash does not match its recorded text, so "
        "the text compared for overlap is not the text the hash identifies."
    ),
    "SEPARATION_MISSING_ID": "A training example lacks a stable identifier.",
    "SEPARATION_MISSING_PROVENANCE": "A provenance field required by protocol is absent.",
    "BUDGET_LEDGER_MISMATCH": (
        "Token totals recomputed from realized batch records disagree with the "
        "declared ledger."
    ),
    "BUDGET_HUMAN_MISMATCH": "Consumed lifetime human-origin tokens differ from the frozen budget.",
    "BUDGET_TOTAL_MISMATCH": "Consumed total optimizer tokens differ from the frozen budget.",
    "BUDGET_NEGATIVE": "A recorded token count is negative.",
    "ARTIFACT_MISSING": "A required artifact referenced by the manifest is absent.",
    "ARTIFACT_HASH_MISMATCH": "A recorded artifact hash does not match the file content.",
    "ARTIFACT_SCHEMA_INVALID": "An artifact failed its frozen JSON schema.",
    "COMMIT_DIRTY": "The run was produced from a dirty or unknown working tree.",
    "PROTOCOL_SEED_MISMATCH": "The chain seed does not match the manifest seed.",
    "PROTOCOL_HORIZON_MISMATCH": "Generations completed exceed the frozen horizon.",
    "PROTOCOL_POLICY_MISMATCH": "The chain result policy differs from the manifest policy.",
    "PROTOCOL_STATUS_NOT_TERMINAL": "The run status is not a terminal state.",
    "EVALUATION_TAIL_OUT_OF_RANGE": "A tail-retention value falls outside [0, 1].",
    "EVALUATION_NLL_NOT_FINITE": "A held-out NLL value is not finite.",
    "EVALUATION_NO_METRICS": "The chain result records no generation metrics.",
}

LIMITING_CODES = {
    "LIMIT_NONDETERMINISM_DOCUMENTED": "Documented nondeterminism prevents byte-identical replay.",
    "LIMIT_REDUCED_GENERATIONS": "The chain completed fewer generations than the frozen horizon.",
    "LIMIT_MISSING_OPTIONAL_ARTIFACT": "An optional artifact reference is absent.",
    "LIMIT_ENVIRONMENT_INCOMPLETE": "The environment record is missing non-critical fields.",
    "LIMIT_NEAR_DUPLICATE_NOT_CHECKED": (
        "Partition entries carry no text, so near-duplicate overlap could not be "
        "checked. Exact-hash separation was still verified."
    ),
    "LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE": (
        "No realized batch records were available, so the declared token ledger "
        "could not be recomputed and was only compared against the frozen budget."
    ),
}

ALL_CODES = {**INVALIDATING_CODES, **LIMITING_CODES}


@dataclass(frozen=True)
class CheckResult:
    """One objective check outcome."""

    name: str
    passed: bool
    code: str | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.passed and self.code is None:
            raise ValueError(f"failed check {self.name} must carry a reason code")
        if self.code is not None and self.code not in ALL_CODES:
            raise ValueError(f"unknown reason code: {self.code}")


@dataclass
class AuditReport:
    """Machine-readable audit output."""

    run_id: str
    classification: str
    reason_codes: list[str] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    input_hashes: dict[str, str] = field(default_factory=dict)
    validator_commit: str = "unknown"
    audited_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "classification": self.classification,
            "reason_codes": self.reason_codes,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "limitations": self.limitations,
            "input_hashes": self.input_hashes,
            "validator_commit": self.validator_commit,
            "audited_at": self.audited_at,
        }


def classify(checks: Iterable[CheckResult]) -> str:
    """Map check results to exactly one frozen classification.

    Any invalidating code produces ``invalid``. Otherwise any limiting code
    produces ``valid_with_limitation``. Otherwise ``valid``. The rule never
    inspects a metric value, so an unfavourable result cannot become invalid.
    """
    failed = [check for check in checks if not check.passed]
    codes = {check.code for check in failed if check.code is not None}

    if codes & set(INVALIDATING_CODES):
        return INVALID
    if codes & set(LIMITING_CODES):
        return VALID_WITH_LIMITATION
    return VALID


def describe(code: str) -> str:
    """Return the frozen human-readable meaning of a reason code."""
    if code not in ALL_CODES:
        raise KeyError(f"unknown reason code: {code}")
    return ALL_CODES[code]
