# Stage B: pilot executed, primary contrast not established, apparatus validated

26 commits. The primary pilot was built, launched, executed, analysed, and reported. **No
allocation claim survives** — and that is the headline, not a footnote.

Read `docs/HANDOVER_2026-08-19.md` first if you read only one thing.

---

## What happened

The 25-chain primary pilot ran on 4× RTX 4090: five policies × five frozen seeds, horizon
10, 6.75 h, ~$20. Every chain completed and none failed.

**The preregistered fairness constraint rejected it, on both of its axes.**

`PROTOCOL.md` §4 requires matched lifetime human-origin tokens **and** matched total
optimizer tokens.

| axis | result |
|---|---|
| human tokens | `joint` consumed 674,193 vs the others' ~749,850 — a **10.1%** shortfall at every seed (F-020) |
| total tokens | realised totals span **2.26%** across arms, above the 2% threshold. **This axis was never asserted anywhere** (F-021) |

Certification: **10 `invalid`, 15 `valid_with_limitation`.**

The primary contrast is therefore reported as **invalid, not null**. We did not repair it,
reweight it, or promote the secondary comparison that would have supported our hypothesis —
and that comparison was available and sizeable (`selection_only` beating `random` by 8.4%).
It carries 1.7% more total training tokens in the same direction, so it is confounded, and
`PREREGISTRATION.md` forbids substituting it for a failed primary analysis regardless.

## What the run does deliver

1. **Between-chain variance** — the number `COMPUTE.md`'s compute gate has blocked on since
   Week 3. CVs of 0.41–1.08% against a 2% threshold. Measured *within* arms, so unaffected
   by either failure. **The frozen five-seed set is already powered at the preregistered
   threshold** — which inverts the assumption that chain count would be the binding
   constraint. Sizing: `docs/decisions/powered_design_sizing_2026-08-19.md`.
2. **One clean comparison.** `schedule_only` vs `random` is matched on both axes. It is a
   null: at this budget and horizon, *when* the budget is spent does not detectably change
   the outcome.
3. **Feasibility, measured.** 57.9 min/chain, 6.75 h, ~$20 — replacing two estimates that
   were both wrong (P-004's ~$9.80, P-005's token projection).
4. **A working apparatus.** Full recursive loop on real models, emitting certifiable
   artifacts.

## Seven defects, every one found after a passing dry run

`FAILURE_LOG.md` F-015 → F-021a. All were invisible to a then-740-test suite.

| ID | What it would have cost |
|---|---|
| F-016 | A guard no configuration could satisfy — every run self-flagged, exit code 0 |
| F-017 | All 25 chains dead in seconds on paths resolved against the upstream checkout |
| F-018 | Two more copies of F-016's rule in the certification path — 25 sound chains, all certified invalid |
| F-019 / F-019a | Provenance in a vocabulary the manifest builder did not read; then the fix verified against the wrong object. **Unrecoverable** — provenance is written at chain start |
| F-020 / F-020a | Terminal reconciliation raised `joint`'s cap but not its floor |
| F-021 / F-021a | The second budget axis unchecked; a re-run would **not** fix it |

**Three share a shape:** a check whose intent was documented and whose implementation did
not achieve it, with no test asserting the intent. A guard never observed to bind is a guard
whose binding is unverified.

**Two limits on the dry run are now written down.** It prints the upstream command rather
than running it, so nothing depending on the subprocess environment is covered. And
score-dependent policies allocate from simulated statistics, so **budget matching for them
cannot be tested by simulation at all**.

`docs/RUNBOOK_PILOT_LAUNCH.md` §5a now requires one real chain plus `validate_run.py` before
any grid. That step found five of the seven.

## Decisions — please review, especially P-008 through P-011

**P-001 – P-011 are accepted by the project owner, not ratified by the team.** No
independent review took place. Three sit in areas CODEOWNERS assigns to others — P-002
(`data/`, Neil), P-008/P-009 (`policies/`, Aarav). This is recorded honestly in
`DECISIONS.md` rather than presented as agreement, and it is the main thing this PR asks
you to look at.

- **P-008** — realised budget matching as a ceiling reached up to indivisibility, not exact
  equality. F-015's option 2.
- **P-009** — `total_optimizer_tokens` is a projection, not a spendable budget.
- **P-010** — P-004's cost and P-005's token projection superseded by measurement.
- **P-011** — **the design decision the run forced.** Rescued human examples now *displace*
  synthetic records instead of being appended, so the total-token condition holds by
  construction. This also fixes a confound nobody had noticed: under addition the no-rescue
  control trains on *less data* than every spending arm, so "spending helps" could never be
  separated from "more data helps". **Unvalidated — no chain has run under it.**

**All six U-items are closed.** U-006 settled at 2% after checking it against measured
anchors; it cannot be changed honestly now, because primary outcomes are open. U-004b closed
as unreachable — its window shut when the AUC figures were computed.

## Paper

All ten sections drafted. Method, experiments, results, abstract and conclusion written
against the executed run. **Every result number is generated into
`paper/tables/pilot_macros.tex` from chain artifacts and cited as a macro — a bare decimal
in a section is a test failure.**

## Artifacts

`results/runs/primary_pilot_2026-08-18/` — 25 chain results tracked (100 KB). The 162 MB of
run manifests are not tracked, but `ARTIFACT_HASHES.json` records SHA-256 for all 61 files
so an archived copy verifies against the repo. **The archive is a ~36 MB tarball held
outside the repository and is the only copy** — it cannot be regenerated without another
$20 of GPU time.

## Tests

788 passed, 13 skipped (from 706). Ruff and repository audit clean.

New guards worth knowing about:
- `test_budget_matching.py` — both fairness axes, 30 tests
- `test_terminal_reconciliation_binds.py` — asserts reconciliation *binds*, not merely that it runs
- `test_frozen_configs_are_certifiable.py` — builds the manifest from what the launcher constructs, not from the config on disk
- `test_corpus_displacement.py` — P-011's invariant
- `test_document_coherence.py` — documents may not contradict the artifacts; verified by injecting each drift

## What this PR does not do

- **It does not re-run the grid.** F-021a shows a re-run reproduces the total-token
  divergence. Validate P-011 on one chain first.
- **It does not obtain any external review.** Novelty is internally audited; the statistics
  review has still not happened; the checklist's reproduction items all need someone outside
  the team.
- **It does not build the paper.** No local TeX toolchain — CI only.

## Asks

1. **Aarav** — P-008, P-009, P-011 are in your area. P-011 changes what the experiment
   means; please push back if displacement is not the intended setting.
2. **Neil** — P-002 is in yours, and F-002's partition vocabulary conflict is *bridged, not
   resolved*. A rename on either side still breaks it silently.
3. **Anyone** — the workshop CFP. Still never supplied. It decides whether this is
   submittable as a design-and-validation paper.
