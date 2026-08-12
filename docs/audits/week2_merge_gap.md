# Week 2 is done and pushed, but unmerged and untagged

**Audited:** 2026-08-12, from `claude/week-3-assignments-boq852`
**Author:** Khantushig (runner/training workstream)
**Status:** report only — no branch was merged, tagged, rebased, or rewritten

This file exists because `docs/STATUS.md` on `main` contradicts work that is
already pushed to this repository. It records what is where. Acting on it is the
integrator's call, not this branch's.

## 1. The gap

Every Week 2 branch exists on `origin` and none is an ancestor of `main`:

| Branch | Commits ahead of `main` | Head |
|---|---:|---|
| `week-2/khantushig-positive-control` | 44 | `8662af6` |
| `week-2/neil-frozen-data-metrics` | 52 | `cd73d39` |
| `week-2/aarav-method-preregistration` | 3 | `7966678` |
| `week-2/ronit-paper-novelty` | 1 | `7410e8c` |
| `integration/week-2-jul25-jul31` | 51 | `99e563b` |

`main` is at `c2aa23e`. `git ls-remote --tags origin` returns **zero tags**, so
`week-1-freeze-2026-07-24` and `week-2-freeze-2026-07-31` do not exist.

The Week 3 packet's start gate — *"do not begin a primary Week 3 chain until
accepted Week 2 work is merged, `main` points to the tested Week 2 snapshot, and
tag `week-2-freeze-2026-07-31` exists"* — is therefore unsatisfiable as written,
not because the work is missing but because it was never integrated.

## 2. What `main` is missing from the runner workstream

Present on `week-2/khantushig-positive-control`, absent from `main`:

| Path | Size | What it is |
|---|---:|---|
| `src/human_data_budget/runner/positive_control_adapter.py` | 699 lines | Translates upstream artifacts into the frozen runner contracts |
| `scripts/run_positive_control_arm.py` | 422 lines | Advances one arm one generation at a time, resumable across sessions |
| `docs/benchmarks/kaggle_smoke_test_runbook.md` | 933 lines | The full Kaggle execution procedure |
| `docs/positive_control/report.md` | 234 lines | Reproduction report |
| `docs/positive_control/expected_vs_observed.md` | 409 lines | Frozen-vs-observed ledger, including the published-value comparison |
| `docs/positive_control/measurements/` | 11 generations × 2 arms | Per-generation `eval_results.json`, `train_results.json`, `artifact_record.json` |
| `configs/experiment/positive_control_{fully_synthetic,human_mixed}.json` | 88 lines each | The executed configs, with pinned revisions |
| `tests/runner/test_positive_control_{contract,driver}.py`, `test_real_checkpoint_resume.py`, `test_reproduction_command.py` | 1133 lines | Tests for all of the above |

The branches have also diverged rather than simply advanced: `main` carries
`src/human_data_budget/validation/` (the validator, 41 adversarial tests), which is
**not** on `integration/week-2-jul25-jul31`. Neither branch is a superset of the
other, so integration is a real merge, not a fast-forward.

## 3. `docs/STATUS.md` on `main` is wrong about the positive control

`main` records:

> | Positive control | Khantushig | Not reproduced | Protocol only | Environment and compute benchmark; upstream commit still unpinned |

All three of those statements are contradicted by the Week 2 branch:

- **"Not reproduced"** — both arms ran to 11 generations. Fully synthetic (α=0) went
  from perplexity 29.6179 to 50.9806, a degradation ratio of 1.7213; human-mixed
  (α=1) went from the same baseline to 30.3730, a ratio of 1.0255. All four frozen
  ordering claims hold. `docs/positive_control/report.md` classifies the result
  `valid_with_limitation`.
- **"Protocol only"** — `docs/positive_control/measurements/` holds per-generation
  train and eval outputs for both arms.
- **"upstream commit still unpinned"** — `resolved_identifiers.json` pins gpt2
  (`607a30d7…`), the detector (`08f218f1…`), wikitext (`b08601e0…`), and the
  prepared train file (`77557c85…`). The upstream repository is pinned at
  `GeorgeDrayson/model_collapse@feb85114…`.

The limitations that keep it at `valid_with_limitation` are recorded on that branch
and are not restated here.

## 4. What this branch did not do

No merge, no tag, no cherry-pick, no rebase, no force-push, and no restatement of
Week 2 measurements as if they were produced here. The numbers in §3 are quoted to
show the contradiction, and their authoritative home stays
`week-2/khantushig-positive-control`.

## 5. What somebody has to decide

1. **Whether Week 2 is accepted.** If yes, integrate the four branches (a real
   merge — see §2) and tag the result. If no, say so in `docs/STATUS.md`.
2. **Which commit `week-2-freeze-2026-07-31` names.** Nothing can reference the
   freeze until it exists.
3. **Whether `docs/STATUS.md` is corrected before or after that merge.** It is
   currently the repository's designated ground truth and is wrong about a
   completed reproduction, which is the more damaging direction of error: it
   understates evidence that exists.

Until (1) and (2) are resolved there is no frozen design to execute, and every
`AWAITING_JULY_31_FREEZE` config keeps having no legitimate source for its values.
