# Compute Ledger

> **No experimental compute has been recorded for this repository.**

This file separates forecasts from actual usage.

## Forecast template

| Stage | Model | Conditions | Chains | Generations | Estimated accelerator-hours | Storage | Basis of estimate | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| Positive control | GPT-2 124M-class | 2 | TBD | 10 | TBD | TBD | Must be measured from one-generation smoke run | Not estimated |
| Mechanism pilot | 160M-class | TBD | At least 5 initial | 10 | TBD | TBD | Positive-control and smoke-run measurements | Blocked |
| Powered core | 410M/1B-class | TBD | Power result | 10+ | TBD | TBD | Pilot measurements | Blocked |
| Independent confirmation | TBD | Decisive contrast only | TBD | TBD | TBD | TBD | Powered-core measurements | Blocked |

Forecasts must state assumptions and may not be presented as actual usage.

## Actual usage template

| Run ID | Date | Commit | Model revision | Hardware | Count | Wall time | Accelerator-hours | Peak memory | Storage written | Outcome |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| None | — | — | — | — | — | — | — | — | — | No runs yet |

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
