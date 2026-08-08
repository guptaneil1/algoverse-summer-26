# Outcome-Contingent Language

Use this file only after manifest validation and generated analysis. Replace bracketed fields with artifact-derived values; never select wording based on rhetorical preference.

## Universal preconditions

No efficacy sentence is allowed unless the positive-control gate is resolved, the protocol and preregistration are frozen, five partitions are disjoint, compared policies match lifetime human and total optimizer tokens, required artifacts and hashes exist, and the analysis is regenerated from complete chain results. Novelty wording additionally requires the external hostile review.

## Favorable joint-policy result

**Allowed:** “Under the frozen [domain], [model], [horizon], and lifetime budget, the joint policy improved [primary outcome] relative to the strongest eligible non-joint baseline by [artifact-derived estimate and interval]. The result supports joint allocation in this tested setting.”

**Required qualifiers:** name the selected baseline; report chain count and interval; state whether the tail metric agrees; report monitoring-omission behavior; avoid “prevents model collapse,” “optimal,” “first,” and universal claims.

## Practical tie or simpler-baseline win

Use only when the valid paired interval lies inside the preregistered equivalence region.

**Allowed:** “The joint policy did not provide a practically meaningful advantage over [baseline] under matched budgets. The simpler policy is therefore preferred for this tested setting.”

Do not infer equivalence from a large p-value or wide interval.

## Harmful joint-policy result

**Allowed:** “Joint adaptation worsened [outcome/stability criterion] relative to [baseline] under the frozen protocol. The proposed allocation rule is not supported in this setting.”

State whether harm arises in the main monitor, omission condition, training stability, tail outcome, or multiple endpoints. Preserve failed/divergent chains under the preregistered rule.

## Inconclusive result

**Allowed:** “The paired interval spans [beneficial/equivalent/harmful] regions, so the experiment does not distinguish the prespecified conclusions. More independent chains or a narrower scope are required.”

Do not use “no effect,” “same,” or “works similarly” when uncertainty is wide.

## Monitoring-omission boundary

- **Boundary detected:** “When the preregistered mode was hidden from the monitor, targeted allocation lost benefit or caused harm on untouched full-distribution evaluation. This supports monitor dependence as a failure boundary in the tested setting.”
- **No boundary detected:** “This omission intervention did not detect the prespecified failure boundary. The result does not establish robustness to other missing, merged, noisy, or adversarial modes.”
- **Uncertain:** “The omission contrast is too imprecise to determine whether monitoring misspecification changes the policy effect.”

Credit Qiao et al. (2026) for already establishing biased-reference selection hazards in recursive synthetic-data settings; do not claim discovery of the general phenomenon.

## Positive-control failure

**Allowed:** “The published positive-control comparison did not satisfy the frozen reproduction criterion because [artifact-backed reason]. Novel-treatment outcomes are not interpreted as validated evidence.”

Classify the failure as infrastructure, implementation, protocol deviation, or scientific mismatch. Do not relabel a failed reproduction as a partial pass.

## Budget mismatch or accounting failure

**Allowed:** “The comparison is invalid because [human/total] optimizer-token budgets were not matched under the frozen accounting rule. No allocation-efficiency conclusion is drawn.”

## Leakage or split-integrity failure

**Allowed:** “The affected analysis is invalid because final-test or prohibited overlapping data influenced [component]. A new untouched test partition and rerun are required.”

## Artifact or reproducibility failure

**Allowed:** “The result is not reportable because [manifest/hash/checkpoint/analysis] provenance is incomplete or inconsistent.”

## Novelty failure

**Allowed:** “The external review identified [paper] as owning the proposed novelty. We withdraw the first-of-kind contribution and position the work as [replication/transfer/controlled comparison].”

A favorable experiment does not override a failed novelty claim.
