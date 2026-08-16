# Week 2 is integrated but not promoted, and one commit is missing

**Audited:** 2026-08-12, from `week-3/khantushig-reference-runs`
**Author:** Khantushig (runner/training workstream)
**Status:** report only — no branch was merged, tagged, rebased, or rewritten

> **Correction.** An earlier version of this file claimed Week 2 was "pushed but
> unmerged". That was wrong: it checked only whether the Week 2 branches were
> ancestors of `main`, and reported the answer as if it covered integration in
> general. Week 2 **was** integrated, on the integration branch. The corrected
> position is below.

## 1. What actually happened

Three of the four Week 2 branches were merged into
`integration/week-2-jul25-jul31` by pull request:

| PR | Branch | State |
|---|---|---|
| #15 | `week-2/ronit-paper-novelty` | merged into integration |
| #16 | `week-2/khantushig-positive-control` | merged into integration |
| #17 | `week-2/aarav-method-preregistration` | merged into integration |
| — | `week-2/neil-frozen-data-metrics` | **not merged — 1 commit outstanding** |

So the Week 2 integration branch exists and carries the positive control, the
preregistration, and the paper work.

## 2. The three gaps

**2.1 Neil's freeze commit is not in the integration branch.** One commit,
`cd73d39` — *"feat(neil/week-2): freeze WikiText-103 manifests, mode definition,
and tail-retention metric"*. It is not a trivial follow-up; it is the data freeze:

| Path | What it carries |
|---|---|
| `configs/data/wikitext103.json` | `status: frozen`, `mode_definition: article_length_quantile`, `partition_strategy: stable_id_hash_modulo` |
| `scripts/build_wikitext103_manifests.py` | 363 lines — builds the five partition manifests |
| `configs/evaluation/primary.json` | frozen evaluator settings |
| `docs/evaluation/tail_retention_freeze.md` | the frozen primary tail metric |
| `docs/data/overlap_report.md`, `mode_definition_audit.md`, `week2_audit_report.md` | the audits behind the freeze |
| `src/human_data_budget/data/manifest.py` | accepts text-free frozen records with precomputed `content_hash`, and rejects a hash that disagrees with its text |
| `tests/data/test_manifest.py`, `test_token_accounting.py` | 167 lines of tests for the above |

**This is the blocker for the reference chains.** No-rescue and fresh-random
consume the five frozen partition manifests; without this commit there is no
frozen data to consume.

Note the manifests themselves are **generated, not committed** —
`data/manifests/` holds only a README, and `configs/data/wikitext103.json` points
`manifest_hashes` at `data/manifests/MANIFEST_HASHES.json`, which is produced by
the build script. Merging the commit is necessary but not sufficient; the script
must then run.

**2.2 The integration branch was never promoted to `main`.** `main` is at
`c2aa23e`, whose merge history runs Week 1 (PRs #8–#13), dependabot, `#20
shared/claude-code-setup`, `#21 shared/week3-result-independent`. No Week 2 PR
appears. `positive_control_adapter.py` and `docs/positive_control/report.md` are
absent from `main`.

**2.3 The repository has zero tags.** `git ls-remote --tags origin` returns
nothing, so neither `week-1-freeze-2026-07-24` nor `week-2-freeze-2026-07-31`
names a commit. Every document referencing the July 31 freeze — including the
`AWAITING_JULY_31_FREEZE` configs — points at something that does not exist as a
git object.

## 3. `docs/STATUS.md` on `main` is stale about the positive control

`main` records:

> | Positive control | Khantushig | Not reproduced | Protocol only | Environment and compute benchmark; upstream commit still unpinned |

All three are contradicted by work that is merged into the integration branch:

- **"Not reproduced"** — both arms ran to 11 generations. Fully synthetic (α=0)
  29.6179 → 50.9806, ratio 1.7213; human-mixed (α=1) → 30.3730, ratio 1.0255.
  All four frozen ordering claims hold; re-verified by recomputation from raw
  artifacts in `docs/positive_control/week3_verification.md`.
- **"Protocol only"** — `docs/positive_control/measurements/` holds per-generation
  train and eval outputs for both arms.
- **"upstream commit still unpinned"** — `resolved_identifiers.json` pins gpt2
  (`607a30d7…`), the detector (`08f218f1…`), wikitext (`b08601e0…`), and the
  prepared train file (`77557c85…`); upstream is pinned at
  `GeorgeDrayson/model_collapse@feb85114…`.

The reproduction is `valid_with_limitation`, not a clean pass; the limitations are
in the verification file and are not restated here.

## 4. What this branch did not do

No merge, no tag, no cherry-pick, no rebase, no force-push. The numbers above are
quoted to show the contradiction; their authoritative home is
`week-2/khantushig-positive-control` and the integration branch.

## 5. What somebody has to decide

1. **Merge `cd73d39`.** Neil opens a PR from `week-2/neil-frozen-data-metrics`
   into `integration/week-2-jul25-jul31`. Nothing in the reference-chain workstream
   can proceed without it.
2. **Promote the integration branch to `main` and tag it**
   `week-2-freeze-2026-07-31`, so the freeze the configs reference exists.
3. **Approve real budgets.** `configs/experiment/primary_pilot.json` carries
   `scientific_status: "fixture_frozen_real_run_blocked"` and an explicit
   `real_run_blocker` requiring tokenizer-counted human and total token budgets.
4. **Correct the STATUS row** once (1) and (2) land.

Until (1)–(3) are resolved there is no executable frozen design, and the
`AWAITING_JULY_31_FREEZE` configs have no legitimate source for their values.
