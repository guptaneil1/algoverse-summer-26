# Decision Log

This file records project choices. A decision is not evidence that the corresponding scientific claim is true.

| ID | Date | Decision | Reason | Status |
|---|---|---|---|---|
| D-001 | 2026-07-13 | Label the repository design-only | The audited archive contained documents but no substantive experiment pipeline or verifiable results | Active |
| D-002 | 2026-07-13 | Target a future NeurIPS cycle, currently 2027 | The NeurIPS 2026 main-track deadline passed on 2026-05-06 | Active; recheck 2027 rules when released |
| D-003 | 2026-07-13 | Use “The Human Data Budget” as the provisional framing | Length, noise, fresh mixing, surprise selection, and scheduling already overlap prior work | Provisional |
| D-004 | 2026-07-13 | Block novel experiments until a published positive control reproduces | The recursive pipeline must be validated before novel comparisons can be trusted | **Condition met 2026-08-07.** Stage A reproduced both arms within 5% of the published values (`docs/positive_control/report.md`, decision `valid_with_limitation`). The block lifts, subject to D-008 and D-010. |
| D-005 | 2026-07-13 | Treat recursive chains as the experimental units | Generations within one chain are dependent observations | Active |
| D-006 | 2026-07-13 | Use held-out human NLL and tail retention as proposed primary outcomes | They address model fit and rare-mode loss without relying only on generated-text aesthetics | Draft; freeze after reproduction |
| D-007 | 2026-07-13 | Separate empirical-led and theory-led scaling plans | A strong theorem and a broad empirical method require different evidence | Active |
| D-008 | 2026-08-07 | Compare against the paper at generation 9, not this project's frozen generation 10 | The paper reports generations 0–9 in nine separate places, so Gen 9 is its endpoint; comparing our Gen 10 against their Gen 9 would compare different quantities. Chosen on that basis, not on which side of the tolerance band it falls — at Gen 10 the fully synthetic arm would sit outside it, and both readings are published side by side. | Active. Any future comparison against this paper uses generation 9. |
| D-009 | 2026-08-07 | Cap upstream's self-BLEU diagnostic at `--self_bleu_n_sample 50` (default 1000) | The default drives an O(n²) NLTK sweep of ~10⁶ pair comparisons per generation, several times the cost of the decoding it describes. It is computed after `data.json` is written and read only by a disabled `wandb.log` and a diagnostic file, so it cannot affect training data or any frozen metric. | Active. Applied identically to both arms. Consequence: our self-BLEU is not comparable to the paper's published figure. |
| D-010 | 2026-08-07 | Hold Stage A's decision at `valid_with_limitation` although the frozen decision table's `valid` row is satisfied | `FAILURE_LOG.md` `PC-2026-08-03-B`, written 2026-08-03 before the numbers were known, set that ceiling for a run completed before the published values existed. This run is that case. Lifting the ceiling after seeing that the numbers agree is the move the protocol exists to prevent. | Active, and **reversible only by explicit written team decision** citing `expected_vs_observed.md` §5. Not to be changed by relabelling. |
| D-011 | 2026-08-07 | Do not retro-edit run records to mark lost artifacts as `pruned` | 42 artifacts were hashed at run time and then lost when the ephemeral host was reclaimed (`PC-2026-08-07-H`). `--prune-models` was never passed, so `pruned: false` was true when the driver wrote it. Marking them pruned would make the adapter's ingest succeed at the cost of a false record. | Active. Loss inventoried separately in `measurements/artifact_retention.json`. |

## Unresolved decisions

| ID | Question | Evidence needed | Decision deadline |
|---|---|---|---|
| U-001 | Continued fine-tuning or controlled from-scratch training? | Positive-control behavior, compute forecast, and claim scope | Before pilot preregistration is frozen |
| U-002 | Which licensed primary domain? | License audit, split feasibility, and tail-mode definition | Before any data download used for experiments |
| U-003 | Exact lifetime budgets? | Positive-control token accounting and screening feasibility | Before treatment outcomes are viewed |
| U-004 | Exact tail-retention metric? | Reliability study and independence from selection score | Before pilot preregistration is frozen. **Now blocking a concrete artifact:** `positive_control_adapter.build_chain_result` refuses to emit a `ChainResult` for Stage A because both schemas require `tail_retention` and no measure exists. |
| U-005 | Final contribution type? | Strength of theorem versus empirical evidence | Before paper drafting |
| U-006 | Smallest scientifically meaningful effect? | Domain scale, prior variability, and mentor/statistics review | Before power analysis |

## How to add a decision

Record the date, alternatives considered, evidence available, chosen option, owner, and what future evidence would reverse the decision. Never silently change a frozen protocol.
