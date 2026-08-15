# Hostile Novelty Review

## Status

`PENDING_EXTERNAL_REVIEW`

This file is deliberately not marked complete. The literature audit and reviewer packet are ready, but Week 2 requires a technically qualified person outside the writing team. An AI-generated or team-authored criticism is not represented as that review.

## External reviewer record

| Field | Required entry |
|---|---|
| Reviewer name | `PENDING_EXTERNAL_REVIEWER` |
| Expertise | `PENDING` - should include recursive training, synthetic-data curation, data-mixture optimization, or a closely related ML area |
| Affiliation/role | `PENDING` |
| Independence | Reviewer must be outside the paper-writing team and disclose any project involvement |
| Review date | `PENDING` |
| Review medium | `PENDING` - annotated document, email, or recorded meeting notes |

## Materials supplied to the reviewer

1. **Exact research question:** Under fixed lifetime human-origin optimizer-token and total optimizer-token budgets, does joint allocation across recursive generation and monitored human-distribution mode improve chain-level retention relative to the strongest matched schedule-only and selection-only policies?
2. The provisional contribution paragraph and claim ledger in `CLAIMS.md`.
3. The complete closest-work table in `docs/evidence/closest_work.csv`.
4. The primary-source registry in `docs/evidence/sources.yaml`.
5. The formal problem and result-free method in `paper/sections/04_problem.tex` and `paper/sections/05_method.tex`.
6. The five strongest original threats plus the two 2026 threats added on August 2.

## Five strongest papers to challenge first

| Paper | Why it threatens the claim |
|---|---|
| Alemohammad et al. (2024), *Self-Consuming Generative Models Go MAD* | Combines recursive training, fresh-real schedules, and biased sampling. |
| Zhao et al. (2026), *RegMix-D* | Optimizes time-varying domain mixtures. |
| Wang et al. (2026), *TiKMiX* | Periodically reallocates training data across time and domains. |
| Luo et al. (2026), *KITE* | Targets diagnosed weaknesses and semantic boundaries under equal per-iteration labeling budgets. |
| Qiao et al. (2026), *When Sample Selection Bias Precipitates Model Collapse* | Shows fragmented monitoring references make recursive selection erase diversity and minority modes. |

## Backward/forward audit log

| Date | Seed/threat | Primary-source action | Disposition |
|---|---|---|---|
| 2026-08-02 | Recursive collapse and fresh-real work | Rechecked the primary-paper families cited by Shumailov, Alemohammad, Gerstgrasser, Kazdan, and Drayson and searched 2025-2026 citing/related work for recursive selection, human/real mixing, verification, and tail preservation. | Existing registry retained; no source found with the complete five-part qualifier. |
| 2026-08-02 | Dynamic mixture work | Rechecked the primary methods and bibliographies around DoReMi, RegMix, Data Mixing Laws, RegMix-D, and TiKMiX for schedules that jointly vary time and domain. | These works own broad time-by-domain allocation language; novelty wording remains context- and accounting-specific. |
| 2026-08-02 | Luo et al., arXiv:2607.17043v1 | Opened the original paper; reviewed Sections 3.1-3.3, 4.1, Appendix 8.2.4, and 8.4 for iterative weakness targeting, semantic curation, and equal labeling-budget comparisons. | Added as a high threat; not a lifetime human-origin optimizer-token allocation method. |
| 2026-08-02 | Qiao et al., arXiv:2606.13732v1 | Opened the original paper; reviewed Section 3.1/Theorems 1-3, Sections 4.3-4.4, Section 6, and Appendix C.5/Table 3 for biased references, selection budgets, and minority-mode loss. | Added as the strongest threat to the monitoring-omission contribution; does not allocate human rescue tokens over time. |

Search services are discovery aids only. `reviewed_primary` was assigned only after opening the original paper and recording an exact section, theorem, table, figure, or appendix location in `sources.yaml`.

## Questions the external reviewer must answer

1. Which existing paper most directly owns the proposed contribution?
2. Is there already a method that jointly optimizes timing and mode/domain targeting inside a recursive self-generated training chain?
3. Does any source allocate one fixed **lifetime** stock of human-origin optimizer-consumed tokens rather than a per-generation ratio, sample count, or verifier budget?
4. Are the schedule-only and selection-only matched baselines a meaningful decomposition or merely an artificial framing?
5. Which sentence in `CLAIMS.md`, the abstract, introduction, related work, or conclusion most overstates novelty?
6. What missing paper, theorem, experiment, or terminology should be added?
7. Should C-004 survive, be narrowed, or be withdrawn?

## Internal pre-review: strongest criticism already identified

**Not an external-review result.** The strongest current criticism is that the project may be combining known ingredients and treating exact accounting plus a baseline decomposition as a novel method. Dynamic mixture work already couples time and domain; KITE couples iterative weakness diagnosis with budget-matched curation; Qiao et al. already establish the monitoring-reference failure. The remaining distinction may be useful experimental bookkeeping rather than a publishable algorithmic contribution.

## Team response before external review

The manuscript no longer claims that time-and-mode allocation, targeted recursive curation, or monitoring bias is new in general. C-004 is restricted to the conjunction of (1) recursion, (2) one fixed lifetime human-origin optimizer-token stock, (3) allocation across generation, (4) allocation across monitored human modes, and (5) matched schedule-only and selection-only baselines. Experimental value must be shown separately from novelty. If an external reviewer identifies a primary source matching those qualifiers, C-004 will be withdrawn before method implementation proceeds.

## Wording changes already made

- Replaced broad “joint time-and-mode allocation” novelty language with the full five-part qualifier.
- Added KITE as a high-threat weakness-targeting and budget-aware curation analogue.
- Added Qiao et al. as prior ownership of the fragmented-monitoring selection hazard.
- Recast the monitoring-omission experiment as a transfer/falsification test rather than discovery of monitoring bias.
- Added explicit favorable, equivalent, harmful, uncertain, and invalidity language.

## External reviewer findings

Complete these fields without deleting the pending history.

- **Strongest criticism:** `PENDING_EXTERNAL_REVIEW`
- **Closest paper named:** `PENDING_EXTERNAL_REVIEW`
- **Reviewer disposition of C-004:** `PENDING_EXTERNAL_REVIEW`
- **Team response:** `PENDING_EXTERNAL_REVIEW`
- **Exact wording changed after review:** `PENDING_EXTERNAL_REVIEW`
- **Unresolved questions:** `PENDING_EXTERNAL_REVIEW`
- **Evidence attachment or link:** `PENDING_EXTERNAL_REVIEW`

## Completion rule

Ronit's Week 2 novelty-review gate remains open until the external reviewer fields are completed, the response is dated, any required source is audited from the primary paper, and all affected manuscript language is updated. A negative review is preserved as evidence and is not relabeled as approval.
