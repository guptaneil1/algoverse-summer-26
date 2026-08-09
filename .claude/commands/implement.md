---
description: Implement against a frozen interface with contract tests, in plan mode first
---

Task: $ARGUMENTS

## Before writing any code

1. Read `docs/ARCHITECTURE.md` for the dependency direction that governs this module.
2. Read the governing `docs/interfaces/*.md` and `schemas/*.json`. The schema is the
   contract. If the task requires changing it, stop and say so — a schema change is a
   cross-workstream event, not an implementation detail.
3. Read the existing tests for this module. They encode decisions that are not written
   down anywhere else.
4. Check `.github/CODEOWNERS`. If the task requires editing outside the current
   branch's workstream, name the files and the owner, and ask before touching them.
5. Check `FAILURE_LOG.md` and `DECISIONS.md` for whether this was already tried.

## Plan first

Output a plan and wait for approval:

- Files created or modified, with a one-line reason each
- The contract each change must satisfy, quoted from the schema or interface doc
- Test names you will add, and the exact assertion each makes
- What you will NOT touch
- The determinism story: where randomness enters and how the seed reaches it

## Then implement

- Tests first where practical; the test should fail for the right reason before the
  implementation lands.
- Pure functions at the boundaries. Side effects concentrated in `runner/`.
- No new dependency without saying why the standard library or an existing dependency
  is insufficient.
- Artifact writes are atomic.
- Anything you could not determine becomes `TODO(owner): <what is needed, from whom>`,
  never a guessed constant.

## Report

```
make lint && make test && make smoke
```

Paste real output. Then:

```
VERIFIED: <what the tests actually prove>
ASSUMED: <what you took on faith>
UNKNOWN: <what is still open, and who unblocks it>
```

If a test passes for a reason you do not fully understand, say so. A test passing by
accident is worse than a test failing.
