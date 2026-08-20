# Submission Checklist

**Deliverable:** `docs/weekly/WEEK_4.md`, Ronit — "Finalize citations, appendix references,
slides/poster, submission summary, and checklist."

**How to use.** Work top to bottom. A section may not be started until every box above it is
ticked, because each depends on the one before. Every box is either objectively verifiable by a
command or is a named person's signed judgement — none is a matter of opinion.

**Current reality (2026-08-15):** Gate A is **8 of 9** — the clean-environment install has not been
run on a clean machine. Gate B is blocked on compute. Gates C through G are unreachable. That is
the honest position and this file does not pretend otherwise.

Note that under this file's own ordering rule, the unticked Gate A box means Gate B is not formally
startable either; it is listed as compute-blocked because that is the binding constraint in
practice, not because Gate A is finished.

---

## Gate A — Repository truth

| | Check | Verify with | State |
|---|---|---|---|
| ☑ | Lint passes | `ruff check .` | passing |
| ☑ | Unit and contract tests pass | `pytest -q` | **578 passing, 15 skipped** (2026-08-17) |
| ☑ | Repository audit passes | `make audit` | passing |
| ☑ | Toy smoke chain runs | `make smoke` | passing |
| ☑ | Upstream positive control is pinned | `docs/evidence/upstream_pin.md` | commit `feb8511…` |
| ☑ | Compute forecast exists with stated assumptions | `COMPUTE.md` | A1–A7 recorded |
| ☑ | `docs/STATUS.md` matches reality | read it | current |
| ☑ | Every known implementation defect is logged | `FAILURE_LOG.md` | F-001 through F-009 recorded |
| ☑ | Clean-environment install verified | `bash scripts/verify_clean_install.sh` | **Run 2026-08-17. Passes on pip >= 23.1** (fresh venv, pip 26.2.1: editable install, 575 passed / 18 skipped, smoke chain, lint, audit, preflight all pass). **Fails on pip 21.2.3**, which is this machine's system pip: PEP 660 editable installs need pip >= 21.3, and all five reported failures cascade from that one cause. See `results/clean_install_report.md`. |

## Gate B — Positive control

**Cleared 2026-08-17.** Both arms executed on 1x RTX 4090. Evidence:
`docs/positive_control/observed_table.md`, `docs/positive_control/measurements_2026-08-17_rtx4090/`,
`COMPUTE.md`, `FAILURE_LOG.md` F-006 through F-009.

| | Check |
|---|---|
| ☑ | `transformers` pinned to a specific commit rather than tracking main (`upstream_pin.md` §4) — pinned to release **4.48.3**, not a git SHA; the hazard the box guards against (tracking `main`) is closed |
| ☑ | Resolved framework versions and tokenizer revision recorded in `PROTOCOL.md` §2 — torch 2.8.0+cu128, transformers 4.48.3, datasets 3.2.0, accelerate 1.2.1, Python 3.12.3, GPT-2 `607a30d7…` |
| ☑ | Both upstream arms completed the full horizon — 11 generations each |
| ☑ | Expected-versus-observed comparison against a criterion frozen **before** execution — ordering and `degradation_ratio_gt: 1.0` frozen in the arm configs; 5% tolerance is engineering-only |
| ☑ | Clean rerun reaches the same scientific conclusion — two independent executions, different hardware and stacks, agree to under 0.3% on every quantity |
| ◐ | Every deviation from upstream listed and dated before the run — **partially.** Deviations 1-11 predate execution. Deviations 12-18 (`expected_vs_observed.md` §6.2) were forced *during* it: the wandb shim, `--no-shared-generation-zero`, and `--prune-models`. All are recorded and dated as discovered, per §6's append rule, but they were not pre-declared. State this rather than tick it clean. |
| n/a | If reproduction failed: a truthful failure package exists — not applicable; the reproduction succeeded. `failure_report.md` from the 2026-08-03 block is retained and marked superseded. |

## Gate C — Frozen decisions

Each of these is a human decision. None may be made after seeing primary outcomes.

**The Owner column is inferred from `docs/TEAM.md` directory ownership, not recorded in
`DECISIONS.md`.** `DECISIONS.md` assigns no owner to U-001 through U-007. Confirm each assignment
with the person named before treating it as agreed.

| | Decision | ID | Owner (inferred) |
|---|---|---|---|
| ☑ | Training regime: retrain from pretrained base each generation | U-001 | Closed by P-003 |
| ☑ | WikiText-103, 400 base_train articles | U-002 | Closed by P-004; cost re-derived in P-010 |
| ☑ | 750,000 lifetime / 75,000 per-gen / 150,000 max | U-003 | Closed by P-005; token projection superseded by P-010 |
| ☑ | `tail_retention`, ratio-based | U-004 | Closed by D-022. **U-004b closed as unreachable** — window shut when primary outcomes opened |
| ☑ | Design-and-validation, no primary empirical claim | U-005 | Closed by P-006; the executed pilot confirms it |
| ☑ | 2% relative | U-006 | Closed 2026-08-19, checked against measured anchors. **Never externally reviewed**; the paper says so |
| ☑ | Frozen and implemented | U-007 | Joint rule implemented; terminal reconciliation fixed at F-020 |
| ☑ | 101, 202, 303, 404, 505 | — | Frozen in `primary_pilot.json`, executed |
| ☑ | Pruned per chain on completion | — | Regenerable from frozen config and seed; recorded in the run README |

**F-001 is no longer a submission blocker — see `FAILURE_LOG.md` F-005.** F-001 recorded
`JointPolicy` as observationally identical to `SelectionOnlyPolicy`. That was true of the code it
read, but that code was the Week-1 scaffold: commit `243f58b` reverted `policies/joint.py` from
Aarav's frozen 150-line implementation to the 49-line scaffold hours before F-001 was written. With
the frozen rule restored, the four families produce four distinct trajectories at every seed
tested, so the decomposition C-002 depends on does exist.

Two qualifications, so this is not read as more than it is. The measurement is **structural, not
scientific**: it shows the fixture simulator can tell the four families apart, and the simulator's
degradation and rescue rates are chosen constants. And U-007 is **not** closed by it — the
allocation rule is frozen at `week2-fixture-v1`, but the under-coverage **score definition** still
has no computation defined anywhere, and C-002 rests on both.

## Gate D — Primary runs

| | Check | Verify with |
|---|---|---|
| ☑ | Preflight budget equality passed | `preflight_budget.py` → PASSED, and **realised** equality now holds on both axes: human 0.0381%, total 0.0000%, against 0.2000% permitted. `run_pilot --check-only` exits 0 (F-026a) |
| ☑ | All 25 chains emitted schema-valid artifacts | `validate_run.py` over `results/runs/primary_pilot_v2_2026-08-20/` |
| ☑ | **No chain classifies `invalid`.** 25 `valid_with_limitation`, 0 `invalid`, read from the per-chain report in `validation.json` rather than an aggregate exit code — the error F-021 recorded. The table lists all 25 and every one is admissible | `pilot/validation.json`, tracked |
| ☑ | Both limitations stated in §7 | `LIMIT_NEAR_DUPLICATE_NOT_CHECKED`, `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE` |
| ☑ | All 25 retained | `results/runs/primary_pilot_v2_2026-08-20/`. The superseded 2026-08-18 grid is retained too, with its 10 invalid chains, and neither run's artifacts were edited |
| ☐ | **Evidence pack prepared, certificate not issued.** `results/certificates/primary_pilot_v2_2026-08-20_EVIDENCE_PACK.md` gathers every machine-checkable field with the command that reproduces it, and states plainly what it does *not* close: the two blocking sections both carry a known unverified property, and a metric must still be recomputed from raw outputs rather than from `chain_result.json`. It is deliberately unsigned — it was assembled by the run operator | `docs/VALIDITY_CERTIFICATE_TEMPLATE.md`; needs a non-operator |
| ◐ | **Automatable half done.** `scripts/reproduce_pilot_table.py` recomputes every published value from `chain_result.json` with arithmetic written independently of the generator; all reproduce for **both** the 2026-08-20 grid and the superseded 2026-08-18 one, and `test_published_values_reproduce.py` runs it in CI. The human half -- a person other than the analysis author running it -- still stands | Neil |
| ☑ | Results freeze tagged `results-freeze-2026-08-20`, annotated with the grid it covers and the primary result. Batch verdicts over all 50 chains of both grids retained at `results/certificates/batch_verdicts.json`, regenerating byte-identically with `--audited-at`. **The batch exits 2** because the superseded grid contributes ten deliberately-retained invalid chains; `results/certificates/README.md` records why that does not block the freeze rather than suppressing it by running the batch over the good grid alone | `git show results-freeze-2026-08-20` |

## Gate E — Analysis and writing

**Partially cleared 2026-08-17.** Sections 01, 05, 06, 07, 08, 09 written or amended.

| | Check |
|---|---|
| ☑ | Every paper-facing number generated by a script; none typed by hand — `scripts/generate_method_tables.py` emits `paper/tables/method_hyperparameters.tex` and `positive_control.tex` from `configs/policy/joint.json` and the committed run artifacts. Enforced by `test_committed_paper_sections_contain_no_hardcoded_result_numbers`, which caught a first draft that violated it. |
| ☑ | Tables and the results figure regenerated from immutable artifacts, and **digests now recorded** in `paper/tables/generated_provenance.json` by `scripts/record_paper_provenance.py`. `--check` re-verifies them and `tests/analysis/test_generated_provenance.py` runs it in CI, so a hand-edit to a generated file fails the suite. Verified by tampering with `pilot_macros.tex` and confirming the check fails. |
| ☑ | No fixture artifact is cited as evidence. `05_method.tex` refers to fixture-based evidence only to bound what it establishes. |
| ☑ | **Template 2 ("Null")** of `paper/outcome_contingent_language.md` now governs `07_results.tex` and the abstract: the interval includes the frozen practically equivalent region, so the null template applies and the words "directionally consistent", "promising" and "approaching significance" are absent. Template 9 ("No primary result at all") no longer applies — there is a primary result. Template 5 ("Mixed across metrics") is applied to the *timing* contrast, where the two preregistered outcomes disagree. |
| ☑ | There **is** a primary result and the abstract leads with it rather than burying it: a null, stated with its interval, before any secondary effect. The secondary effects are larger and would read better first; they do not come first. |
| ☑ | Every abstract sentence licensed. **Re-audited 2026-08-20** for the rewritten abstract: S22–S32 added, S10 resolved to a null with direction and interval per the standing rule, and S15–S18 and **S20 retired** — S20 asserted that no claim is made about allocation policy, which is now false and was checked out of four sections. Two pairings are mandatory: any timing claim carries the confirmatory disagreement, and any statement of the null carries the missing comparators |
| ☑ | Scanned clean across every section. The two negated uses of "optimal" in `08_limitations.tex` were rewritten away on 2026-08-20 rather than left for an owner to adjudicate: the disclaimers now say what they mean without the banned word ("which human-data policy is best under any economic accounting", "any policy measured here is the best available"). Zero occurrences remain outside the word "optimizer". |
| ☑ | C-004 carries all three modifiers; *matched non-joint baselines* was missing and was added 2026-08-19 | C-004 novelty claim carries all three modifiers: *recursive*, *fixed lifetime human-token budget*, *matched non-joint baselines* |
| ☑ | C-002 records the attempt that did not test it; C-004 internally audited with the stop rule applied |
| ☑ | `08_limitations.tex`: "one licensed text domain and a small screening-scale language model"; "only the frozen domain, model, horizon, decoding rule, and budget regime". |
| ☑ | No `RESULT_PENDING` marker remains in `paper/sections/`. |

## Gate F — External review

| | Check |
|---|---|
| ☐ | Hostile external novelty review obtained from someone outside the team |
| ☐ | Statistics and experimental-design review obtained |
| ☐ | Uninvolved-reader review obtained |
| ☐ | **Needs a person.** `python scripts/reproduce_pilot_table.py` is one command and prints pass/fail; anyone on the team can run it |
| ☐ | No mock-review score below 3/4 on quality, clarity, significance, originality |
| ☐ | No unresolved fatal novelty or correctness objection |
| ☐ | The contribution can be summarised correctly after one reading |

## Gate G — Package

| | Check | Verify with |
|---|---|---|
| ☐ | Paper builds cleanly from a clean checkout | `paper-build` CI job |
| ☐ | Submission archive builds | `make submission` |
| ☑ | No secrets: scanned 2026-08-19, the only hits are documentation prose about *not* committing credentials. Largest tracked asset is `base_train.jsonl` at 5.8 MB |
| ☐ | Every headline value traces to a frozen artifact | claim-to-evidence audit |
| ◐ | Outline rewritten again for the corrected grid (2026-08-20): the status slide now leads with the **null**, slide 5 becomes where the effect actually is, the defects slide is split into loud/cheap and silent/expensive rather than one list, and the design-change slide records what displacement bought. Slides themselves not built |
| ☐ | Final tag created | `submission-final-YYYY-MM-DD` |

---

## Standing prohibitions

These apply at every gate and are not negotiable by deadline pressure.

- **Final test data is radioactive.** It may not influence prompts, selection, thresholds, early
  stopping, or hyperparameters. If a proposed change touches the test partition, stop.
- **After a results freeze**, permitted edits are clarity, citations, formatting, packaging, and
  removal of unsupported claims. Adding a seed, metric, subgroup, exclusion, budget, or redesigned
  method is prohibited.
- **An unfavourable result is not a bug.** Reclassifying it as an implementation failure requires
  independent evidence of a defect, recorded in `FAILURE_LOG.md`.
- **Fixture output may never be cited.** Everything under `results/` produced by
  `scripts/build_fixture_artifacts.py` is watermarked non-evidence.

## If the deadline arrives before Gate D

Ship the honest paper. A manuscript that presents a well-specified question, a validated pipeline,
a pinned positive control, and a truthful account of what was not reached is a real contribution
and is defensible. A manuscript with results that cannot be traced to artifacts is neither.
