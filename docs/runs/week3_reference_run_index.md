# Week 3 Reference Run Index — no-rescue and fresh-random

> **ZERO RUNS RECORDED.** As of August 9, 2026 no reference chain has been
> launched. The table below is empty because nothing has run, not because rows
> were removed. `docs/STATUS.md` records the positive control as *not reproduced*
> and experimental results as *none*.

Append one row per chain the moment it is launched — at `planned` status, before
any result exists. A chain that is added only after it succeeds produces a
survivor-biased index.

## Index

| Run ID | Condition | Seed | Commit | Config sha256 | Manifest sha256 | Artifact location | Status | Classification | Failure ref |
|---|---|---|---|---|---|---|---|---|---|
| _(none)_ | | | | | | | | | |

**Status** is one of `planned`, `running`, `complete`, `failed`, `invalid` —
the terminal set from `schemas/run_manifest.schema.json`.

**Classification** is filled by Neil's validator, not by the runner:
`valid`, `invalid`, or `valid_with_limitation`, produced by

```bash
python scripts/validate_run.py <run_directory> --report results/validity/<run_id>.json
```

Leave it blank until the audit runs. Never self-classify a chain.

## Rules for this file

1. **Failed and incomplete chains stay.** Deleting a row is how an unfavourable
   outcome disappears. If a chain failed, record the failure class and point at
   `FAILURE_LOG.md`.
2. **A row is added at launch, not at success.**
3. **No row may be edited after the chain reaches a terminal status**, except to
   add the validator's classification.
4. **Large artifacts live in immutable external storage.** This index records the
   location and hash; Git holds only small evidence.

## Before the first row can be written

Both blocked, per `docs/audits/week3_execution_required.md`:

- `configs/experiment/primary_no_rescue.json` and `primary_fresh_random.json` are
  skeletons marked `AWAITING_JULY_31_FREEZE`. `scripts/run_chain.sh` refuses to
  launch them.
- `run_manifest.json` emits no `data.partitions` block, so the validator returns
  `invalid` with `SEPARATION_MISSING_PROVENANCE` — confirmed against the toy
  chain. Fix this before spending accelerator hours; a chain that cannot be
  certified is wasted compute.
