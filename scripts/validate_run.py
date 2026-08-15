#!/usr/bin/env python3
"""Three-state run validator.

Implements the `docs/weekly/WEEK_3.md` Neil deliverable: "Build one command that
returns ``valid``, ``invalid``, or ``valid_with_limitation`` for any run."

Classification is objective and derived only from artifacts on disk. The
validator never inspects treatment outcomes, so it cannot be influenced by
whether a result is favourable. Blocking failures are drawn from
``PROTOCOL.md`` §3 (data separation, token accounting, provenance,
reproducibility).

Exit codes
----------
0   valid
2   valid_with_limitation
1   invalid
64  usage error — the validator did not run

64 exists so that 2 stays exclusive to ``valid_with_limitation``. argparse exits
with 2 on any usage error, which would otherwise be indistinguishable from a
genuine limitation: a CI wrapper treating 2 as "proceed with acknowledgement"
would proceed on a validator that produced no verdict at all.

The non-zero code for ``valid_with_limitation`` is deliberate: a limitation must
be acknowledged explicitly by whoever consumes the result, not silently treated
as a clean pass.

Usage
-----
    python scripts/validate_run.py RUN_DIR [RUN_DIR ...] [--json]

For a batch invocation the process exits with the worst state observed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[1]

VALID = "valid"
VALID_WITH_LIMITATION = "valid_with_limitation"
INVALID = "invalid"

_EXIT_CODES = {VALID: 0, VALID_WITH_LIMITATION: 2, INVALID: 1}
_SEVERITY = {VALID: 0, VALID_WITH_LIMITATION: 1, INVALID: 2}
EXIT_USAGE = 64  # sysexits.h EX_USAGE; keeps 2 exclusive to valid_with_limitation


@dataclass
class Verdict:
    """Classification of a single run directory."""

    run_directory: str
    state: str = VALID
    blocking: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def block(self, reason: str) -> None:
        self.blocking.append(reason)
        self.state = INVALID

    def limit(self, reason: str) -> None:
        self.limitations.append(reason)
        if self.state != INVALID:
            self.state = VALID_WITH_LIMITATION

    def as_dict(self) -> dict[str, object]:
        return {
            "run_directory": self.run_directory,
            "state": self.state,
            "blocking_failures": self.blocking,
            "limitations": self.limitations,
        }


def _load(path: Path, verdict: Verdict, label: str) -> dict | None:
    """Read one artifact, or record a blocking failure and return ``None``.

    Three failure modes are handled deliberately:

    - ``json.loads("null")`` returns ``None`` *without raising*. Returning that
      straight through would collide with this function's own failure sentinel,
      and the caller's ``is None`` early-return would then skip every check and
      report the run as valid. The isinstance guard is what closes that hole.
    - ``read_text`` raises ``UnicodeDecodeError`` on non-UTF-8 bytes and
      ``OSError`` when the path is a directory or unreadable. Both are caught,
      because an uncaught one aborts the whole process and, in batch mode,
      discards every verdict computed so far.
    - A top-level JSON array or string parses fine but is not an artifact.
    """

    if not path.exists():
        verdict.block(f"{label} missing at {path}")
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        # JSONDecodeError and UnicodeDecodeError are both ValueError;
        # PermissionError and IsADirectoryError are both OSError.
        verdict.block(f"{label} could not be read as JSON: {exc}")
        return None
    if not isinstance(document, dict):
        verdict.block(
            f"{label} is not a JSON object (parsed as {type(document).__name__})"
        )
        return None
    return document


def _check_schema(document: dict, schema_name: str, verdict: Verdict, label: str) -> bool:
    try:
        validate_json(document, ROOT / "schemas" / schema_name)
    except Exception as exc:  # jsonschema raises a family of validation errors
        verdict.block(f"{label} failed schema {schema_name}: {exc}")
        return False
    return True


def _check_budget_matching(manifest: dict, result: dict, verdict: Verdict) -> None:
    """Budget equality is the fairness constraint (PROTOCOL.md §4)."""
    budget = manifest.get("budget", {})
    declared_human = budget.get("lifetime_human_optimizer_tokens")
    declared_total = budget.get("total_optimizer_tokens")
    consumed_human = result.get("consumed_human_tokens")
    consumed_total = result.get("consumed_total_tokens")

    if declared_human is not None and consumed_human != declared_human:
        verdict.block(
            "lifetime human-token budget violated: manifest declares "
            f"{declared_human}, chain consumed {consumed_human}"
        )
    if declared_total is not None and consumed_total != declared_total:
        verdict.block(
            "total optimizer-token budget violated: manifest declares "
            f"{declared_total}, chain consumed {consumed_total}"
        )
    if (
        consumed_human is not None
        and consumed_total is not None
        and consumed_human > consumed_total
    ):
        verdict.block(
            f"impossible accounting: human tokens {consumed_human} exceed "
            f"total tokens {consumed_total}"
        )


def _check_metric_series(result: dict, verdict: Verdict) -> None:
    metrics = result.get("metrics") or []
    generations = [metric["generation"] for metric in metrics]

    if len(set(generations)) != len(generations):
        verdict.block(f"duplicate generation indices in metrics: {generations}")
    elif generations and sorted(generations) != list(range(len(generations))):
        verdict.block(
            "metric generations must be contiguous from zero, got "
            f"{sorted(generations)}"
        )

    completed = result.get("generations_completed")
    if completed is not None and len(metrics) != completed:
        # Blocking, not a limitation: the artifact contradicts itself, so any
        # per-generation analysis reads a different number of points than the
        # chain claims to have run. A limitation here would also mask the
        # separate "incomplete chain" message from _check_status_and_scope.
        verdict.block(
            f"metric count {len(metrics)} does not match generations_completed "
            f"{completed}"
        )


def _check_identity(manifest: dict, result: dict, verdict: Verdict) -> None:
    if manifest.get("run_id") != result.get("run_id"):
        verdict.block(
            f"run_id mismatch: manifest {manifest.get('run_id')!r} vs chain result "
            f"{result.get('run_id')!r}"
        )

    manifest_policy = (manifest.get("policy") or {}).get("name")
    if manifest_policy is not None and manifest_policy != result.get("policy"):
        verdict.block(
            f"policy mismatch: manifest {manifest_policy!r} vs chain result "
            f"{result.get('policy')!r}"
        )

    manifest_seed = (manifest.get("randomness") or {}).get("chain_seed")
    if manifest_seed is not None and manifest_seed != result.get("chain_seed"):
        verdict.block(
            f"chain_seed mismatch: manifest {manifest_seed} vs chain result "
            f"{result.get('chain_seed')}"
        )


def _check_status_and_scope(manifest: dict, result: dict, verdict: Verdict) -> None:
    status = manifest.get("status")
    if status == "invalid":
        verdict.block("manifest status is 'invalid'")
    elif status in {"planned", "running"}:
        verdict.block(f"manifest status {status!r} — run has not completed")
    elif status == "failed":
        verdict.limit("manifest status is 'failed'; artifacts retained for the failure log")

    if manifest.get("stage") == "fixture":
        # ASCII only: this string reaches Windows CI consoles under cp1252,
        # where an em dash renders as a replacement character.
        verdict.limit(
            "stage is 'fixture' - contract test artifact, not scientific evidence"
        )

    # Fails closed: the schema does not require working_tree_clean, so an absent
    # key is "unknown", not "clean". Treating unknown as clean would silently
    # drop a PROTOCOL.md §3 reproducibility limitation.
    if manifest.get("working_tree_clean") is not True:
        verdict.limit(
            "working tree was dirty or unrecorded at run time; "
            "exact code state is not recoverable"
        )

    horizon = manifest.get("horizon")
    completed = result.get("generations_completed")
    if horizon is not None and completed is not None:
        if completed < horizon:
            verdict.limit(
                f"incomplete chain: {completed} of {horizon} generations completed"
            )
        elif completed > horizon:
            # Over-running a preregistered horizon is a protocol violation, not a
            # bonus. Only the under-run direction was previously checked.
            verdict.block(
                f"chain exceeded its declared horizon: {completed} generations "
                f"completed against horizon {horizon}"
            )

    if result.get("valid") is False:
        reason = result.get("exclusion_reason")
        if reason:
            verdict.limit(f"chain self-reports invalid with recorded reason: {reason}")
        else:
            verdict.block("chain self-reports invalid with no exclusion_reason recorded")
    elif result.get("exclusion_reason"):
        # The inverse contradiction: an exclusion was recorded but the chain
        # still claims validity. One of the two fields is wrong, and guessing
        # which would be worse than refusing the artifact.
        verdict.block(
            "chain reports valid=true while recording an exclusion_reason: "
            f"{result['exclusion_reason']!r}"
        )


def validate_run(run_directory: Path) -> Verdict:
    """Classify one run directory as valid, valid_with_limitation, or invalid."""

    verdict = Verdict(run_directory=str(run_directory))

    manifest = _load(run_directory / "run_manifest.json", verdict, "run manifest")
    result = _load(run_directory / "chain_result.json", verdict, "chain result")
    if manifest is None or result is None:
        return verdict

    manifest_ok = _check_schema(manifest, "run_manifest.schema.json", verdict, "run manifest")
    result_ok = _check_schema(result, "chain_result.schema.json", verdict, "chain result")
    if not (manifest_ok and result_ok):
        return verdict

    _check_identity(manifest, result, verdict)
    _check_budget_matching(manifest, result, verdict)
    _check_metric_series(result, verdict)
    _check_status_and_scope(manifest, result, verdict)
    return verdict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("run_directory", nargs="+", type=Path)
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable verdicts"
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 2 on usage errors, colliding with valid_with_limitation.
        # --help exits 0 and must stay 0.
        return EXIT_USAGE if exc.code else 0

    verdicts = [validate_run(directory) for directory in args.run_directory]

    if args.json:
        print(json.dumps([verdict.as_dict() for verdict in verdicts], indent=2))
    else:
        for verdict in verdicts:
            print(f"{verdict.state.upper()}  {verdict.run_directory}")
            for reason in verdict.blocking:
                print(f"    BLOCKING:   {reason}")
            for reason in verdict.limitations:
                print(f"    LIMITATION: {reason}")

    worst = max(verdicts, key=lambda verdict: _SEVERITY[verdict.state])
    return _EXIT_CODES[worst.state]


if __name__ == "__main__":
    sys.exit(main())
