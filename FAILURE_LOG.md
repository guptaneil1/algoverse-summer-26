# Failure Log

> No primary experimental chain has been attempted in this repository. The entries
> below are implementation and protocol defects found in the pipeline itself.

Failures, null results, contradictory evidence, and protocol violations must be retained. They may not be deleted because they weaken the preferred conclusion.

## Entries

| ID | Date | Stage | Run/claim | Failure | Evidence | Cause status | Resolution | Scientific consequence |
|---|---|---|---|---|---|---|---|---|
| F-001 | 2026-08-12 | Pipeline | Toy smoke chain `fixture_joint_seed1` | `run_manifest.json` emitted no `data.partitions` block, so every chain classified `invalid` with `SEPARATION_MISSING_PROVENANCE` — 14 checks passing and the run still uncertifiable | `scripts/validate_run.py runs/fixture_joint_seed1` → `invalid`, exit 2, `checks_failed: ["separation_partitions_recorded"]` | Implementation defect (`runner/manifest.py:54` copied the config `data` block, which carries no partitions) | Fixed on `claude/week-3-assignments-boq852`: `build_partitions` resolves provenance from a declared source; validator now returns `valid`, exit 0, 20 checks. Pinned by `tests/runner/test_validate_toy_chain.py` | None to any result — no primary chain had run. Had it not been found first, every primary chain would have been uncertifiable and the accelerator time unrecoverable, since provenance cannot be back-filled after a run |
| F-002 | 2026-08-12 | Pipeline | Partition vocabulary contract | `validation/audit.py` and `data/manifest.py` disagree on 3 of 5 partition names and 2 of 4 provenance fields | `validation/audit.py:29-37` (`base_human_train`/`generation_prompts`/`final_human_test`, `stable_id`/`source_dataset`) vs `data/manifest.py:12-19` (`base_train`/`prompts`/`test`, `example_id`/`source`) | Protocol/interface defect, both modules @Neil-owned | **Open.** Runner translates in `_DATA_MODULE_PARTITIONS`; contract recorded in `schemas/run_manifest.schema.json` and `docs/interfaces/run_manifest.md`. Not fixed at source — cross-owner edit needs @Neil | A rename on either side breaks the translation silently. No result affected yet |
| F-003 | 2026-08-12 | Process | Week 2 integration | Week 2 work is pushed but unmerged and untagged; `docs/STATUS.md` on `main` states the positive control is "Not reproduced" when it was reproduced | `git ls-remote --tags origin` → 0 tags; `week-2/khantushig-positive-control` 44 commits ahead of `main` and not an ancestor; `docs/positive_control/report.md` on that branch | Protocol/process, not implementation | **Open** — integrator decision. Reported in `docs/audits/week2_merge_gap.md`; no branch merged, tagged, or rewritten | The packet's Week 3 start gate is unsatisfiable as written, and the repository's designated ground-truth file understates evidence that exists |

## Entry rules

For every failure, record:

- exact run or claim identifier;
- code and configuration commit;
- manifest and log location;
- whether the cause is implementation, infrastructure, protocol, or scientific;
- evidence supporting that classification;
- whether rerunning is allowed under the frozen rules;
- effect on claims and future stages.

An unfavorable treatment result is not an implementation failure without independent evidence of a defect.
