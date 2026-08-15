# Draft Preregistration

> **DRAFT — NOT FROZEN, NOT REGISTERED, AND NOT EVIDENCE OF COMPLETED WORK.**

This document will be frozen only after the published positive control passes and before novel treatment outcomes are inspected.

## Research question

Under a fixed lifetime budget of human-origin optimizer tokens, does jointly allocating those tokens across recursive generations and under-covered human-distribution modes reduce recursive-training degradation relative to the strongest schedule-only and selection-only policies?

## Primary estimand

The paired chain-level difference between the proposed joint policy and the strongest eligible non-joint baseline in area under the held-out human NLL-regret curve over the frozen recursive horizon.

## Experimental unit

One complete independently seeded recursive training chain.

## Proposed design

| Item | Draft choice |
|---|---|
| Screening model | Pythia-160M or frozen equivalent |
| Primary domain | TBD after license and split audit |
| Horizon | Ten generations |
| Initial variance sample | At least five paired chain seeds |
| Final seed count | Simulation-based power result |
| Budget levels | Zero plus two nonzero lifetime budgets, values TBD |
| Pairing | Same chain seed and starting assets across policies |

## Treatment families

1. No rescue.
2. Fresh random rescue.
3. Strongest schedule-only baseline.
4. Strongest selection-only baseline.
5. Joint time-and-mode policy.
6. Oracle allocation as a non-deployable upper bound.

## Primary outcomes

1. Chain-level area under held-out human NLL regret across generations.
2. Chain-level tail-retention score on a held-out evaluation partition.

The precise tail-retention definition must be frozen after a reliability audit and must not reuse the policy’s selection score as its only evaluation.

## Secondary outcomes

- semantic distribution coverage;
- generated-text diversity;
- memorization or nearest-neighbor overlap;
- downstream task performance where licensed and meaningful;
- per-mode regret;
- allocation trajectory;
- compute and human-token efficiency.

Secondary outcomes cannot replace a failed primary outcome.

## Planned primary contrast

At each nonzero lifetime budget, compare the joint policy with the best eligible schedule-only or selection-only baseline using paired chain seeds. “Best” must be selected using screening data or a rule frozen before confirmation outcomes are viewed.

## Power

The smallest scientifically meaningful effect is currently unresolved and must be reviewed before analysis. Chain-level variance from the screening stage will be used in a simulation matching the final repeated-generation analysis. The powered seed count will target 80–90% power for the frozen effect.

If the required seed count is unaffordable, policies, domains, or claims will be reduced. The seed count will not be reduced merely to fit the budget.

## Multiplicity

One primary contrast, one primary horizon, and one primary budget will be designated for the central claim. Other budgets, policies, domains, and outcomes will be labeled secondary and corrected or interpreted as exploratory according to the frozen analysis plan.

## Missing or failed runs

- Hardware failures and corrupted artifacts are excluded only under objective rules written before treatment inspection.
- Divergent training is a scientific outcome unless an independently verifiable implementation failure caused it.
- Failed chains remain in `FAILURE_LOG.md`.
- Replacement seeds are generated from a predeclared ordered seed list.

## Stopping rules

- Stop immediately for data leakage, invalid provenance, or incorrect token budgets.
- Do not stop early because a treatment looks successful or unsuccessful.
- Pilot completion is determined by the frozen seed list and artifact-validity rules.

## Robustness tests required before a broad claim

- independent domain;
- larger model scales;
- independent model family for an empirical-led paper;
- biased or incomplete monitoring reference;
- fixed versus fresh human anchors;
- stronger accumulation, scheduling, and selection baselines;
- long-horizon decisive contrast.

## Freeze procedure

Before the first novel treatment result is opened:

1. resolve every `TBD` that affects inference;
2. assign a version and content hash;
3. record the code and configuration commit;
4. obtain mentor and statistics-review signoff;
5. write the freeze timestamp in `DECISIONS.md`;
6. permit changes only through dated amendments that preserve the original version.
