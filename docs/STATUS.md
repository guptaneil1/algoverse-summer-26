# Current Project Status

**Last truthful update:** August 20, 2026 — the corrected grid completed under both
fairness axes and the primary contrast is a **valid null**. C-002 tested and not supported.
**Previous update:** August 19, 2026 — pilot executed, analysed, primary contrast recorded
as NOT ESTABLISHED. Variance estimate delivered.
**Update before that:** August 17, 2026
**Update before that:** August 15, 2026 — upstream positive-control commit pinned.
**Original deadline:** August 15, 2026 — **not met; see §Schedule reality**
**Current week by calendar:** Week 4 (August 8–14 plan). **Current week by evidence:** Week 2,
now complete for the positive-control workstream.

**Reason for this update:** a major evidence gate. Stage A executed end to end on 2026-08-17:
both arms, eleven generations, artifact hashes verified, results regenerated from saved metrics.
This is the second independent execution and the one whose artifacts survive. The Stage A
environment freeze in `PROTOCOL.md` §2 is recorded from measured host values, releasing the
seven conditional xfails. Evidence: `docs/positive_control/observed_table.md`,
`docs/positive_control/measurements_2026-08-17_rtx4090/`, `COMPUTE.md`, and `FAILURE_LOG.md`
F-006 through F-009.

> **Corrected grid completed, 2026-08-20. The primary contrast is a valid null.**
> 25 of 25 chains on 2× RTX 4090, run in four seed-block phases (`DECISIONS.md` P-012),
> zero chain failures. Full record: `docs/runs/primary_pilot_v2_2026-08-20_results.md`.
>
> **Both fairness axes hold.** Human spread across spending arms **0.0381%** against
> 0.2000% permitted; total optimizer tokens **identical at 16,678,912 for every chain in
> every arm**, a 0.0000% spread. `run_pilot --check-only` exits 0. The previous grid failed
> both — 10.1070% (F-020) and 2.2564% (F-021). P-011's displacement rule, accepted
> unvalidated, is now validated on 25 chains.
>
> **Certification: 25 `valid_with_limitation`, 0 `invalid`**, read from the per-chain
> report in `validation.json` rather than an aggregate exit code — the specific error F-021
> recorded. The two limitations are the standing `LIMIT_NEAR_DUPLICATE_NOT_CHECKED` and
> `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE`.
>
> **C-002 is tested and NOT SUPPORTED.** Joint minus the strongest eligible non-joint
> baseline (`selection_only`) is **+0.01026, 95% CI [-0.00916, +0.02968]**, +0.45%
> relative, against a practical equivalence region of ±0.05073. The interval lies *wholly
> inside* that region, so this is equivalence at the preregistered threshold rather than
> insufficient power — the design is powered to three chains per arm and ran five. It is
> **not** evidence that joint is worse: the interval covers zero. Confirmatory tail
> retention agrees at +0.00003, CI [-0.00100, +0.00105].
>
> **Three admissible secondary contrasts locate the effect.** All arms are matched on both
> axes, so unlike the previous grid these stand on the same footing as the primary. Spending
> a human budget at all is worth **4.04%** against a control trained on identical data
> volume; targeting under-covered modes a further **9.59%**; scheduling when to spend
> **0.41%**, an interval containing zero. Which modes the budget targets matters; when it is
> spent does not, on the primary outcome. On the confirmatory outcome timing shows a small
> effect whose interval excludes zero, and that disagreement is reported.
>
> **Cost:** 5.96 h across launches in which every chain finished, 9.56 h counting the
> attempts F-025 and F-026 ended; roughly $18 and $29 at the observed $3/hour. Throughput
> 5.07 min/generation. Wall time for a phased grid is the **sum of per-launch maxima**, not
> the max over shard summaries — a single max returns 3.35 h, which is one phase.
>
> **Two infrastructure defects cost time and no science.** F-025 (launcher unpinned from its
> own GPU) and F-026 (resume re-ran the generation it was interrupted in, into a directory
> upstream refuses to overwrite). Both stopped chains from starting; neither corrupted a
> chain that finished.
>
> **Variance reproduced.** CVs 0.32%–1.09% against a 2% threshold, on an independent grid
> under a changed assembly rule, against 0.41%–1.08% before. `joint`'s variance is no longer
> qualified: it spent its budget as designed.

> **Pilot executed and analysed, 2026-08-19.** The 25-chain primary pilot ran to
> completion on 4× RTX 4090. The longest shard ran **6.75 h**; the grid was observed
> complete at 05:24 after roughly an hour of idle billing. All 25 chains completed and none
> failed, but certification is **10 `invalid`, 15 `valid_with_limitation`** -- an
> earlier version of this block said all were limited, which misread the run's
> aggregate exit code as a per-chain classification (F-021). Full record:
> `docs/runs/primary_pilot_2026-08-18_results.md`.
>
> **The primary contrast is NOT ESTABLISHED — invalid, not null.** `--check-only`
> exits 1: `joint` consumed 674,193 human tokens against every other spending arm's
> ~749,850, a 10.1% spread, identically at all five seeds. It received 10% less human
> data than the arm it is contrasted against, so `PROTOCOL.md` §4's fairness condition
> fails and `CLAIMS.md` C-002's contract is unmet by this run. Cause and fix:
> `FAILURE_LOG.md` F-020 — terminal reconciliation raised `joint`'s spending cap but
> left its floor at 1 token, so its urgency rule, not the reconciliation, decided the
> spend. **No claim about the joint-versus-baseline comparison follows from this run.**
>
> **A second constraint was never checked.** `PROTOCOL.md` §4 requires matched total
> optimizer tokens as well as matched human tokens, and only the human axis was ever
> asserted. Realised totals span **2.26%** across arms, above the 2% threshold. Applying
> both axes, the only matched contrast in the whole run is `schedule_only` vs `random`
> -- which is the null. The `selection_only` advantage carries 1.7% more total training
> tokens and is **suggestive but confounded**, not a budget-matched result. F-021; the
> guard now asserts both axes.
>
> **What the run does establish is the between-chain variance the compute gate was
> waiting on**, and it is unaffected by the spend gap because it is measured *within*
> arms. Coefficients of variation are 0.41%–1.08% against a 2% practical threshold;
> the paired `joint`-minus-`selection_only` SD is 0.00880 against a 2% threshold of
> 0.04626. **Five paired chains already give roughly 80% power at 2%.** This inverts
> the planning assumption: chain count is not the binding constraint on a powered
> study. `COMPUTE.md`'s gate can be released on this evidence, with the caveat that
> `joint`'s own variance was measured on chains that underspent.
>
> Also measured: one chain completes in **3,393 s**. The two non-blocking limitations
> on the fifteen certified chains are `LIMIT_NEAR_DUPLICATE_NOT_CHECKED` and
> `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE`.
>
> **Re-running the grid is blocked on funding, not on code.** 6.75 h at the measured
> per-shard wall time, roughly $20 at the observed rate; the session ended with about $6.
>
> Getting there took four defects, every one found *after* a passing dry run and every
> one invisible to a then-740-test suite (`FAILURE_LOG.md` F-016 through F-019a): a
> launcher guard that no configuration could satisfy; corpus paths resolved against the
> upstream checkout, killing all 25 chains in seconds; two further copies of the same
> guard in the certification path, which would have marked every finished chain invalid;
> and partition provenance declared in a vocabulary the manifest builder did not read.
> All four surfaced from **running one real chain and validating it**, now a required
> step in `docs/RUNBOOK_PILOT_LAUNCH.md` §5a ahead of any grid. The F-002 partition
> vocabulary conflict recorded in the table below is what F-019 turned out to be.
>
> **P-001 through P-010 are now accepted by the project owner** (2026-08-19), not
> ratified by the team — no independent review took place and three sit in other
> members' CODEOWNERS areas. All six U-items are closed: U-006 settled at 2% after a
> check against measured anchors, U-004b closed as unreachable. See `DECISIONS.md` for
> what "accepted" does and does not mean here.
>
> Cost reality, superseding both prior estimates (P-010): the grid ran in **6.75 h** for
> roughly **$20**, against the 2.8 h the prior handover carried and the ~$9.80 P-004
> derived for *more* arms. Powered-design sizing:
> `docs/decisions/powered_design_sizing_2026-08-19.md`.

> **Week 3 did not complete.** The August 7 results freeze did not happen: the
> repository contains zero tags, no `integration/week-3-aug01-aug07` branch, no
> `week-3/*` personal branches, and `results/aggregates/` holds only a README.
> Week 4 as written takes the August 7 immutable aggregate as its input, so it
> cannot start as specified. See `docs/audits/week3_execution_required.md`.
>
> **This file understates the Week 2 positive control.** The row below still reads
> *Not reproduced*, but Week 2 **was** integrated on
> `integration/week-2-jul25-jul31` (PRs #15/#16/#17), and it holds a completed
> two-arm reproduction with per-generation measurements and pinned upstream
> revisions — re-verified by recomputation in
> `docs/positive_control/week3_verification.md`. What did not happen: promotion to
> `main`, the freeze tag, and Neil's `cd73d39` (the frozen WikiText-103 manifests,
> mode definition, and tail metric). Correcting the row requires the integrator to
> promote and tag, so it is flagged here rather than edited unilaterally.
> Evidence: `docs/audits/week2_merge_gap.md`.

| Area | Owner | Status | Current evidence | Blocking issue |
|---|---|---|---|---|
| Literature and novelty | Ronit | Substantially complete | 31 bib entries; **31 sources** in `sources.yaml`; 23-paper `closest_work.csv` with audit status; 5 written novelty threats + responses | External hostile novelty review not obtained |
| Paper | Ronit | **All 10 sections drafted (2026-08-19)** | Abstract 271 words, results and conclusion written against the executed run, limitations carries the pilot's four specific limits. Result numbers are generated into `paper/tables/pilot_macros.tex` and cited as macros; a bare decimal in a section is a test failure | No section is a stub. Outstanding: TeX build is CI-only (no local toolchain), and the checklist's review items all need a person outside the team |
| Positive control | Khantushig | **Reproduced 2026-08-17** | Both arms, 11 generations, on 1x RTX 4090. Second independent execution; agrees with the 2026-08-07 T4 run to within 0.3% on every quantity. Hashes verified, artifacts retained in `docs/positive_control/measurements_2026-08-17_rtx4090/` | None. Was the project-wide critical path; now cleared |
| Recursive runner | Khantushig | **Real chain executes end to end (2026-08-18)** | Toy contract runner as before, plus `runner/real_chain.py`, `training/real.py`, `generation/real.py`, `evaluation/real.py`, `data/corpus.py`. A screening run completed 3 generations of real GPT-2 training, decoding, allocation and per-mode evaluation on one RTX 4090 — `docs/screening/pipeline_validation_2026-08-18.md` | None for the apparatus. The pilot itself is blocked on the July 31 design freeze, not on code |
| Run manifest provenance | Khantushig | **Exercised on a real chain 2026-08-18; certifies `valid_with_limitation`** | A completed GPU chain's manifest carries all five partitions at their frozen sizes (22,637 / 4,235 / 1,359 / 60 / 60) and validates with only `LIMIT_` codes. Pinned by `tests/runner/test_frozen_configs_are_certifiable.py`, which builds the manifest from `run_pilot.chain_config`'s output for every arm rather than from the config on disk | The F-002 vocabulary conflict is **bridged, not resolved**: `build_partitions` now maps `data.manifests` through `_DATA_MODULE_PARTITIONS`. F-019 is what that conflict cost. A rename on either side still breaks it silently |
| Data manifests | Neil | Fixture only; domain audit delivered | Toy manifests; `docs/evidence/domain_audit.md` recommends WikiText-103 primary, C4 `realnewslike` fallback | U-002 not decided; `data/manifests/` contains no real manifest |
| Evaluation | Neil | Two tail candidates implemented, neither frozen | `tail.py` (`tail_retention`, `nll_gap`), `logit_nll.py`, unit tests | U-004 not decided; reliability/independence audit needs real data |
| Policies | Aarav | Four policies implemented; **all four are distinguishable** | `policies/` restored to the `week2-fixture-v1` rule; `tests/policies/test_treatment_decomposition.py` (7 tests, 3 seeds) | **F-001 superseded by F-005** — the degeneracy was an artifact of commit `243f58b` reverting `joint.py` to the Week-1 scaffold, not a property of the method. The under-coverage **score definition** (U-007) is still open |
| Statistics | Aarav | Contract analysis complete; fixture figures regenerated from the restored policies | `analysis/` 716 lines; `results/figures/` 4 figures + provenance hashes | No real primary runs; U-003 and U-006 open |

## Verification status (measured 2026-08-16)

Every row below was produced by running its command on this date. The previous
table reported **294 passed** for the test suite; that figure was not reproducible
at any commit or invocation, and the suite could not run to completion at all —
`tests/analysis/test_fake_result_rendering.py` aborted collection, so `pytest -q`
(what CI runs) executed zero tests.

| Check | Command | Result |
|---|---|---|
| Unit + contract tests | `PYTHONPATH=src python -m pytest -q` | **571 passed, 15 skipped, 7 xfailed** |
| Dependency lock | `uv lock --check` | resolves — 31 packages |
| Lint | `ruff check .` | passes — `install_claude.py` excluded, see below |
| Toy smoke chain | `make smoke` | passes — `completed toy chain: fixture_joint_seed1` |
| Repository audit | `make audit` | passes — `repository scaffold audit passed` |
| Preflight budget check | `make preflight CONFIGS=configs/experiment/toy_cpu.json` | passes — `1 config(s) internally consistent` |
| All fixture artifacts | `make fixture-artifacts` | 12 artifacts hashed into `results/ARTIFACT_MANIFEST.json` |
| Submission archive | `bash scripts/build_submission.sh` | **builds** — `dist/human-data-budget-submission.zip` |
| Paper build | `paper-build` CI job | **unverified locally — no TeX toolchain on this machine** |
| Clean-environment install | `bash scripts/verify_clean_install.sh` | **not yet run on a clean machine** |

**The 7 xfails are resolved (2026-08-17).** `PROTOCOL.md` §2 no longer carries
`TODO(khantushig)`: the environment freeze was recorded from measured values on the
executing host (torch 2.8.0+cu128, transformers 4.48.3, datasets 3.2.0, accelerate
1.2.1, Python 3.12.3, GPT-2 revision `607a30d7...`). The conditional marker in
`tests/runner/_stage_a_gate.py` released them automatically, as designed. The suite
now reports **578 passed, 15 skipped, 0 xfailed**. Pins are recorded in
`requirements-positive-control.txt` rather than `requirements-lock.txt`, which is
uv-generated with `--hash=sha256:` for `--require-hashes` CI.

**Three infrastructure defects found and fixed on 2026-08-15.**

1. **`make submission` could never complete.** `scripts/build_submission.sh` runs `ruff check .`
   under `set -euo pipefail`, and lint had 55 errors — all in `install_claude.py`, a vendored
   Claude-tooling file outside `src/` and outside every `CODEOWNERS` entry. The script therefore
   exited before reaching `git archive`, and the CI `lint` job failed on every PR. Fixed by
   `extend-exclude = ["install_claude.py"]` in `pyproject.toml`.
2. **`.gitignore` excluded every generated artifact the repo depends on.** `results/figures/*` and
   `results/aggregates/*` were ignored with only their READMEs negated, so `make figures` produced
   output that could never be committed — contradicting `results/README.md`, which states Git holds
   "small validated aggregates, generated tables/figures, and documentation." Fixed with explicit
   negations. Raw `runs/` output stays ignored, which is correct.
3. **matplotlib was undeclared.** Figure generation had no declared dependency anywhere, so
   `make figures` could not run in a locked environment. Added as a `figures` optional-dependency
   extra, pinned `>=3.10,<4` because matplotlib version determines PNG bytes and therefore the
   content hashes recorded in `results/figures/figure_provenance.json`.

**One environment finding, not fixed.** `pip install -e .` fails on pip 21.2.3 with "File setup.py
or setup.cfg not found". PEP 660 editable installs landed in pip **21.3**, so that is the floor —
`make setup` will not work on anything older. Tests here were run with `PYTHONPATH=src` instead.

## Scientific claim state

One item has advanced since July 18: the positive control. Everything else stands.

- Recursive-training motivation: literature-grounded with scope qualifiers.
- Exact novelty: unverified (internal audit complete; external review outstanding).
- Positive control: **reproduced**, qualitatively, twice. Arm ordering and degradation
  direction recovered. Agreement with published values rests on a 5% relative difference
  used as an internal engineering tolerance only; this is not proof of exact replication.
- Pipeline correctness: validated on real assets for the positive-control path. The Stage B
  chain path remains fixture-tested only.
- Novel pilot: not run.
- Experimental results: none.
- Broad or main-conference claim: unsupported.

## Schedule reality

The August 15 deadline was not met and no submission exists. The accurate description is not
"behind on weeks 2, 3, and 4" but:

| Week | State |
|---|---|
| 1 | Complete, except two overdue items now closed by this update (upstream pin, domain audit) |
| 2 | **The live frontier.** Partially complete; stalled |
| 3 | 0% — correctly, every task consumes runs that do not exist |
| 4 | 0% — correctly, every task consumes the August 7 freeze that never occurred |

Weeks 3 and 4 are not overdue work. They are unreachable work. No member can begin them.

## Critical path

One dependency chain governs everything:

```
GPU access (done) ─→ Stage A positive control (done, 2026-08-17) ─→ July 31 design
freeze (OPEN) ─→ Stage B pilot ─→ results

The binding constraint is no longer compute. All three primary configurations remain
`AWAITING_JULY_31_FREEZE` and `run_chain.sh` correctly refuses them. That is a decision,
not an accelerator shortage.
```

Independently of compute, three members have Week 2 work available now:

- **Ronit:** ~90% of Week 2 needs no runs — method/experiments prose, claim-to-evidence matrix,
  outcome-contingent templates, presentation outlines. Only the external review is blocked.
- **Neil:** once U-002 is decided, hashing, partitioning, and five disjoint manifests are CPU work.
- **Aarav:** freezing the joint allocation rule is a design decision, not a compute task. Only the
  budget freeze (U-003) genuinely waits on positive-control token accounting.
- **Khantushig:** hard-blocked on GPU. This is the only genuinely blocked workstream.

## Open decisions blocking the pilot

`DECISIONS.md` U-001 through U-006 all remain open. U-002 (domain) now has a written
recommendation awaiting a team decision; the other five have no recommendation yet.

## Meaning of scaffolded

The repository includes interfaces, schemas, toy fixtures, tests, CI, and collaboration
documentation so independent development can proceed. These artifacts do not constitute a completed
training system or experimental evidence.

## Updating this file

Update only at a weekly integration freeze or a major evidence gate. Link the relevant merged PR,
tag, run manifest, or report. Never change `Not reproduced` to `Complete` because code exists; the
corresponding immutable run evidence must exist and validate.

**Ownership gap:** this file appears in no `CODEOWNERS` entry, which is why it went four weeks
without correction. Assign an owner.
