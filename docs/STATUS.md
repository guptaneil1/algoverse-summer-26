# Current Project Status

**Last truthful update:** August 15, 2026
**Previous update:** July 18, 2026 (Week 1) — this file was four weeks stale and understated
completed work in several areas while overstating schedule position.
**Original deadline:** August 15, 2026 — **not met; see §Schedule reality**
**Current week by calendar:** Week 4 (August 8–14 plan). **Current week by evidence:** Week 2.

**Reason for this update:** correction of a stale file, plus one minor evidence gate — the upstream
positive-control commit is now pinned (`docs/evidence/upstream_pin.md`).

| Area | Owner | Status | Current evidence | Blocking issue |
|---|---|---|---|---|
| Literature and novelty | Ronit | Substantially complete | 31 bib entries; **31 sources** in `sources.yaml`; 23-paper `closest_work.csv` with audit status; 5 written novelty threats + responses | External hostile novelty review not obtained |
| Paper | Ronit | 4 of 9 sections drafted | Intro, related work, problem, limitations (~2,860 words) | Method and experiments text unwritten; results sections correctly pending |
| Positive control | Khantushig | **Not reproduced** | Upstream pinned at `feb8511479a2e2dc868e1caf3f63cb99f1fcc746`; `reproduce_positive_control.sh` still exits 3 | **No GPU. Project-wide critical path.** |
| Recursive runner | Khantushig | Contract toy runner complete | `runner/` 836 lines; 12 test files covering determinism, atomic write, checkpoint-resume/integrity, two-generation chain, adapter contracts | Real training/generation not implemented |
| Data manifests | Neil | Fixture only; domain audit delivered | Toy manifests; `docs/evidence/domain_audit.md` recommends WikiText-103 primary, C4 `realnewslike` fallback | U-002 not decided; `data/manifests/` contains no real manifest |
| Evaluation | Neil | Two tail candidates implemented, neither frozen | `tail.py` (`tail_retention`, `nll_gap`), `logit_nll.py`, unit tests | U-004 not decided; reliability/independence audit needs real data |
| Policies | Aarav | Four policies implemented; **two pairs are degenerate** | `policies/` 215 lines; `tests/policies/test_joint_degeneracy.py` | **F-001: joint is observationally identical to selection-only, and random to schedule-only.** Joint allocation rule not scientifically frozen |
| Statistics | Aarav | Contract analysis complete; fixture figures generated | `analysis/` 420 lines; `results/figures/` 4 figures + provenance hashes | No real primary runs; U-003 and U-006 open |

## Verification status (measured 2026-08-15)

| Check | Command | Result |
|---|---|---|
| Unit + contract tests | `PYTHONPATH=src python -m pytest -q` | **294 passed** (was 104) |
| Dependency lock | `uv lock --check` | resolves; `figures` extra included |
| Lint | `ruff check .` | **passes** — `install_claude.py` excluded, see below |
| Toy smoke chain | `make smoke` | passes — `completed toy chain: fixture_joint_seed1` |
| Repository audit | `make audit` | passes |
| Preflight budget check | `make preflight CONFIGS=configs/experiment/toy_cpu.json` | passes |
| All fixture artifacts | `make fixture-artifacts` | 12 artifacts hashed into `results/ARTIFACT_MANIFEST.json` |
| Paper build | `paper-build` CI job | **unverified locally — no TeX toolchain on this machine** |
| Clean-environment install | `bash scripts/verify_clean_install.sh` | **not yet run on a clean machine** |

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

Unchanged from July 18. No item below has advanced.

- Recursive-training motivation: literature-grounded with scope qualifiers.
- Exact novelty: unverified (internal audit complete; external review outstanding).
- Positive control: not reproduced in this repository.
- Pipeline correctness: scaffolded and unit-tested on fixtures; not validated on real assets.
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
GPU access ─→ Stage A positive control ─→ pipeline validation on real assets ─→ Stage B pilot ─→ results
                      ↑
        upstream commit pinned (done, 2026-08-15)
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
