# Reconciling the Overleaf draft with the executed run

**Written 2026-08-20.** A second manuscript of this project exists outside the repository —
an Overleaf draft titled *"Where Should Scarce Human Data Go? A Budgeted Allocation Across
Time and Modes in Recursive Model Training"*, authored Aarav Thilop, with
`[RESULT PLACEHOLDER]` markers throughout.

This document exists because that draft is **structurally sound and factually stale**, and
because the results it is waiting for now exist. It gives every fill-in value and every
correction, so the reconciliation is a transcription job rather than a research one.

---

## 0. The decision that has to be made before any of this matters

**There are two manuscripts of the same paper**, and only one can be submitted.

| | Repository (`paper/main.tex`) | Overleaf draft |
|---|---|---|
| Results | Executed, every number a generated macro | `[RESULT PLACEHOLDER]` throughout |
| References | 31, in `references.bib` | 7, hand-written `thebibliography` |
| Builds | Yes — 18 pages, 0 errors, 0 undefined refs | Not built here |
| Numbers can drift from artifacts | No — a bare decimal fails a test | Yes — nothing checks it |
| Author line | `Anonymous August 2026 Project Draft` | Named author |
| Section 4 estimand | Corrected (F-027) | Carries the defect |
| Overview figure ("Figure 1") | Pipeline diagram, in the appendix | None |

**This is an owner decision, not mine.** The two plausible resolutions:

1. **Overleaf is the submission.** Then apply every correction in §2 and every value in §1
   by hand, and accept that the manuscript loses the drift protection — no test will catch
   a mistyped number in Overleaf.
2. **The repository is the submission.** Then the Overleaf draft's genuinely better
   material — the introduction's framing, the related-work paragraphs, the interpretation
   rule in Appendix C — is merged into `paper/sections/`, and Overleaf is retired.

What must not happen is both continuing. Two manuscripts diverging while one is being
polished against artifacts and the other is being edited by hand is how a submitted paper
ends up containing a number nobody can reproduce.

---

## 1. Every placeholder, and what fills it

All values from `results/runs/primary_pilot_v2_2026-08-20/`, generated into
`paper/tables/pilot_macros.tex`. Independently recomputed by
`scripts/reproduce_pilot_table.py`, which shares no code with the generator.

### Abstract — `[RESULT PLACEHOLDER]`

> Across 25 chains at matched budgets, joint time-and-mode allocation did not improve on the
> strongest non-joint baseline: paired mean difference +0.0103, 95% interval
> [−0.0092, +0.0297], or +0.45% relative. The interval lies entirely inside the frozen ±2%
> practical-equivalence region, so this is an equivalence rather than an inconclusive
> comparison. The secondary contrasts locate the effect that does exist: spending a human
> budget at all is worth 4.04% against a control trained on identical data volume, targeting
> under-covered modes a further 9.59%, and scheduling when to spend 0.41% with an interval
> containing zero.

### §6.1 Validity and Budget Matching

| Quantity | Value |
|---|---|
| Chains per arm | 5, all five arms |
| Total chains | 25 of 25 complete, 0 failed |
| Excluded | **0**. No replacement seeds used |
| Certification | 25 `valid_with_limitation`, **0 `invalid`** |
| Lifetime human tokens, spending arms | 749,709 – 749,995 against a 750,000 ceiling |
| Human spread | **0.0381%**, against 0.2000% permitted |
| Total optimizer tokens | **16,678,912, identical in every chain of every arm** |
| Total spread | **0.0000%** |
| Control arm | exactly 0 human tokens, 5 chains |

Both fairness constraints hold. State that before any performance number, as the draft's own
subsection instructs.

### §6.2 Recursive Degradation

| Policy | NLL-regret AUC | SD | CV | Tail retention |
|---|---|---|---|---|
| No rescue (control) | 2.6431 | 0.0140 | 0.53% | 0.8676 |
| Fresh random | 2.5364 | 0.0080 | 0.32% | 0.8769 |
| Schedule-only | 2.5261 | 0.0194 | 0.77% | 0.8846 |
| Selection-only | 2.2931 | 0.0250 | 1.09% | 0.9024 |
| Joint time-and-mode | 2.3034 | 0.0221 | 0.96% | 0.9024 |

Lower AUC is better; higher tail retention is better.

### §6.3 Joint vs. Single-Dimension — the five items the draft asks for

1. **Baseline selected:** selection-only (lowest mean AUC among the four non-joint arms).
2. **Mean paired joint − baseline:** **+0.0103**.
3. **Interval:** **[−0.0092, +0.0297]** — see §2.2, this is a *t* interval, not a bootstrap.
4. **Relative effect:** **+0.45%**.
5. **Preregistered interpretation:** **negligible.** By the draft's own Appendix C rule, the
   entire interval lies within ±τ, τ = 0.02.

### §6.4 Tail Retention

| Contrast | Mean | 95% interval |
|---|---|---|
| joint − selection-only (confirmatory) | +0.00003 | [−0.00100, +0.00105] |
| schedule-only − fresh random | +0.00766 | [+0.00563, +0.00968] |

The confirmatory outcome **agrees** with the primary on the primary contrast, and more
tightly. It **disagrees** on the timing contrast — an interval excluding zero at 0.87% of the
fresh-random level. Report the disagreement; do not report only the null.

### §6.5 Allocation Behavior — **cannot be filled**

The per-generation allocation records exist only in the chain checkpoints, which were not
archived before the compute was released (`FAILURE_LOG.md` F-028). **Cut this subsection or
replace it with the limitation.** Do not describe allocation behaviour from memory or
inference.

This is the reviewer's obvious follow-up — *did joint actually behave differently, or did it
converge to selection-only's allocation?* — and the honest answer is that the record was not
kept. Both arms consumed 749,827 human tokens, identically, which is consistent with both
reaching the same reconciliation ceiling and says nothing about timing or targeting.

### §7 Conclusion — `[RESULT PLACEHOLDER]`

> Under matched lifetime human-token and total optimizer-token budgets, joint time-and-mode
> allocation was practically equivalent to the strongest implemented non-joint baseline. At
> this operating point the allocation question decomposes: which under-covered modes a fixed
> human budget targets changes the outcome, and when within the chain it is spent does not.

### §Limitations — the result-dependent addition the draft reserves

Three sentences, all required:

> Three of the seven predeclared comparators were not implemented, including a
> non-deployable oracle upper bound, so the headroom above every policy measured here is
> unknown and an equivalence between two policies says nothing about how far either sits
> from what is achievable. The per-generation allocation records were not archived, so
> whether the joint policy reached its total by a different route than selection-only cannot
> be determined. The practical-equivalence threshold on which the null rests has been
> checked against measured anchors and never externally reviewed, and an equivalence rests
> on that threshold more directly than a positive finding would.

### Remaining markers

- `nll_threshold_candidate = [FILL VALUE]` — this was to be frozen *before* outcomes opened.
  Outcomes are open. **Delete the placeholder**; filling it now would be setting a threshold
  with knowledge of the results.
- Appendix D result placeholders — per-seed outcomes and generation-wise NLL are derivable
  from `chain_result.json`; budget allocation by generation and by mode are **not** (F-028).

---

## 2. Corrections the draft needs regardless of which manuscript wins

### 2.1 The primary-outcome formula is wrong — highest severity

The draft defines

```
A^π = Σ_g w_g (L_g^π − L_g^ref),   Σ_g w_g = 1
```

The analysis computes regret against **the chain's own generation-0 value**, by **trapezoid**,
**unnormalised**:

```
r_g = L_g − L_0 ,   A = Σ_{g=1}^{G−1} ½(r_{g−1} + r_g)
```

Three differences, none cancelling. `L_g^ref` **appears in no artifact**, so the stated
formula is not computable from the released data at all. And the trapezoid weights sum to
G−1 = 9, so a reader who normalised them would obtain **0.2948** where the paper reports
**2.65316** — a factor of exactly nine.

**No reported number changes.** What is wrong is the sentence describing what those numbers
are. Recorded as `FAILURE_LOG.md` F-027; the repository's §4 is already corrected and the
corrected wording can be lifted from `paper/sections/04_problem.tex`.

### 2.2 "bootstrap confidence interval" → Student *t*

The draft says paired differences are summarised "by their mean and a bootstrap confidence
interval obtained by resampling complete chains." The analysis uses a two-sided 95% Student
*t* interval on four degrees of freedom. Same defect the repository carried until today.

### 2.3 "16.1 million tokens" is a superseded projection

The draft states total optimizer consumption is "matched at 16.1 million tokens." That is
P-005's pre-execution projection. The **measured** value is **16,678,912** — 3.6% higher —
and P-009 reclassified the figure as a projection rather than a spendable budget precisely
because no policy choice can reach it. Use the measured number.

### 2.4 The config comment points at the superseded grid

```
% Current source: configs/experiment/primary_pilot.json, frozen 2026-08-18.
```

That grid was **rejected by its own fairness check** on both axes (F-020, F-021) and ten of
its chains certify invalid. The executed configuration is
`configs/experiment/primary_pilot_v2.json`, and the run is `primary_pilot_v2_2026-08-20`.

### 2.5 Two mandatory pairings are absent

From `docs/evidence/claim_evidence_matrix.md`, both required wherever the claim appears:

- **Any timing claim** carries the confirmatory-outcome disagreement, or is explicitly scoped
  to the primary outcome. "Timing does not matter" unqualified is false.
- **Any statement of the null** carries the three unimplemented comparators. Without them it
  reads as "nothing beats selection-only", which this run cannot support.

### 2.6 Seven references is thin, and the checklist demands they be verified

The repository's `references.bib` carries 31 entries, all cited, none missing. The draft's
seven are a subset. Beyond breadth, the Algoverse checklist item 1 requires each citation be
opened and confirmed — author list, year, venue, and that the paper says what is claimed.
That has not been done for either manuscript and is a genuine outstanding task.

---

## 3. Against the Algoverse checklist

| Item | State |
|---|---|
| 1. Citations real | **Not verified.** No DOI/arXiv resolution check has been run on either manuscript. Outstanding for both |
| 2. Overview diagram | Repository has a pipeline figure, in the appendix, not as Figure 1. Overleaf draft has **none**. Neither satisfies "a reader understands the core idea from diagram + caption alone" as a Figure 1 |
| 3. Numbers consistent | Repository: enforced — prose cites macros and a bare decimal fails a test. Overleaf: nothing enforces it |
| 4. AI sanity pass | This document is part of one. F-027 and F-028 came out of it |
| 5. Claims map to evidence | Repository: `docs/evidence/claim_evidence_matrix.md`, audited 2026-08-20. Overleaf: no equivalent |
| 6. Baselines fair | Both axes matched and measured; three of seven predeclared comparators unimplemented and stated as a limitation |
| 7. Tables/figures self-contained | Repository: table and figure now referenced in text, captions carry the takeaway. Overleaf: placeholders |
| 8. Notation consistent | §4's estimand was inconsistent with the implementation until today (F-027) |
| 9. Anonymisation | Repository is anonymous. **Overleaf carries a named author** — must be removed for a double-blind venue |
| 10. Venue compliance | **Neither uses a venue template.** Both are `\documentclass{article}`. Main text measures ~13.5 pages against NeurIPS's 9-page limit, and the NeurIPS style is *narrower* than 1-inch margins, so the real figure is likely worse |
| 11. Final mechanics | Repository builds clean: 0 errors, 0 undefined refs, 0 overfull boxes, no remaining placeholders. Overleaf has placeholders throughout |

**The two hard blockers for either manuscript are item 10 (length and template) and item 1
(citation verification).** Neither is resolvable without a decision from you: the first needs
the target venue's style file, the second needs someone to open 31 links.
