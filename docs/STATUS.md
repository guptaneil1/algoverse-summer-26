# Current Project Status

**Last truthful update:** August 18, 2026 — pilot launched on 4× RTX 4090 after four
execution defects were found and closed. **Result not yet in.**
**Previous update:** August 17, 2026
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

> **Pilot in flight, 2026-08-18.** The 25-chain primary pilot
> (`configs/experiment/primary_pilot.json`, `FROZEN`) is running on 4× RTX 4090.
> Nothing about its *result* is known, and nothing in this file should be read as one.
> What is known: the apparatus executes end to end on real hardware, one full chain
> completes in **3,393 s** measured, and a completed chain certifies
> `valid_with_limitation` — the two limitations being `LIMIT_NEAR_DUPLICATE_NOT_CHECKED`
> and `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE`.
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
> Two decisions were made under that pressure and are **proposed, not ratified**:
> P-008 re-specifies realised budget matching as a ceiling reached up to indivisibility;
> P-009 makes `total_optimizer_tokens` a reported projection rather than an asserted
> budget. P-009 rests on a projection the first measurement already contradicts —
> **16,678,912** actual against 16,100,000 projected, on the arm that spends nothing —
> and should be re-derived now that a measurement exists.
>
> Cost reality: measured per-chain time puts the grid near **7 hours**, against the 2.8 h
> the prior handover carried and the ~$9.80 P-004 derived for *more* arms. Both
> estimates predate any chain; P-004's derivation needs revisiting.

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
| Paper | Ronit | 5 of 10 sections drafted | Drafted: related work 1,016 / introduction 834 / appendix 731 / problem 557 / limitations 451 words. Stubs: method 61, experiments 72, abstract 58, results 45, conclusion 36 | Method and experiments are the writable gap — neither needs a run. Results and conclusion correctly pend the chains |
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
