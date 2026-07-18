# Experiment Runbook

## Before launching

1. Confirm the run has an approved experiment issue.
2. Confirm the code commit is frozen and the working tree is clean.
3. Confirm all configs and manifests validate.
4. Confirm the ordered seed is allowed.
5. Confirm expected compute/storage and artifact destination.
6. Generate the run manifest with status `planned`.
7. Run budget and leakage preflight checks.

## During a run

- Never edit the active config.
- Preserve stdout/stderr and tracker ID.
- Save atomic generation checkpoints.
- Update manifest state without overwriting history.
- Record generation/training/evaluation timings separately.
- Do not inspect final test results for tuning.

## Failure handling

Classify only with evidence:

- infrastructure failure;
- implementation defect;
- data/protocol violation;
- scientific divergence/unfavorable result.

Record the exact run, commit, manifest, evidence, rerun permission, replacement seed rule, and consequence in `FAILURE_LOG.md`. An unfavorable result is not an implementation defect by default.

## Completion

1. Verify every planned generation completed.
2. Hash artifacts.
3. Produce `chain_result.json`.
4. Run the independent validator.
5. Mark `valid`, `invalid`, or `valid_with_limitation`.
6. Copy only small generated aggregates into Git.
7. Add actual compute to `COMPUTE.md`.

## Results freeze

At August 7 freeze:

- stop adding primary seeds;
- retain every completed/failed chain;
- validate manifests and budgets;
- record exclusions under frozen rules;
- create the immutable chain-level aggregate;
- tag the repository;
- label later work exploratory.
