# Claim Ledger

No claim in this file is a result unless its status is explicitly `SUPPORTED BY RUN ARTIFACTS`.

## Current claims

| ID | Type | Exact statement | Evidence needed | Status |
|---|---|---|---|---|
| C-000 | Fact about this repository | No Human Data Budget experiment has been run or verified in this repository | Repository audit | Verified |
| C-001 | Literature-grounded motivation | Recursive training on generated data can degrade model fit or distributional coverage in studied settings | Primary model-collapse papers | Supported with scope qualifiers |
| C-002 | Hypothesis | At equal lifetime human-token budget, joint allocation across time and under-covered modes reduces chain-level regret relative to the strongest schedule-only and selection-only baselines | Powered recursive-chain experiment | Untested |
| C-003 | Hypothesis | The advantage of targeted allocation decreases or reverses when the monitoring reference omits globally important modes | Predeclared monitoring-bias intervention | Untested |
| C-004 | Provisional novelty claim | Joint finite-lifetime human-token allocation across generation and mode is distinct from the closest fresh-mixing, scheduling, surprise-selection, and semantic-sampling work | Saturated literature search and external expert review | Unverified |
| C-005 | Proposed mechanism | Under-covered modes with high projected future regret receive greater marginal value from human anchors | Theory or mechanism intervention plus experiment | Untested |

## Claim C-002 contract

### Allowed wording now

> The project will test whether joint allocation improves human-rescue efficiency under a fixed lifetime budget.

### Forbidden wording now

- “The method prevents model collapse.”
- “The method is optimal.”
- “The method beats random rescue.”
- “Five percent targeted data beats ten percent random data.”
- “This is the first human-data scheduling method.”

### Required comparison

At the same total number of human-origin training tokens, compare the joint policy with:

1. no rescue;
2. fresh random human mixing;
3. strongest schedule-only allocation;
4. strongest selection-only allocation;
5. accumulation where scientifically applicable;
6. oracle mode information as an upper bound, never as a deployable baseline.

### Falsification

C-002 is not supported if the powered interval for the joint-versus-strongest-non-joint contrast includes the frozen practically equivalent or harmful region, or if the result fails across the predeclared confirmation settings.

## Claim C-004 novelty contract

### Required search families

- recursive learning plus fresh real/human data;
- finite data-budget scheduling across iterations;
- active, surprise, tail, or semantic sample selection;
- adaptive center/edge or coverage sampling;
- selection bias under partial or corrupted references;
- verification and synthetic-data filtering;
- accumulation and replacement protocols.

### Novelty stop rule

If primary-source review finds a method that already jointly allocates a fixed lifetime human-data budget across recursive time and human-distribution modes under comparable feedback, withdraw or rewrite C-004 before implementing the proposed method.

## Result promotion rule

A hypothesis can become a result only when the following are linked:

- frozen protocol version;
- code commit;
- environment and asset revisions;
- run manifests;
- raw chain-level outcomes;
- exact analysis command;
- uncertainty calculation;
- generated table or figure hash;
- limitations and failed robustness checks.
