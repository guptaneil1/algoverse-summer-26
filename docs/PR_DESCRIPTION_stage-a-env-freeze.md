# Stage B: the corrected grid, both fairness axes holding, and a preregistered null

52 commits. The primary pilot was built, launched, rejected by its own fairness check,
corrected, re-launched, and executed. **The preregistered hypothesis is not supported** —
and that is the headline, not a footnote.

Read `docs/HANDOVER_2026-08-20.md` first if you read only one thing.

---

## What happened

Two grids. The first is superseded and retained; the second is the result.

**Grid 1 (2026-08-18)** ran 25 chains on 4x RTX 4090 and was **rejected by the
preregistered fairness constraint on both of its axes**: `joint` underspent human tokens by
10.1% at every seed (F-020), and realised total optimizer tokens spanned 2.26% across arms
on an axis nothing had ever asserted (F-021). Ten chains certify `invalid`. Its artifacts,
its `validation.json` and its numbers stay in the repository and stay independently
checkable, because F-020 and F-021 cite them.

The second axis was a **design** defect, not an implementation one. Adding human data to a
fixed synthetic corpus makes total training volume depend on how much a policy spent, so
allocation strategy and data quantity cannot be separated — including against a control
that spends nothing, which meant "spending helps" could never be told apart from "more data
helps". P-011 specifies that rescued human examples **displace** synthetic records instead.

**Grid 2 (2026-08-20)** ran 25 chains on 2x RTX 4090 in four seed-block phases. Every chain
completed, none failed, and **none certifies invalid**.

| axis | result |
|---|---|
| human tokens | 749,709–749,995 against a 750,000 ceiling — **0.0381%** spread, against 0.2000% permitted |
| total tokens | **identical at 16,678,912 for every chain in every arm** — 0.0000% spread |

Certification: **25 `valid_with_limitation`, 0 `invalid`**, read from the per-chain report
rather than an aggregate exit code, which is the specific error F-021 recorded.
`run_pilot --check-only` exits 0.

## The result

**The primary contrast is valid and it is a null.**

```
joint - selection_only = +0.01026   95% CI [-0.00916, +0.02968]   +0.45% relative
practical-equivalence region        +/-0.05073
interval lies entirely inside it    yes, reaching 0.0297
```

`CLAIMS.md` C-002 is **tested and not supported**, by its own falsification clause. This is
the strong form of a null: the interval does not merely include zero, it excludes every
difference the preregistration calls practically meaningful. The design is sized for three
chains per arm at that threshold and ran five, so this is equivalence rather than a power
shortfall. It is **not** evidence that joint is worse — the interval covers zero.
Confirmatory tail retention agrees at +0.00003, CI [-0.00100, +0.00105].

**Where the effect actually is.** All arms are matched on both axes, so every secondary
contrast is admissible on the same footing as the primary — unlike grid 1, where exactly one
was.

| contrast | effect | 95% CI |
|---|---|---|
| `random` − `no_rescue` | −4.04% | [−0.121, −0.092] |
| `selection_only` − `random` | −9.59% | [−0.269, −0.218] |
| `schedule_only` − `random` | −0.41% | [−0.036, +0.016] |

Which under-covered modes a fixed human budget targets changes the outcome; when within the
chain it is spent does not — **on the primary outcome**. On the confirmatory tail-retention
outcome timing shows a small effect whose interval excludes zero, and
`docs/evidence/claim_evidence_matrix.md` makes reporting that alongside any timing claim a
mandatory pairing rather than a stylistic choice. The `random` − `no_rescue` figure is worth
a second look: because displacement holds training volume fixed, the control trains on
exactly as much data as the spending arms, so that 4.04% is attributable to the data's
origin rather than its quantity. Under grid 1's additive rule it was not.

## What else the run delivers

1. **Between-chain variance, reproduced.** CVs of 0.32–1.09% against a 2% threshold, on an
   independent 25 chains under a changed corpus-assembly rule — against 0.41–1.08% from
   grid 1. **The frozen five-seed set exceeds what the preregistered threshold requires**,
   which inverts the assumption that chain count would be the binding constraint. Sizing:
   `docs/decisions/powered_design_sizing_2026-08-19.md`, unchanged and now checked twice.
   `joint`'s variance no longer carries the qualification it did in grid 1: it spent its
   budget as designed.
2. **P-011 validated.** It was accepted with "no chain has run under it". 25 have, and
   totals are identical across arms to the token.
3. **Feasibility, measured.** 5.07 min per generation on 2x RTX 4090; 5.96 h for the
   launches in which every chain finished, 9.56 h including the two that infrastructure
   defects ended. Roughly $18 and $29 at the observed $3/hour.
4. **A working apparatus.** Full recursive loop on real models under matched budgets,
   emitting certifiable artifacts, and a resume path that now actually resumes.

## Twelve defects, every one found after a passing dry run

`FAILURE_LOG.md` F-015 → F-026a. All were invisible to the suite as it stood at the time.

**The split that matters is not by severity, it is by whether the defect was loud.**

| Loud — failed visibly, cost time and no science | |
|---|---|
| F-017 | All 25 chains dead in seconds on paths resolved against the upstream checkout |
| F-023 | Corpus record budget wrong by a factor of eight; caught by the $1.30 validation chain the runbook exists to make mandatory |
| F-025 | `--cuda-device` pinned subprocesses but not the launcher, where evaluation runs. Four shards on one GPU, ~1 h |
| F-026 | Resume restarted on the generation an interruption was inside, into a directory upstream refuses to overwrite. 17 chains, ~2.6 h |

| Silent — passed, and cost science | |
|---|---|
| F-016 | A guard no configuration could satisfy — every run self-flagged, exit code 0 |
| F-018 | Two more copies of F-016's rule in the certification path — 25 sound chains would all have certified invalid |
| F-019 / F-019a | Provenance in a vocabulary the manifest builder did not read; then the fix verified against the wrong object. **Unrecoverable** — provenance is written at chain start |
| F-020 / F-020a | Terminal reconciliation raised `joint`'s cap but not its floor. Cost the whole first grid |
| F-021 / F-021a | The second budget axis was never checked. Ten chains invalid, three documents carrying a false statement for a day |
| F-024 / F-024a | The validator's documented exit codes inverted against its own implementation, in five places. An operator following them accepts an invalid run and rejects a valid one |

The loud four cost roughly five hours of pod time between them and no scientific content:
each stopped chains from *starting*, and none corrupted a chain that finished. The silent
ones cost a $20 grid, ten invalid chains, and a day of documents saying something untrue.
**Loud failures are cheap. The ones that pass are not.**

**Four share a shape:** a check whose intent was documented and whose implementation did not
achieve it, with no test asserting the intent. A guard never observed to bind is a guard
whose binding is unverified. F-024a is the same shape one level up — a *fix* whose
enumeration of locations was incomplete, because it searched for the phrasing it remembered.

**Five limits on the dry run are now enumerated** rather than rediscovered one at a time: it
cannot see the subprocess environment (F-017), cannot check budget matching for
score-dependent policies (F-020), cannot exercise anything consuming the decoded corpus
(F-022), cannot run two shards on real hardware (F-025), and cannot produce an interrupted
process, which is the only thing that exposes a resume defect (F-026).

`docs/RUNBOOK_PILOT_LAUNCH.md` §5a requires one real chain plus `validate_run.py` before any
grid; that step found five defects. `docs/RUNBOOK_V2_RESUME.md` adds the phased,
guard-on-failure launch that finished this grid without a further stall.

## Decisions — please review, especially P-011 and P-012

**P-001 – P-011 are accepted by the project owner, not ratified by the team.** No
independent review took place. Three sit in areas CODEOWNERS assigns to others — P-002
(`data/`, Neil), P-008/P-009 (`policies/`, Aarav). This is recorded honestly in
`DECISIONS.md` rather than presented as agreement, and it is the main thing this PR asks
you to look at. **P-012 is not part of that block**: its substance is a spend decision the
owner made directly against costed options, and only its phase *ordering* is the
assistant's — a scheduling choice with no scientific content, which changed which chains ran
first and never which ran.

- **P-008** — realised budget matching as a ceiling reached up to indivisibility, not exact
  equality. F-015's option 2.
- **P-009** — `total_optimizer_tokens` is a projection, not a spendable budget.
- **P-010** — P-004's cost and P-005's token projection superseded by measurement.
- **P-011** — **the design decision the first grid forced, and the one the result depends
  on.** Rescued human examples *displace* synthetic records instead of being appended, so
  the total-token condition holds by construction. It also fixes a confound nobody had
  noticed: under addition the no-rescue control trains on *less data* than every spending
  arm, so "spending helps" could never be separated from "more data helps". **No longer
  unvalidated — 25 chains ran under it and realised totals are identical across arms to the
  token.** If displacement is not the intended scientific setting, this is the moment to
  say so, because the reported effect of spending depends on it.
- **P-012** — finish the interrupted grid to all five seeds, running seed blocks in order of
  remaining cost. Executed in full; because it reached the last phase the ordering left no
  trace in the design. Outcome recorded in `DECISIONS.md`.

**All six U-items are closed.** U-006 settled at 2% after checking it against measured
anchors; it cannot be changed honestly now, because primary outcomes are open. U-004b closed
as unreachable — its window shut when the AUC figures were computed.

**One threshold correction is worth a second opinion.** Three conventions for U-006's
denominator existed in the repo: both documents that settled it compute 2% against the
fresh-random mean, and the analysis generator used the strongest baseline. The code now uses
the documented convention. That is a threshold definition touched *after* primary outcomes
were open, which is what U-006 exists to constrain — so two things are recorded rather than
assumed: the verdict is identical under either convention (±0.05073 and ±0.04586, with the
interval reaching 0.0297), and both figures are emitted as macros so a reader can check.
F-026a carries the full note.

## Paper

All ten sections written against the executed grid. The abstract, introduction
contribution, results, limitations and conclusion were rewritten when the run landed: the
paper previously reported no primary result and now reports a null with an interval.
**Every result number is generated into `paper/tables/pilot_macros.tex` from chain artifacts
and cited as a macro — a bare decimal in a section is a test failure.**

`docs/evidence/claim_evidence_matrix.md` carries a fresh audit of every sentence in the
rewritten abstract, including the retirement of "we make no claim about allocation policy",
which is now false and had to be checked out of four sections.

## Artifacts

`results/runs/primary_pilot_v2_2026-08-20/` — 65 files tracked (~250 KB): 25 chain results,
25 generation-0 reference snapshots, eleven shard summaries, `aggregate.json`,
`validation.json` and the hash ledger. The 162 MB of run manifests are not tracked, but
`ARTIFACT_HASHES.json` records SHA-256 for all 101 files so an archived copy verifies
against the repo. **The archive is a ~36 MB tarball held outside the repository and is the
only copy** — it cannot be regenerated without another ~$18 and six hours of GPU time.

Two artifact classes are newly tracked, for both grids. `validation.json`, because F-021
happened by reading an aggregate exit code instead of the per-chain report sitting in that
file; and the reference snapshots, because the confirmatory metric is not recomputable
without them.

`results/runs/primary_pilot_2026-08-18/` is retained unchanged, including its ten invalid
chains.

## Tests

**817 passed, 14 skipped, 0 failed** (from 788). Ruff and repository audit clean, and
`bash scripts/build_submission.sh` builds the archive with its SHA-256.

Run these with the venv active. Several tests and the submission script shell out to bare
`python`; without `.venv/Scripts` on `PATH` they pick up the system interpreter, which has no
`human_data_budget` installed, and produce one failure and 58 collection errors that say
nothing about the repository.

New guards worth knowing about:
- `test_budget_matching.py` — both fairness axes, 30 tests
- `test_terminal_reconciliation_binds.py` — asserts reconciliation *binds*, not merely that it runs
- `test_frozen_configs_are_certifiable.py` — builds the manifest from what the launcher constructs, not from the config on disk
- `test_corpus_displacement.py` — P-011's invariant
- `test_document_coherence.py` — documents may not contradict the artifacts; verified by injecting each drift
- `test_resume_clears_stale_generation.py` — F-026: a resumed generation owns its output directory. 2 of 3 fail if the fix is reverted, verified by reverting it
- `test_run_pilot_seed_subset.py` — `--only-seeds` keeps config order (the shard deal is positional) and phase summaries cannot collide

## What this PR does not do

- **It does not diagnose why the additive rule made totals diverge.** Displacement removes
  the divergence by construction; F-021a's question — block packing or divergent generated
  text — is now unanswerable from these artifacts and is recorded as a limitation rather
  than quietly dropped.
- **It does not implement comparators 5–7.** Accumulation or fixed-fraction mixing,
  detector-based selection, and the oracle upper bound. "Strongest eligible baseline" means
  strongest among four, and without the oracle the headroom above every policy measured here
  is unknown. This is stated wherever the null is.
- **It does not obtain any external review.** Novelty is internally audited; the statistics
  review has still not happened, and the primary finding is an equivalence, which rests on
  the 2% threshold more directly than a positive finding would.
- **It does not issue a validity certificate.** The evidence pack is prepared and
  deliberately unsigned — it was assembled by the run operator.
- **It does not build the paper.** No local TeX toolchain — CI only.

## Asks

1. **Aarav** — P-008, P-009, P-011 are in your area. P-011 is no longer a proposal: 25
   chains ran under it and it is what makes the totals identical. If displacement is not the
   intended scientific setting, say so now, because the result depends on it.
2. **Neil** — P-002 is in yours, and F-002's partition vocabulary conflict is *bridged, not
   resolved*. Also: `python scripts/reproduce_pilot_table.py` is one command and prints
   pass/fail. The checklist wants it run by someone other than the analysis author, and that
   is the only reason the item is still open.
3. **A statistics reader** — the primary finding is an equivalence inside a ±2% region. That
   threshold has been checked against measured anchors and never externally reviewed. It is
   now load-bearing in a way it was not when the run had no result.
4. **Anyone** — the workshop CFP. Still never supplied, and easier to answer now: there is
   an empirical result, not only a design.
