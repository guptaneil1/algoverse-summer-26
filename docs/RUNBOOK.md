# Experiment Runbook

## Before launching

1. Confirm the run has an approved experiment issue.
2. Confirm the code commit is frozen and the working tree is clean.
3. Confirm all configs and manifests validate.
4. Confirm the ordered seed is allowed.
5. Confirm expected compute/storage and artifact destination — see the forecast
   and assumptions A1–A7 in `COMPUTE.md`, and fix the checkpoint retention policy
   before launch, because it constrains which resume tests remain possible.
6. Generate the run manifest with status `planned`.
7. Run budget and leakage preflight checks:

   ```bash
   make preflight CONFIGS="configs/experiment/*.json"
   ```

   This checks budget arithmetic, that the candidate pool can actually fund the
   per-generation budget, that the pool spans at least two modes, that no config
   still carries a `TBD` placeholder, and — with `--compare` — that every policy
   in the comparison declares identical lifetime human and total optimizer
   budgets. It exits non-zero on any failure, before compute is spent.

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
2. Hash artifacts. Checkpoints carry a `.sha256` sidecar written by
   `runner/checkpoint.py`; verify with `verify_checkpoint` before trusting a
   resume, since a corrupt checkpoint can still parse as valid JSON.
3. Produce `chain_result.json`.
4. Run the independent validator:

   ```bash
   make validate RUN=runs/<run_id>
   ```

   Or in batch, which exits with the worst state observed:

   ```bash
   python scripts/validate_run.py runs/* --json > results/certificates/batch_verdicts.json
   ```

5. Mark `valid`, `invalid`, or `valid_with_limitation` — exit codes 0, 1, and 2
   respectively. Issue a certificate per headline result using
   `docs/VALIDITY_CERTIFICATE_TEMPLATE.md`; it must be issued by someone who did
   not operate the run.
6. Copy only small generated aggregates into Git. `.gitignore` already tracks
   `results/aggregates/*.json`, `results/figures/*.png`, `results/tables/*.tex`,
   `results/csv/*.csv`, and `results/ARTIFACT_MANIFEST.json`, while keeping raw
   `runs/` output out. Export analysis-ready CSV with `scripts/export_csv.py`.
7. Add actual compute to `COMPUTE.md`, in the **Actual usage** table — never by
   editing the forecast rows, which must remain visible as forecasts.

## Results freeze

At August 7 freeze:

- stop adding primary seeds;
- retain every completed/failed chain;
- validate manifests and budgets;
- record exclusions under frozen rules;
- create the immutable chain-level aggregate;
- tag the repository;
- label later work exploratory.
