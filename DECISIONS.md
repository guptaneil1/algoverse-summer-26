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

## Proposed decisions awaiting ratification

Made because the evidence left one defensible reading, not because the owner agreed. Each
records what would reverse it. **Ratify or override; do not leave pending silently.**

| ID | Date | Proposed by | Decision | Evidence | Reverses if |
|---|---|---|---|---|---|
| P-002 | 2026-08-18 | Assistant (Ronit's session) | The budget is denominated in `optimizer_token_count` (frozen GPT-2 tokenizer), added as a second field. `token_count` stays the whitespace word count and keeps driving the frozen `article_length_quantile` mode definition. `candidates_from_manifest` refuses an example lacking the new field rather than falling back. | `PROTOCOL.md` §3 forbids estimated counts and `models.Candidate` documents optimizer tokens, so the budget cannot be words. `docs/data/mode_definition_audit.md:30` names the "whitespace-split rule" as part of the frozen mode definition, so the mode unit should not move. Measured divergence 1.096-1.318x per example (`FAILURE_LOG.md` F-010b). Partition hashes verified unchanged, since `_manifest_hash` covers only `[example_id, content_hash]`. | Neil determines the mode definition should also move to BPE, in which case the cutoffs re-freeze and `token_count` is recomputed. That is a scientific re-freeze, deliberately not done here. |
| P-001 | 2026-08-18 | Assistant (Ronit's session) | `tail_retention`'s reference and current mode scores are a **monotone-decreasing transform of** mean held-out NLL, not raw NLL. `docs/evaluation/tail_retention_freeze.md` §3 amended; reference implementation `evaluation.real.mode_nll_to_retention_scores`. | Four artifacts fix higher-is-better against one that did not: `evaluation/tail.py`'s `clip(current/reference, 0, 1)`; its docstring; `tests/evaluation/test_metrics.py` asserting `({"rare":0.5},{"rare":1.0}) -> 0.5`; and `runner/chain.py` passing `1.0 - undercoverage`. Raw NLL would clip a degraded model to 1.0 — see `FAILURE_LOG.md` F-011. | Neil determines `tail.py` should invert instead, making raw NLL the correct input. The frozen decision (ratio-based primary, gen-0 snapshot, validation partition) is untouched either way. |

## Unresolved decisions

| ID | Question | Evidence needed | Decision deadline |
|---|---|---|---|
| U-001 | Continued fine-tuning or controlled from-scratch training? | Positive-control behavior, compute forecast, and claim scope | Before pilot preregistration is frozen |
| U-003 | Exact lifetime budgets? | Positive-control token accounting and screening feasibility | Before treatment outcomes are viewed |
| U-004b | Exact `nll_threshold_candidate` value? | Baseline NLL distribution on the validation partition from a real generation-0 model | Before primary outcomes are opened. Narrowed 2026-08-08 from U-004: the metric *choice* (`tail_retention`, ratio-based, primary) is now frozen — `docs/evaluation/tail_retention_freeze.md`. Only the numeric threshold remains open. **Its input now exists (2026-08-18):** the screening run produced a generation-0 baseline and its per-mode validation NLL distribution — common 3.223015, mid 3.235674, tail 3.127379 — recorded in `docs/screening/pipeline_validation_2026-08-18.md`. Setting the threshold is now a decision rather than a blocked one, though it should be re-derived from the frozen pilot baseline rather than from a screening run. |
| U-005 | Final contribution type? | Strength of theorem versus empirical evidence | Before paper drafting |
| U-006 | Smallest scientifically meaningful effect? | Domain scale, prior variability, and mentor/statistics review | Before power analysis |

**Evidence status, 2026-08-17.** The Stage A execution supplied the evidence named in the
rows above for U-001 (positive-control behavior, compute forecast) and U-003
(positive-control token accounting, screening feasibility). It is collected in
`docs/evidence/stage_b_freeze_evidence.md`, which decides nothing — U-001 and U-003 remain
open and remain Aarav's. U-004b is one ~50-second training run from having its evidence.
U-005 and U-006 are unchanged and need human judgment.

That document also puts arithmetic on assumption A7: at the measured cost, a pilot at
WikiText-2 token scale is roughly 23 accelerator-hours, and a full WikiText-103 pilot is
roughly 900. The subsample choice therefore dominates every other cost decision and couples
U-002 to U-003.

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

## Week 2 data & evaluation freeze decisions

| ID | Date | Owner | Decision | Reason | Status |
|---|---|---|---|---|---|
| D-019 | 2026-08-08 | Neil | Finalize WikiText-103-v1 as the primary licensed domain, closing U-002 | Week 1 audit already recommended it (`data/datasheet.md`); Week 2 confirmed real access and licensing are unblocked — the corpus was actually downloaded and built, not just planned. Fallback (OpenWebText2) stays documented, unused. | Frozen. Dataset revision pinned to `b08601e04326c79dfdd32d625aee71d232d685c3`. |
| D-020 | 2026-08-08 | Neil | Freeze `article_length_quantile` as the primary mode definition over `wikipedia_article_category` | Reliability/independence audit (`docs/data/mode_definition_audit.md`): the category candidate needs Wikipedia metadata absent from the frozen dataset revision, sourced from a live system that can drift after the freeze date. The quantile candidate needs nothing outside the frozen corpus. | Frozen. tail<=1106 tokens, common>2661 tokens, computed from the train split. |
| D-021 | 2026-08-08 | Neil | Deduplicate the canonical WikiText-103-v1 release by exact content hash (test > validation > train priority) before partitioning | The upstream release contains 241 exact-duplicate articles, including one ("The Hustler (film)") that appears in both train and test — real train/test leakage in the upstream data, found by the Week 2 overlap build, not injected by this project. Priority order guarantees held-out splits are never reduced and no duplicate can leak train↔eval. | Frozen. Full accounting in `docs/data/overlap_report.md`. |
| D-022 | 2026-08-08 | Neil | Freeze `tail_retention` (ratio-based) as the primary tail-retention metric, `nll_gap` as secondary, closing the metric-choice half of U-004 | Reliability/independence audit (`docs/evaluation/tail_retention_freeze.md`): `tail_retention` is the metric that actually measures retention against a fixed starting point, matching D-006's framing; `nll_gap`'s immediate computability (no reference snapshot needed) is real but doesn't answer the same question. Both are already proven independent of the policy `undercoverage_score`. | Frozen. `nll_threshold_candidate` remains open as U-004b — it needs a real baseline model. |

### Scope note

D-019–D-022 unblock the Stage 4 Human Data Budget pilot's data/evaluation contract. They do
**not** retroactively unblock Stage A's `positive_control_adapter.build_chain_result` refusal —
Stage A's upstream pipeline (GPT-2 / WikiText-2) produces no mode-level evaluation at all, so it
has no input for either tail-retention metric regardless of which is primary
(`docs/evaluation/tail_retention_freeze.md` §4).
