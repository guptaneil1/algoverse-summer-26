# Week 3 Reference Run Index — no-rescue and fresh-random

> **ZERO PRIMARY RUNS RECORDED.** As of August 12, 2026 no reference chain has been
> launched. The table below is empty because nothing has run, not because rows
> were removed.
>
> The toy fixture chain in the second table is **not** a primary chain and must
> never be counted as one. It carries no model, consumes no accelerator, and its
> `valid` classification certifies the *pipeline*, not any scientific result.

Append one row per chain the moment it is launched — at `planned` status, before
any result exists. A chain that is added only after it succeeds produces a
survivor-biased index.

## Index

| Run ID | Condition | Seed | Commit | Config sha256 | Manifest sha256 | Artifact location | Status | Classification | Failure ref |
|---|---|---|---|---|---|---|---|---|---|
| _(none)_ | | | | | | | | | |

## Fixture chains — not primary, never analysed

| Run ID | Condition | Seed | Config | Status | Classification | Purpose |
|---|---|---|---|---|---|---|
| `fixture_joint_seed1` | toy joint, CPU, no model | 1 | `configs/experiment/toy_cpu.json` | `complete` | `valid` (exit 0, 20 checks) | Proves the runner can emit a certifiable package. Pinned by `tests/runner/test_validate_toy_chain.py` |

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

- ~~`run_manifest.json` emits no `data.partitions` block, so the validator returns
  `invalid`.~~ **Cleared 2026-08-12.** The toy chain now certifies `valid` with
  exit 0. See `FAILURE_LOG.md` F-004 and `docs/runner/week3_integrity_report.md` §2.
- **Still blocked:** `configs/experiment/primary_no_rescue.json` and
  `primary_fresh_random.json` are skeletons marked `AWAITING_JULY_31_FREEZE`, and
  `scripts/run_chain.sh` refuses to launch them. Their scientific values have no
  legitimate source until the freeze exists — and it does not:
  `docs/audits/week2_merge_gap.md` records zero tags in the repository.
- **Still blocked:** real budgets are unapproved.
  `configs/experiment/primary_pilot.json` on `integration/week-2-jul25-jul31`
  carries `"real_run_blocker": "Real-model execution is blocked until the team
  approves a tokenizer-counted real human-token budget and total optimizer-token
  budget."`

When those clear, each chain must declare a provenance source under `data` —
`partition_manifests` pointing at the five frozen partition manifests. A config
without one produces a manifest with no `partitions` block and the chain will
classify `invalid`; the runner will not synthesise provenance to paper over it.
