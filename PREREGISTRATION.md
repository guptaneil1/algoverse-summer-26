
# Human Data Budget Pilot Preregistration

> **Version:** week2-fixture-v1
> **Date:** 2026-07-31
> **Scientific-config SHA-256:** `33d268deb5a7b1c13a95f4f5e4171af77403872b49dc79f2afd2a7b19d63261b`
> **Status:** Fixture comparison frozen; real-model execution blocked.
> **Evidence warning:** FIXTURE - NOT SCIENTIFIC EVIDENCE.

No primary novel-treatment outcome was used to select any rule in this
document.

## Research question

Under a fixed lifetime budget of optimizer-consumed human-origin tokens,
does jointly choosing when to spend human tokens and which under-covered
modes to target reduce recursive-training degradation relative to the
strongest eligible schedule-only or selection-only baseline?

## Primary estimand

The primary estimand is the paired chain-level difference:

`joint NLL-regret AUC - selected non-joint baseline NLL-regret AUC`

Lower values favor the joint policy.

One complete independently seeded recursive chain is one experimental
unit. Generations within one chain are dependent observations and are not
treated as separate experimental units.

## Frozen fixture design

| Item | Choice |
|---|---|
| Horizon | 10 generations |
| Lifetime human-token budget | 100 |
| Total optimizer-token budget | 10000 |
| Ordered primary seeds | 101, 202, 303, 404, 505 |
| Ordered replacement seeds | 606, 707, 808, 909, 1010 |
| Primary outcome | Held-out human NLL-regret AUC |
| Confirmatory outcome | Frozen primary tail-retention metric |
| Primary contrast | Joint minus strongest eligible non-joint baseline |
| Meaningful-effect threshold | 2% relative NLL-regret AUC |

Human-origin tokens are included inside the total optimizer-token budget.
Synthetic-origin optimizer tokens must be reduced so every policy
consumes exactly the same total optimizer-token budget.

## Real-run blocker

Real-model execution is blocked until the team approves a tokenizer-counted real human-token budget and total optimizer-token budget.

The values above are frozen only for fixtures and software-validation
tests. They may not be represented as an approved real experiment.

## Policy-visible state

A policy may use only:

1. Current generation number.
2. Remaining lifetime human-token budget.
3. Frozen rescue candidates and their non-padding token counts.
4. Monitoring statistics from the previous generation.
5. Its own previous allocation history.
6. Its supplied deterministic policy seed.

A policy may not use final-test examples, final-test metrics, future
generations, another policy's outputs, or primary treatment outcomes.

## Mode representation

Modes are frozen, auditable groups defined by the data owner before
execution. Final-test data cannot define, modify, merge, split, or tune
a mode.

## Under-coverage score

For mode `m` at generation `g`:

`u[g,m] = clip((L[g-1,m] - L[reference,m]) /
max(abs(L[reference,m]), 1e-8), 0, 1)`

`L[g-1,m]` is the previous generation's monitoring-partition NLL.

A partially missing mode receives score zero. If all monitoring is
missing, the selection order falls back to a deterministic seeded
shuffle. A nonfinite score invalidates the allocation.

## Random policy

The random policy spends 10 human tokens in every generation. It shuffles
eligible candidates using the supplied policy seed and does not read any
under-coverage score.

## Schedule-only policy

The schedule-only policy spends:

`[0, 0, 0, 0, 0, 20, 20, 20, 20, 20]`

Candidate selection is a supplied-seed shuffle. Mode under-coverage does
not affect selection.

## Selection-only policy

The selection-only policy spends 10 human tokens every generation. It
ranks candidates by descending lagged under-coverage score and breaks
ties using ascending example ID.

It cannot alter the spending schedule.

## Joint policy

The joint policy uses the maximum finite monitored mode score as urgency.

- Urgency below 0.25: desired spending is 0.
- Urgency from 0.25 to below 0.50: desired spending is 10.
- Urgency at least 0.50: desired spending is 20.

The desired amount is clamped to a feasible range that preserves the
ability to consume the exact lifetime budget by the end of the horizon.

Candidate ranking uses descending under-coverage score, followed by
ascending example ID.

## Baseline-selection rule

The eligible baselines are schedule-only and selection-only.

The baseline with lower mean NLL-regret AUC on validation-only screening
chains is selected. If their absolute difference is at most 0.001 AUC
units, selection-only is chosen.

Primary treatment outcomes cannot be used to choose the baseline.

## Meaningful-effect interpretation

Define relative difference as:

`(joint AUC - baseline AUC) / baseline AUC`

- Beneficial: mean is at most -2% and the paired interval is below zero.
- Harmful: mean is at least +2% and the paired interval is above zero.
- Negligible: the entire interval lies between -2% and +2%.
- Uncertain: every other valid result pattern.

## Exclusions

A chain may be excluded only for:

- A corrupt or missing required artifact.
- Verified incorrect token accounting.
- A verified wrong frozen config or code commit.
- Verified data leakage or manifest mismatch.
- Infrastructure termination before a required checkpoint.

Divergence, harmful performance, null performance, and negligible effects
remain scientific outcomes unless independent evidence proves an
implementation defect.

## Replacement seeds

An excluded seed is replaced with the next unused seed from the frozen
replacement list. The failed run and exclusion reason remain recorded.

## Multiplicity

There is one central budget, horizon, primary outcome, and primary
contrast. Other budgets, horizons, outcomes, and comparisons are
secondary or exploratory.

They cannot replace a failed primary analysis.

## Stopping

There is no outcome-based stopping.

Execution may stop only for a predeclared validity, accounting,
provenance, leakage, safety, or infrastructure condition.

## Amendments

Every amendment must:

1. Preserve the original version and hash.
2. Include a date and owner.
3. State the evidence motivating the change.
4. State whether primary outcomes had been accessed.
5. Never use a promising or disappointing result to alter the protocol.
