# Team, Roles, and Ownership

## Role 1 — Ronit

**Title:** Research and submission lead

Owns:

- `paper/`
- `docs/evidence/`
- `CLAIMS.md`
- `DECISIONS.md`

Responsible for:

- hostile closest-work and novelty review;
- claim wording and evidence links;
- manuscript and bibliography;
- presentation/poster;
- final submission packaging;
- ensuring results are never overstated.

Permanent mock inputs: placeholder LaTeX tables and figures marked `RESULT_PENDING`.

## Role 2 — Khantushig

**Title:** Training and experiment-infrastructure lead

Owns:

- `src/human_data_budget/training/`
- `src/human_data_budget/generation/`
- `src/human_data_budget/runner/`
- `configs/training/`
- `configs/generation/`

Responsible for:

- official positive-control reproduction;
- training and generation loops;
- chain orchestration;
- checkpoint/resume behavior;
- seed propagation;
- run manifests and compute accounting;
- operating reference/random experiment jobs.

Permanent mock inputs: toy corpus, uniform policy, and null evaluator.

## Role 3 — Neil

**Title:** Data, evaluation, and validity lead

Owns:

- `src/human_data_budget/data/`
- `src/human_data_budget/evaluation/`
- `data/`
- `tests/data/`
- `configs/data/`
- `configs/evaluation/`

Responsible for:

- dataset and license audit;
- stable IDs, hashes, and disjoint partitions;
- provenance and optimizer-token accounting;
- held-out human NLL and tail-retention evaluation;
- leakage, memorization, and artifact validation;
- final per-run validity certificate.

Permanent mock inputs: toy examples, saved fake logits, deliberately corrupted manifests, and fake checkpoints.

## Role 4 — Aarav

**Title:** Method, baselines, and statistics lead

Owns:

- `src/human_data_budget/policies/`
- `src/human_data_budget/analysis/`
- `configs/policy/`
- `PREREGISTRATION.md`
- generated `results/aggregates/` and `results/figures/`

Responsible for:

- formal problem and proposed joint policy;
- random, schedule-only, and selection-only baselines;
- paired seed list and frozen primary contrast;
- chain-level AUC and uncertainty analysis;
- power simulation;
- script-generated tables and figures;
- operating the schedule/selection/joint experiment jobs.

Permanent mock inputs: simulated mode states and fake schema-valid chain results.

## Shared interface ownership

The following require an interface-change issue and at least one affected owner review:

- `schemas/`
- `docs/interfaces/`
- `configs/experiment/`
- `PROTOCOL.md`
- primary outcome or exclusion definitions.

## Independence rule

Within a week, nobody may require code, data, results, or approval from another person's current weekly branch to complete their deliverable. Each person works from the frozen beginning-of-week tag and their permanent fixtures. Integration occurs only at the scheduled weekly gate.
