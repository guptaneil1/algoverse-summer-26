# Gated Research Roadmap

> **Deadline note (July 18, 2026):** The operational August 15 plan is in
> [`docs/ROADMAP.md`](docs/ROADMAP.md). This file retains the broader future
> evidence path. The August pilot does not satisfy the later multi-scale gates.

This is a go/no-go roadmap. A later stage may not begin because a date arrived; it begins only when the preceding gate passes.

## Stage 0 — Repository truth and decision freeze

### Deliverables

- Truthful design-only README.
- Claim ledger and primary-source registry.
- Research protocol and draft preregistration.
- Decision, compute, and failure logs.
- Written list of allowed and prohibited novelty claims.

### Pass condition

Every statement about implementation or results matches an artifact that exists. No result is claimed.

## Stage 1 — Novelty kill review

### Deliverables

- Closest-work matrix covering fresh human mixing, accumulation, verification, high-surprise selection, schedule allocation, semantic sampling, and biased selection.
- Backward- and forward-citation search for every close paper.
- Contradiction search targeted at finite lifetime human budgets and joint time-by-mode allocation.
- One-page contribution specification reviewed by the project mentor and at least one additional researcher who did not originate the idea.

### Pass condition

No discovered paper already owns the exact joint problem, and the reviewers agree that a clearly distinguishable claim remains.

### Stop condition

If closer work already jointly allocates a finite lifetime human-data budget across recursive time and human-distribution modes, pivot before writing novel-method code.

## Stage 2 — Published positive-control reproduction

### Deliverables

- Pinned commit of the official Drayson et al. code.
- Pinned dataset, model, tokenizer, environment, and configuration revisions.
- GPT-2 recursive-training reproduction through generations 0–9.
- Fully synthetic and human-mixed control arms using the official configurations.
- Expected-versus-observed report with a predeclared tolerance.
- Fresh-environment rerun.
- Exact run manifests and generated metric files.

### Pass condition

The expected treatment ordering and endpoint behavior reproduce within the predeclared criterion, and a clean rerun reaches the same scientific conclusion.

### Stop condition

No novel Human Data Budget experiment begins if the positive control cannot be reproduced after documented debugging.

## Stage 3 — Pipeline correctness

### Required tests

- Stable content hashes and example identifiers.
- Disjoint candidate, prompt, validation, and test partitions.
- Exact training-token and human-token accounting.
- Seed propagation through data, generation, training, and evaluation.
- Resume equivalence from a saved checkpoint.
- Provenance retention after shuffling and batching.
- No prompt/evaluation leakage.
- Script-generated table and figure hashes.

### Pass condition

All blocking tests pass in a clean environment. Failed tests produce no paper-facing results.

## Stage 4 — 160M mechanism and variance pilot

### Design

- Model: Pythia-160M or another frozen screening model selected before results.
- Primary domain: one licensed domain.
- Horizon: ten recursive generations.
- Initial seeds: at least five paired independent chains for variance estimation; final seed count is not assumed.
- Budget levels: zero plus two nonzero lifetime budgets frozen before treatment results are examined.
- Policies: no rescue, fresh random rescue, strongest schedule-only baseline, strongest selection-only baseline, joint policy, and oracle upper bound.
- Primary outcomes: held-out human negative log-likelihood and a frozen tail-retention measure.

### Deliverables

- Chain-level raw outcomes.
- Mechanism measurements by human-distribution mode.
- Monitor-bias stress test.
- Simulation-based power analysis.
- Compute forecast for the powered study.
- Written scale, pivot, or stop decision.

### Pass condition

The joint policy exceeds the strongest non-joint baseline by the frozen smallest meaningful effect, the uncertainty is compatible with a feasible powered study, and the mechanism prediction is supported.

## Stage 5 — Powered core study

Begin only after Stage 4 passes.

### Expected scope

- At least two domains.
- 410M- and 1B-class core scales.
- Seed count determined by the Stage 4 power simulation.
- No-rescue and matched human-only references.
- All scientifically non-dominated schedule, selection, accumulation, and fresh-mixing baselines.
- Long-horizon confirmation for the decisive contrast.

### Empirical-led scaling requirement

If the paper is primarily empirical or methodological, run a tightly scoped independent-family or 7B-class confirmation of the decisive comparison. If that is infeasible, narrow the claim or pursue a theory-led contribution.

## Stage 6 — Paper and independent audit

### Deliverables

- All headline figures regenerated from immutable artifacts.
- Completed NeurIPS checklist draft.
- Claim-to-evidence audit of every abstract and introduction sentence.
- Three independent mock reviews: topic expert, statistics/experimental-design reviewer, and uninvolved ML reader.
- Reproduction of the headline table by someone who did not write the analysis.

### Submission gate

- No mock-review score below 3/4 on quality, clarity, significance, or originality.
- No unresolved fatal novelty or correctness objection.
- No missing experiment that directly tests the headline claim.
- The paper's contribution can be summarized correctly after one reading.

## Permanent stop/pivot rules

Pivot or narrow the work when any of the following occurs:

- closer work owns the central contribution;
- the published positive control cannot be reproduced;
- leakage or provenance cannot be ruled out;
- a powered design is unaffordable;
- the effect disappears against the strongest relevant baseline;
- the effect exists only at 160M and no major theorem supports broader scope;
- the policy fails under realistic monitoring bias without yielding a principled failure-boundary result.
