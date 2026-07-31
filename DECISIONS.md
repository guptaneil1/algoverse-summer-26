# Decision Log

This file records project choices. A decision is not evidence that the corresponding scientific claim is true.

| ID | Date | Decision | Reason | Status |
|---|---|---|---|---|
| D-001 | 2026-07-13 | Label the repository design-only | The audited archive contained documents but no substantive experiment pipeline or verifiable results | Active |
| D-002 | 2026-07-13 | Target a future NeurIPS cycle, currently 2027 | The NeurIPS 2026 main-track deadline passed on 2026-05-06 | Active; recheck 2027 rules when released |
| D-003 | 2026-07-13 | Use “The Human Data Budget” as the provisional framing | Length, noise, fresh mixing, surprise selection, and scheduling already overlap prior work | Provisional |
| D-004 | 2026-07-13 | Block novel experiments until a published positive control reproduces | The recursive pipeline must be validated before novel comparisons can be trusted | Active |
| D-005 | 2026-07-13 | Treat recursive chains as the experimental units | Generations within one chain are dependent observations | Active |
| D-006 | 2026-07-13 | Use held-out human NLL and tail retention as proposed primary outcomes | They address model fit and rare-mode loss without relying only on generated-text aesthetics | Draft; freeze after reproduction |
| D-007 | 2026-07-13 | Separate empirical-led and theory-led scaling plans | A strong theorem and a broad empirical method require different evidence | Active |

## Unresolved decisions

| ID | Question | Evidence needed | Decision deadline |
|---|---|---|---|
| U-001 | Continued fine-tuning or controlled from-scratch training? | Positive-control behavior, compute forecast, and claim scope | Before pilot preregistration is frozen |
| U-002 | Which licensed primary domain? | License audit, split feasibility, and tail-mode definition | Before any data download used for experiments |
| U-003 | Exact lifetime budgets? | Positive-control token accounting and screening feasibility | Before treatment outcomes are viewed |
| U-004 | Exact tail-retention metric? | Reliability study and independence from selection score | Before pilot preregistration is frozen |
| U-005 | Final contribution type? | Strength of theorem versus empirical evidence | Before paper drafting |
| U-006 | Smallest scientifically meaningful effect? | Domain scale, prior variability, and mentor/statistics review | Before power analysis |

## How to add a decision

Record the date, alternatives considered, evidence available, chosen option, owner, and what future evidence would reverse the decision. Never silently change a frozen protocol.


## Week 2 method freeze decisions

**Scientific-config SHA-256:** `33d268deb5a7b1c13a95f4f5e4171af77403872b49dc79f2afd2a7b19d63261b`

| ID | Date | Owner | Decision | Status |
|---|---|---|---|---|
| D-008 | 2026-07-31 | Aarav | Use a 10-generation central fixture horizon | Fixture frozen |
| D-009 | 2026-07-31 | Aarav | Match 100 human tokens and 10,000 total optimizer tokens | Fixture frozen; real conversion blocked |
| D-010 | 2026-07-31 | Aarav | Use ordered primary seeds 101, 202, 303, 404, 505 | Fixture frozen |
| D-011 | 2026-07-31 | Aarav | Use replacement seeds 606, 707, 808, 909, 1010 | Fixture frozen |
| D-012 | 2026-07-31 | Aarav | Use clipped lagged relative mode-NLL gap | Fixture frozen |
| D-013 | 2026-07-31 | Aarav | Use a back-loaded schedule-only baseline | Fixture frozen |
| D-014 | 2026-07-31 | Aarav | Use fixed spending with score ranking for selection-only | Fixture frozen |
| D-015 | 2026-07-31 | Aarav | Use thresholded 0/10/20 joint spending with feasibility clamp | Fixture frozen |
| D-016 | 2026-07-31 | Aarav | Use a 2% relative NLL-regret AUC practical threshold | Fixture frozen |
| D-017 | 2026-07-31 | Aarav | Exclude only verified implementation, infrastructure, protocol, leakage, or accounting failures | Frozen |
| D-018 | 2026-07-31 | Aarav | Use joint versus the validation-selected strongest eligible non-joint baseline | Frozen |

### Real-execution blocker

Real-model execution is blocked until the team approves a tokenizer-counted real human-token budget and total optimizer-token budget.
