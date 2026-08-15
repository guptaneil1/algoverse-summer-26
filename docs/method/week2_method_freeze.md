
# Week 2 Method Freeze

**Version:** week2-fixture-v1  
**Scientific-config SHA-256:** `33d268deb5a7b1c13a95f4f5e4171af77403872b49dc79f2afd2a7b19d63261b`  
**Status:** Fixture-valid method; real-model execution blocked.  
**Warning:** FIXTURE - NOT SCIENTIFIC EVIDENCE.

## Goal

The experiment compares four ways of spending the same lifetime supply
of human-origin optimizer tokens:

1. Random rescue.
2. Schedule-only rescue.
3. Selection-only rescue.
4. Joint time-and-mode rescue.

Every compared policy must receive exactly the same lifetime human-token
budget and exactly the same total optimizer-token budget.

## Generation definition

One generation is one complete:

`train -> generate -> rescue -> evaluate -> checkpoint`

transition in a recursive chain.

## Accounting requirements

For every policy `p`:

`sum over generations of human_tokens[p,g] = 100`

and:

`sum over generations of total_optimizer_tokens[p,g] = 10000`

Repeated presentations count every optimizer exposure.

Padding tokens do not count.

Human-origin and synthetic-origin token totals remain separately
auditable.

## Under-coverage score

For mode `m`:

`u[g,m] = clip((L[g-1,m] - L[reference,m]) /
max(abs(L[reference,m]), 1e-8), 0, 1)`

Only previous-generation monitoring information may be used.

Final-test data is never policy-visible.

## Random-policy pseudocode

    budget = min(10, remaining_human_tokens)
    shuffle candidates using supplied seed
    select without exceeding budget

## Schedule-only pseudocode

    budget = frozen_schedule[current_generation]
    shuffle candidates using supplied seed
    select without exceeding budget

Frozen schedule:

    0, 0, 0, 0, 0, 20, 20, 20, 20, 20

## Selection-only pseudocode

    budget = min(10, remaining_human_tokens)
    score candidates using lagged mode under-coverage
    sort by descending score
    break ties by ascending example_id
    select without exceeding budget

## Joint-policy pseudocode

    urgency = maximum finite monitored mode score

    if urgency < 0.25:
        desired = 0
    else if urgency < 0.50:
        desired = 10
    else:
        desired = 20

    lower = max(
        0,
        remaining_human_tokens
        - 20 * future_generation_count
    )

    upper = min(
        20,
        remaining_human_tokens
    )

    budget = clamp(desired, lower, upper)

    sort candidates by descending score
    break ties by ascending example_id
    select without exceeding budget

## Hyperparameters

| Parameter | Value |
|---|---:|
| Horizon | 10 |
| Lifetime human tokens | 100 |
| Total optimizer tokens | 10000 |
| Base generation spend | 10 |
| Maximum generation spend | 20 |
| Token granularity | 10 |
| Low urgency threshold | 0.25 |
| High urgency threshold | 0.50 |
| Score floor | 0 |
| Score ceiling | 1 |
| Denominator floor | 1e-8 |
| Practical effect threshold | 2% |
| Primary seeds | 101, 202, 303, 404, 505 |

## Difference from non-joint baselines

Schedule-only may alter timing but may not target modes.

Selection-only may target modes but may not alter its fixed spending
schedule.

Joint is the only eligible policy that may alter both spending timing and
mode allocation using the frozen policy-visible state.

## Missing monitoring

A partially missing mode receives score zero.

If every mode is missing:

- Selection-only uses a seeded random candidate order.
- Joint spends its base amount of 10 tokens and uses a seeded random
  candidate order.

## Validity rules

A comparison is invalid when it has:

- Mismatched paired seed sets.
- Unequal lifetime human-token budgets.
- Unequal total optimizer-token budgets.
- Nonfinite policy scores.
- Data leakage.
- Config or manifest hash mismatches.

Poor or harmful performance is not an implementation exclusion.

## No-outcome statement

These rules were written using interfaces, fixtures, and fake results.

No primary novel-treatment result influenced the score, schedule, seed
list, threshold, exclusion rule, or interpretation language.

## Real-run blocker

Real-model execution is blocked until the team approves a tokenizer-counted real human-token budget and total optimizer-token budget.
