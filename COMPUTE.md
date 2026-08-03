# Compute Ledger

> **No experimental compute has been recorded for this repository.**

This file separates forecasts from actual usage.

## Forecast template

| Stage | Model | Conditions | Chains | Generations | Estimated accelerator-hours | Storage | Basis of estimate | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| Positive control | GPT-2 124M (`openai-community/gpt2`) | 2 | 1 seeded chain per arm | 11 (indices 0–10) | ~10–40 T4-hours (estimate, wide) | ~12–15 GB | Formula estimate from the pinned upstream config; decoding, not training, dominates. **Still not the measured one-generation smoke run this column requires.** See `docs/benchmarks/khantushig_week2.md` §4 | Estimated, not measured; unexecuted |
| Mechanism pilot | 160M-class | TBD | At least 5 initial | 10 | TBD | TBD | Positive-control and smoke-run measurements | Blocked |
| Powered core | 410M/1B-class | TBD | Power result | 10+ | TBD | TBD | Pilot measurements | Blocked |
| Independent confirmation | TBD | Decisive contrast only | TBD | TBD | TBD | TBD | Powered-core measurements | Blocked |

Forecasts must state assumptions and may not be presented as actual usage.

## Actual usage template

| Run ID | Date | Commit | Model revision | Hardware | Count | Wall time | Accelerator-hours | Peak memory | Storage written | Outcome |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| None | — | — | — | — | — | — | — | — | — | No experimental runs yet |
| `week2-infrastructure` | 2026-08-03 | `week-2/khantushig-positive-control` | n/a — no model loaded | 4 vCPU x86_64, **no GPU** | 1 | 3.78 s (full test suite) | **0.00** | 40.4 MiB | ~90 KiB (source, configs, tests, docs) | Infrastructure only. No model trained, no accelerator used. Not an experiment. |
| `positive_control_fully_synthetic_seed42` | — | — | — | — | 0 | — | — | — | — | **Not executed** — no accelerator available; see `docs/positive_control/failure_report.md` |
| `positive_control_human_mixed_seed42` | — | — | — | — | 0 | — | — | — | — | **Not executed** — no accelerator available; see `docs/positive_control/failure_report.md` |

## Required accounting

For each paper experiment, report:

- accelerator model and memory;
- number of devices;
- wall time and accelerator-hours;
- CPU, RAM, and storage where material;
- per-run and total reported-study compute;
- preliminary and failed-run compute separately;
- generation, training, and evaluation compute separately when measurable.

## Compute gate

The powered experiment may begin only when observed pilot variance and measured runtime imply a feasible design. If compute is insufficient, narrow the research claim or strengthen the theory-led path; do not replace powered independent chains with a larger unpowered condition grid.
