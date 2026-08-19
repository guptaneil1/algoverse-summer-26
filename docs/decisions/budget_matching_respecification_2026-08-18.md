# P-008 — realised budget matching, re-specified

**Date:** 2026-08-18
**Status:** Accepted by the project owner 2026-08-19, not ratified by the team.
`DECISIONS.md` P-008 and its acceptance note.
**Supersedes:** the exact-equality guard in `scripts/run_pilot.py`.
**Owner of the underlying question:** Aarav (`DECISIONS.md` U-003, U-007), per `FAILURE_LOG.md` F-015.

## What changed

`PROTOCOL.md` §4 requires every policy in a budget-matched comparison to consume the
same lifetime human-origin optimizer tokens. That was implemented as exact equality
over realised spend. This decision re-specifies it as **an equal ceiling reached up to
indivisibility**, which is F-015's option 2.

Three conditions, all required:

1. No arm exceeds its lifetime ceiling. Overspend is a hard error, never rounding.
2. Every **spending** arm lands within one indivisible candidate of the ceiling.
3. Residual spread across spending arms stays at or below one tenth of the practical
   effect threshold.

Arms whose policy spends nothing by construction are excluded from 2 and 3, and held
to an exact zero instead.

## Why exact equality had to go

It was not merely strict. It was unsatisfiable, for two independent reasons.

**The control arm.** `NoRescuePolicy` consumes zero by construction — that is what
makes it the reference condition. Comparing that zero against the spending arms meant
no configuration containing a control arm could ever pass. Every possible pilot run
would have been flagged.

**Indivisible examples.** A policy stops when the next candidate does not fit the
remaining allowance. Candidates cannot be split, so an arm cannot land exactly on its
ceiling, and where it stops depends on which candidates its seed offered it. Exact
equality across seeds is unreachable in principle, not by accident.

`FAILURE_LOG.md` F-016 records the guard defect; F-015a records the closure this
decision formalises.

## Why this is not a relaxation

The replacement is stronger than the original on everything the original could
actually test, because the original could not be satisfied and therefore carried no
information.

Condition 2 is what does the work, and its bound is **measured, not chosen**. The
largest candidate in the frozen rescue pool costs 26,902 optimizer tokens (4,235
candidates, mean 4,082.4, from `data/manifests/rescue_candidates.jsonl`). Against a
750,000 ceiling, the largest shortfall observed in the frozen grid is **291**. F-015's
own numbers — `schedule_only` roughly 233,000 short — fail condition 2 by four orders
of magnitude relative to the observed residual. `tests/runner/test_budget_matching.py`
pins that: the historical values must still fail, or the re-specification would be
laundering the confound rather than closing it.

## The part that is a judgement

Condition 3's one-tenth margin is not derived. It is chosen so that a difference in
how much human data an arm received sits an order of magnitude below the smallest
effect the study will call practically meaningful (2%, P-007). At the pilot's
threshold this permits 0.2%; the frozen grid measures 0.0381%.

This inherits P-007's weakness directly. P-007 adopted the 2% threshold as a stopgap
because the required statistics review never happened, so a review that moves the
threshold moves this bound with it. That is the stated reversal condition, and it is
the reason this is proposed rather than frozen.

## Measurements this rests on

All from a dry run of `configs/experiment/primary_pilot.json`, 25/25 chains,
2026-08-18. The dry-run path exercises real allocation, real manifests and real budget
arithmetic with simulated training.

| Arm | Realised lifetime human spend | Across five seeds |
|---|---|---|
| `no_rescue` | 0 | identical, by construction |
| `random` | 749,757 – 749,970 | varies with seed |
| `schedule_only` | 749,709 – 749,995 | varies with seed |
| `selection_only` | 749,866 | identical |
| `joint` | 749,844 | identical |

Spread across the four spending arms: **0.0381%**. Permitted: 0.2000%.

The same numbers are reproduced by reassembling four independent shard summaries
(`--check-only`), which is the path the sharded launch takes.

## What this does not decide

It does not make the pilot a powered test. `COMPUTE.md`'s compute gate still blocks the
powered experiment until pilot variance is known, and five frozen seeds against a 2%
threshold will very likely straddle the practically equivalent region. Budget matching
holding is a precondition for the contrast being interpretable at all, not evidence
about its result.
