"""The Stage A environment freeze gate, shared by the positive-control tests.

`PROTOCOL.md` §2 carries an unresolved placeholder:

    TODO(khantushig): after the first successful Stage A install, record the
    resolved torch/transformers/datasets versions and the GPT-2 tokenizer
    revision actually used, then freeze them into requirements-lock.txt.

`scripts/reproduce_positive_control.sh` refuses to proceed while it is there,
exiting 11 (unfrozen protocol) before reaching the behaviour the tests below
target. That refusal is correct — expected behaviour cannot be declared after the
fact — but it makes those tests unrunnable until someone completes a Stage A
install, which needs a GPU. `docs/STATUS.md` records the positive control as the
project-wide critical path for exactly this reason.

Filling the placeholder by hand would fabricate frozen environment values, which
`CLAUDE.md` rule 1 forbids. So the tests are marked expected-failure rather than
deleted, weakened, or left red.

The marker is **conditional and strict**, which matters:

- conditional: it reads `PROTOCOL.md` at collection time. Resolve the TODO and the
  tests run for real on the next run — nobody has to remember to unmark them.
- strict: if a marked test passes while the TODO is still present, pytest reports
  a failure. A guard that quietly starts passing is a guard nobody is checking.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "PROTOCOL.md"

#: The exact placeholder that gates Stage A.
FREEZE_PLACEHOLDER = "TODO(khantushig)"


def stage_a_environment_is_frozen() -> bool:
    """True once the Stage A environment freeze has been recorded in PROTOCOL.md."""
    if not PROTOCOL.is_file():
        return False
    return FREEZE_PLACEHOLDER not in PROTOCOL.read_text(encoding="utf-8")


#: Apply to any test that cannot run until the Stage A environment is frozen.
requires_stage_a_freeze = pytest.mark.xfail(
    condition=not stage_a_environment_is_frozen(),
    reason=(
        f"blocked: PROTOCOL.md still contains {FREEZE_PLACEHOLDER}, so "
        "reproduce_positive_control.sh exits 11 (unfrozen protocol) before this "
        "behaviour is reached. Resolving it requires a successful Stage A install, "
        "which requires a GPU. Remove this marker when the freeze is recorded."
    ),
    strict=True,
)
