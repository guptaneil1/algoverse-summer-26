# Week 3 Policy Behavior Report

> **STATUS: NOT PERFORMED.**
> No policy chain has run, so there is no behaviour to report. This file is the
> prepared structure. `results/aggregates/` is empty and `docs/STATUS.md` records
> experimental results as *none*.

This report describes **what each policy did**, not whether it did well. It is
written from allocation logs, never from outcome metrics, and it exists so a
reader can verify that each policy obeyed its frozen rule.

---

## Per-generation record required from every chain

For each generation of each chain, the run must preserve:

**Pre-action state** — generation index, remaining human budget, remaining total
budget, horizon remaining, the monitored statistics the policy was allowed to
see, eligible candidate IDs, supplied seed and state.

**Scores and decisions** — mode-undercoverage inputs and normalized scores where
allowed, rank and tie resolution, spend amount, selected candidate IDs and modes,
fallback reason if any, policy version and hash.

**Post-action ledger** — human-origin and synthetic-origin optimizer tokens
consumed this generation, cumulative totals, remaining budgets, references to
generated/training/evaluation artifacts.

**Outcome references** — generation metrics stored as outputs only. Final-test
output stays invisible to the policy. A metric may be fed back only if the frozen
policy-visible state explicitly allows that monitored quantity.

## Allocation history

| Chain | Policy | Gen | Human spent | Cumulative human | Remaining | Candidates seen | Selected | Mode(s) | Tie/fallback |
|---|---|---|---|---|---|---|---|---|---|
| _(none)_ | | | | | | | | | |

## Spending shape by policy

Once chains exist, one short paragraph per policy describing **when** the budget
went out — front-loaded, uniform, back-loaded, or bursty — and, for the two
mode-aware policies, **which** modes absorbed it.

| Policy | Expected shape under the frozen rule | Observed |
|---|---|---|
| `schedule_only` | Spending follows the frozen schedule; candidate choice ignores mode score | TODO(aarav) |
| `selection_only` | Matched fixed schedule; candidates ranked by frozen mode score | TODO(aarav) |
| `joint` | Both timing and mode chosen from policy-visible state alone | TODO(aarav) |

## Tie and fallback events

Every tie resolution and every fallback, with the generation and the rule that
fired. Frequent fallbacks mean the policy rarely operated as designed, which
changes how the primary contrast should be read.

- TODO(aarav)

## Deviations from expected behaviour

Anything the policy did that the frozen rule did not obviously predict.

- TODO(aarav)

## Budget preflight results

| Chain | Policy | Lifetime human tokens | Total optimizer tokens | Matches comparator set |
|---|---|---|---|---|
| _(none)_ | | | | |

Preflight runs **before** launch. A chain without a passing preflight cannot
enter a comparative claim.

## Monitoring-bias stress test

Run only after the primary jobs are secure, under a separately labelled config
and output. Secondary or exploratory unless `PREREGISTRATION.md` says otherwise.

- Status: NOT PERFORMED
- Config: TODO(aarav) — must be a distinct file, not a flag on a primary config
- Output location: TODO(aarav)

---

### The rule that governs this file

**No hyperparameter changes.** This report will reveal surprising allocations,
frequent ties, or a policy that spends its whole budget in generation one.
Record it. Do not adjust a threshold, schedule, score, fallback, seed order, or
budget after observing primary behaviour — an outcome-driven change cannot enter
the primary analysis, and a change made here would silently invalidate every
downstream contrast.
