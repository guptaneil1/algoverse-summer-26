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
| ☐ | Training regime: continued fine-tuning or from scratch | U-001 | Team |
| ☐ | Licensed primary domain selected and recorded | U-002 | Neil |
| ☐ | Lifetime and total token budgets | U-003 | Aarav |
| ☐ | One primary tail-retention metric | U-004 | Neil |
| ☐ | Contribution type: empirical-led or theory-led | U-005 | Team |
| ☐ | Smallest scientifically meaningful effect | U-006 | Aarav + mentors |
| ☐ | **Under-coverage score definition frozen** | U-007 | Aarav |
| ☐ | Ordered seed list declared | — | Aarav |
| ☐ | Checkpoint retention policy declared before launch (`COMPUTE.md`) | — | Khantushig |

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
| ☐ | Preflight budget equality passed for every chain | `make preflight CONFIGS="…"` |
| ☐ | Every chain emitted a schema-valid manifest and chain result | `python scripts/validate_run.py runs/*` |
| ☐ | No chain classified `invalid` is included in any analysis | validator exit code |
| ☐ | Every chain classified `valid_with_limitation` has its limitation stated in the paper | validator output |
| ☐ | Failed and incomplete chains retained, not deleted | `FAILURE_LOG.md` |
| ☐ | Validity certificate issued per headline result, by someone who did not operate the run | `docs/VALIDITY_CERTIFICATE_TEMPLATE.md` |
| ☐ | Primary NLL and tail metrics independently recomputed from frozen outputs | Neil |
| ☐ | Results freeze tagged | `week-3-results-freeze-YYYY-MM-DD` |

## Gate E — Analysis and writing

**Partially cleared 2026-08-17.** Sections 01, 05, 06, 07, 08, 09 written or amended.

| | Check |
|---|---|
| ☑ | Every paper-facing number generated by a script; none typed by hand — `scripts/generate_method_tables.py` emits `paper/tables/method_hyperparameters.tex` and `positive_control.tex` from `configs/policy/joint.json` and the committed run artifacts. Enforced by `test_committed_paper_sections_contain_no_hardcoded_result_numbers`, which caught a first draft that violated it. |
| ◐ | Tables regenerated from immutable artifacts; **digests not yet recorded** for the two new `paper/tables/` entries. Figures unchanged. |
| ☑ | No fixture artifact is cited as evidence. `05_method.tex` refers to fixture-based evidence only to bound what it establishes. |
| ☑ | Template 9 of `paper/outcome_contingent_language.md` ("No primary result at all") used verbatim in `07_results.tex`. `docs/outcome_templates.md`'s nearest entry covers validation *failure*, which is not this case: nothing failed validation, nothing ran. |
| ☑ | There is no primary result. The abstract says so in its closing sentence, not a footnote. |
| ☐ | Every abstract sentence licensed by its row in `docs/evidence/claim_evidence_matrix.md` |
| ◐ | Scanned clean across 01, 05, 06, 07, 09. **`08_limitations.tex` uses "optimal" twice**, both inside disclaimers ("does not establish an economically optimal…", "does not claim… the proposed policy is optimal"). Negated usage, not a claim — but an owner should confirm that reading rather than have it ticked silently. |
| ☐ | C-004 novelty claim carries all three modifiers: *recursive*, *fixed lifetime human-token budget*, *matched non-joint baselines* |
| ☐ | Claim ledger statuses updated to match what the evidence supports |
| ☑ | `08_limitations.tex`: "one licensed text domain and a small screening-scale language model"; "only the frozen domain, model, horizon, decoding rule, and budget regime". |
| ☑ | No `RESULT_PENDING` marker remains in `paper/sections/`. |

## Gate F — External review

| | Check |
|---|---|
| ☐ | Hostile external novelty review obtained from someone outside the team |
| ☐ | Statistics and experimental-design review obtained |
| ☐ | Uninvolved-reader review obtained |
| ☐ | Headline table reproduced by someone who did not write the analysis |
| ☐ | No mock-review score below 3/4 on quality, clarity, significance, originality |
| ☐ | No unresolved fatal novelty or correctness objection |
| ☐ | The contribution can be summarised correctly after one reading |

## Gate G — Package

| | Check | Verify with |
|---|---|---|
| ☐ | Paper builds cleanly from a clean checkout | `paper-build` CI job |
| ☐ | Submission archive builds | `make submission` |
| ☐ | No secrets or large assets committed | `git ls-files \| xargs du -sh \| sort -h \| tail` |
| ☐ | Every headline value traces to a frozen artifact | claim-to-evidence audit |
| ☐ | Presentation prepared from `docs/presentation_outline.md` |
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
