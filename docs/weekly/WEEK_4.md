# Week 4 — Independent Finalization and Submission

**Dates:** August 8–14
**Base tag:** `week-3-results-freeze-2026-08-07`
**Integration branch:** `integration/week-4-aug08-aug14`
**Release tag:** `submission-rc-2026-08-14`

## Shared outcome

Four final packages are independently produced from the immutable August 7 snapshot and integrated on August 14. Nobody waits for another member's Week 4 work.

## Ronit — `week-4/ronit-final-submission`

Tasks:

- Insert August 7 generated aggregates/figures through stable filenames.
- Write results, abstract, discussion, conclusion, and final limitations without exceeding evidence.
- Update claim statuses and ensure null/harmful/uncertain outcomes remain visible.
- Finalize citations, appendix references, slides/poster, submission summary, and checklist.
- Build final PDF with no unresolved `RESULT_PENDING` marker except explicitly future work.

Complete deliverable by August 13: final paper source/PDF, presentation, claim ledger, and submission package.

Independent input: August 7 frozen generated files; Week 4 analysis uses the same filenames and cannot block writing.

## Khantushig — `week-4/khantushig-reproduction-release`

Tasks:

- Test installation from a clean environment.
- Run lint, unit, contract, toy smoke, and documented reproduction commands.
- Verify checkpoint loading/resume and exact README commands.
- Finalize lockfile, configs, checksums, compute ledger, and environment report.
- Produce anonymized code archive if required.

Complete deliverable by August 13: clean reproduction/release package and report.

Independent input: August 7 repository/artifact snapshot.

## Neil — `week-4/neil-validity-certificate`

Tasks:

- Validate every primary manifest, asset hash, split, provenance record, seed, budget, and checkpoint reference.
- Independently recompute primary NLL and tail metrics from frozen outputs.
- Compare raw chain values to frozen aggregate and verify all exclusions/failures.
- Finalize data card, evaluation appendix, and per-result validity certificate.

Complete deliverable by August 13: signed-style validity report classifying each headline result.

Independent input: August 7 immutable artifact set.

## Aarav — `week-4/aarav-final-analysis`

Tasks:

- Regenerate NLL curves, regret AUC, tail retention, paired differences, intervals, and effect sizes.
- Compare joint with random, schedule-only, and selection-only under frozen contrast.
- Generate headline table, primary curve, allocation/per-mode views, and valid robustness results.
- Conduct only predeclared or clearly exploratory sensitivity analyses.
- Generate LaTeX/CSV/figures and hashes through one reproducible command.
- Finalize statistics appendix and analysis report.

Complete deliverable by August 13: `make reproduce-headline`-equivalent outputs and final analysis report.

Independent input: August 7 immutable chain-level dataset.

## August 14 integration

- Build from a clean checkout.
- Insert generated files without hand copying values.
- Cross-check paper claims against validity and reproduction reports.
- Conduct novelty, statistics, and uninvolved-reader mock reviews in parallel.
- Allow clarity, citation, formatting, packaging, and unsupported-claim-removal changes only.
- Do not add a primary seed, metric, subgroup, exclusion, budget, or redesigned method.
- Tag `submission-rc-2026-08-14`.

## August 15 submission

- Re-run CI and clean paper build.
- Verify no secrets/large assets are committed.
- Verify every headline value traces to artifacts.
- Create `submission-final-2026-08-15` and submit before the final hours.
