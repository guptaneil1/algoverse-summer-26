# Week 3 Policy Run Index — schedule-only, selection-only, joint

> **ZERO RUNS RECORDED.** As of August 9, 2026 no policy chain has been launched.
> The table is empty because nothing has run. `results/aggregates/` contains no
> aggregate, and `docs/STATUS.md` records experimental results as *none*.

One row per chain, appended at launch. Three conditions, each over the frozen
ordered seed list, all at identical budgets.

## Index

| Run ID | Policy | Seed | Commit | Config sha256 | Manifest sha256 | Budget preflight | Artifact location | Status | Classification |
|---|---|---|---|---|---|---|---|---|---|
| _(none)_ | | | | | | | | | |

**Budget preflight** records the result of the exact lifetime-human-token and
total-optimizer-token equality check against the eligible comparator set, run
*before* launch. A chain launched without a passing preflight cannot enter a
comparative claim.

**Classification** comes from Neil's validator, never from this workstream.

## The three conditions

| Policy | Frozen behaviour |
|---|---|
| `schedule_only` | Uses the frozen spending schedule to decide when and how much human rescue is spent; does **not** use mode-undercoverage scores to choose candidates. |
| `selection_only` | Uses the matched fixed spending schedule, but ranks candidates by the frozen mode score, tie rule, and fallback behaviour. |
| `joint` | Chooses both spending and mode allocation from only policy-visible state: remaining budget, generation, horizon, seed. Never sees final-test information. |

## Rules for this file

1. Failed and incomplete chains stay in the index with an evidence-based status.
2. A row is added at launch, not on success.
3. Record surprising allocations, ties, and fallbacks in
   `week3_policy_behavior_report.md`. **Do not adjust a threshold, schedule,
   score, fallback, seed order, or budget after observing primary behaviour.**
4. Do not wait on Khantushig's reference chains — all conditions use the frozen
   interfaces and run independently.

## Before the first row can be written

- `configs/experiment/primary_pilot.json` is a skeleton marked
  `AWAITING_JULY_31_FREEZE`; the arms, seeds, budgets, primary outcome, contrast,
  and exclusion rules are all unset.
- The manifest provenance gap in
  [`docs/validity/week3_adversarial_audit.md`](../validity/week3_adversarial_audit.md)
  section 7 applies to these chains too.

Once chains exist, aggregate with:

```bash
python scripts/aggregate_chain_results.py <chain_result paths> \
    --output results/aggregates/provisional_week3.json --label provisional
```

The aggregator rejects duplicate run IDs, chains spanning different budgets, and
schema-invalid inputs, and records every input hash so the file regenerates
exactly.
