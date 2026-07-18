# Week 3 — Primary Experiments and Artifact Freeze

**Dates:** August 1–7
**Base tag:** `week-2-freeze-2026-07-31`
**Integration branch:** `integration/week-3-aug01-aug07`
**Results tag:** `week-3-results-freeze-2026-08-07`

## Shared outcome

Complete all feasible frozen primary chains, validate artifacts under objective rules, and freeze one immutable chain-level dataset. Each member works from the July 31 snapshot rather than another Week 3 branch.

## Ronit — `week-3/ronit-paper-review`

Tasks:

- Bring result-independent prose, references, diagrams, and limitations to submission quality.
- Write precommitted interpretation templates for favorable, null, harmful, and uncertain outcomes.
- Obtain one clarity and one significance review.
- Audit every claim against the frozen protocol and novelty record.
- Prepare final presentation layout and repository explanation.

Complete deliverable: submission-quality paper/presentation that can incorporate any honest outcome.

No current-week dependency: uses July 31 paper/method snapshot and pending generated files.

## Khantushig — `week-3/khantushig-reference-runs`

Tasks:

- Operate no-rescue and fresh-random conditions using the frozen seed order.
- Complete the clean positive-control verification.
- Preserve configs, manifests, allocations, metrics, checkpoints, logs, and failures.
- Record generation/training/evaluation compute and storage separately.
- Resume objective infrastructure failures only under the frozen rule.
- Produce runner integrity and actual-compute reports.

Complete deliverable: immutable reference/random chains and clean positive-control package.

No current-week dependency: uses July 31 frozen data, evaluator, policy, and runner.

## Neil — `week-3/neil-validity-audit`

Tasks:

- Complete adversarial tests for exact/near duplicates, prompt/test and candidate/test overlap.
- Test padding, repetition, incomplete batches, gradient accumulation, resume, corrupt hashes, and incomplete provenance.
- Test evaluator determinism and tail reliability against saved fixtures/checkpoints.
- Build one command that returns `valid`, `invalid`, or `valid_with_limitation` for any run.
- Prepare data/evaluation appendix and validity-certificate template.
- At Friday freeze, apply the finished validator to available frozen artifacts.

Complete deliverable: independent run-audit system and classifications for the freeze.

No current-week dependency: validator development uses adversarial fixtures; only the final batch invocation reads completed artifacts.

## Aarav — `week-3/aarav-policy-runs`

Tasks:

- Operate schedule-only, selection-only, and joint conditions independently using frozen seeds/configs.
- Verify preflight budget equality for each chain.
- Retain generation-wise mode states, scores, selections, and allocation history.
- Generate provisional aggregates only from schema-valid completed chains.
- Run monitoring-bias stress test only after primary jobs are secure.
- Produce policy-behavior report without changing frozen hyperparameters.

Complete deliverable: immutable three-policy chain artifacts and provisional machine-generated analysis.

No current-week dependency: uses July 31 frozen runner/data/evaluator; does not wait for Khantushig's jobs.

## August 7 freeze procedure

1. Stop adding primary seeds at the declared time.
2. Hash every completed artifact.
3. Run Neil's validator.
4. Preserve all failed/incomplete chains.
5. Apply only frozen exclusions/replacement rules.
6. Generate and hash the immutable chain-level aggregate.
7. Label later work exploratory.
8. Tag `week-3-results-freeze-2026-08-07`.
