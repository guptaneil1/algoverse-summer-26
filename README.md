# The Human Data Budget

> **Deadline:** August 15, 2026
> **Current phase:** four-week implementation and focused pilot
> **Scientific status:** no validated novel result yet

Language models may increasingly be trained on text produced by earlier language models. Across repeated generations, errors can accumulate and underrepresented parts of human language can disappear. This project asks:

> Under a fixed lifetime budget of human-origin optimizer tokens, when should those tokens be used during recursive training, and which under-covered modes of a human reference distribution should they target?

We compare four budget-matched strategies:

1. fresh random human-data rescue;
2. schedule-only allocation;
3. selection-only allocation; and
4. joint time-and-mode allocation.

The August 15 deliverable is a reproducible published positive-control replication and a focused 124M–160M pilot on one licensed domain. We do **not** currently claim that the joint policy prevents model collapse, is optimal, or generalizes across models and domains.

## Simple example

Suppose a recursive training program has 100 million human-origin tokens available across ten model generations. Random rescue spends them on randomly chosen human examples. Schedule-only rescue chooses the generations in which to spend them. Selection-only rescue chooses under-covered semantic modes but follows a fixed schedule. The proposed joint policy chooses both the generation and the modes, while every comparison receives exactly the same lifetime human-token and total-training-token budget.

## What is being built

```text
frozen data manifests
        ↓
recursive train → generate → allocate human rescue → next generation
        ↓                         ↑
held-out evaluation        budget-matched policy
        ↓
immutable chain results → chain-level statistics → paper tables/figures
```

## Team

| Role | Member | Owns |
|---|---|---|
| Research and submission | **Ronit** | literature, claims, paper, presentation, final packaging |
| Training infrastructure | **Khantushig** | positive control, training, generation, checkpoints, run orchestration |
| Data and validity | **Neil** | data manifests, leakage, provenance, token accounting, evaluation |
| Method and statistics | **Aarav** | policies, baselines, preregistration, paired analysis, figures |

See [TEAM.md](docs/TEAM.md) for exact responsibilities and directory ownership.

## Four-week schedule

| Week | Dates | Frozen outcome |
|---|---|---|
| 1 | July 18–24 | Four independently working subsystems using fixtures |
| 2 | July 25–31 | Positive control, frozen data/metrics, frozen method, result-free paper |
| 3 | August 1–7 | Immutable primary run set and validation-ready artifacts |
| 4 | August 8–14 | Final paper, validity certificate, analysis, release package |
| Submission | August 15 | Clean, tested submission archive |

See [ROADMAP.md](docs/ROADMAP.md) and the files in [`docs/weekly/`](docs/weekly/) for exact named tasks and deliverables.

## Current status

The starting archive contained research-governance documents but no experiment code or results. This scaffold adds the collaboration structure, interfaces, fixtures, tests, and CI needed for four parallel workstreams. The included Python package is a tested contract skeleton, not a completed model-training implementation. See [STATUS.md](docs/STATUS.md) for the current truth.

## Quickstart

Python 3.10 or later is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python -m pip install -e . --no-deps
pytest
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
```

The toy command exercises the policy, manifest, chain-result, and analysis contracts without downloading a model or dataset.

## GitHub workflow

Each week has one integration branch and four named personal branches. Everyone develops from the frozen beginning-of-week snapshot and uses fixtures rather than another person's work-in-progress. Personal draft PRs target the weekly integration branch; the tested integration PR then targets `main`.

```text
main
└── integration/week-N-...
    ├── week-N/ronit-...
    ├── week-N/khantushig-...
    ├── week-N/neil-...
    └── week-N/aarav-...
```

Read [WORKFLOW.md](docs/WORKFLOW.md), then run `bash scripts/bootstrap_branches.sh` after the repository has been created on GitHub. A ZIP upload cannot itself create Git branches.

## Research rules

- Recursive chains—not generations—are experimental units.
- Every budget-matched policy must consume the same lifetime human-origin optimizer tokens and total optimizer tokens.
- Final test data may not influence prompts, selection, thresholds, early stopping, or hyperparameters.
- Every result must trace to a frozen config, code commit, data manifest, raw chain artifact, and versioned analysis command.
- No paper-facing number is entered manually.
- Failures, null results, exclusions, and contradictions remain recorded.
- “First,” “optimal,” and “prevents collapse” are prohibited until established.

## Repository map

| Location | Purpose |
|---|---|
| `docs/PROJECT_CONTEXT.md` | Complete plain-language and scientific context |
| `docs/TEAM.md` | Named ownership and responsibilities |
| `docs/STATUS.md` | Live truth about what exists |
| `docs/ROADMAP.md` | Four-week master plan |
| `docs/WORKFLOW.md` | Branch, issue, PR, integration, and freeze rules |
| `docs/ARCHITECTURE.md` | Component boundaries and dependency direction |
| `docs/interfaces/` | Frozen contracts between independent workstreams |
| `docs/weekly/` | Exact weekly assignments for all four members |
| `src/human_data_budget/` | Implementation package |
| `configs/` | Versioned scientific settings |
| `schemas/` | Machine-readable artifact contracts |
| `tests/` | Unit and contract tests |
| `paper/` | Manuscript source and generated result inputs |
| `results/aggregates/` | Small generated, versionable result aggregates |

## Evidence gates

1. truthful repository and claim ledger;
2. hostile novelty review;
3. published positive-control reproduction;
4. leakage, provenance, token-accounting, determinism, and resume tests;
5. frozen focused pilot;
6. independent artifact and claim audit.

The August deadline compresses the original long-horizon roadmap. Broader multi-domain, 410M/1B, independent-family, and 7B confirmations remain future work and must not be implied by the pilot.

## License

MIT. See [LICENSE](LICENSE).
