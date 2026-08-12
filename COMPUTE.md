# Compute Ledger

> **No experimental compute has been recorded for this repository.**

This file separates forecasts from actual usage.

## Forecast template

| Stage | Model | Conditions | Chains | Generations | Estimated accelerator-hours | Storage | Basis of estimate | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| Positive control | GPT-2 124M-class | 2 | TBD | 10 | TBD | TBD | Must be measured from one-generation smoke run — blocked on upstream commit pin, ML framework, and accelerator access; see `docs/benchmarks/khantushig_week1.md` | Not estimated |
| Mechanism pilot | 160M-class | TBD | At least 5 initial | 10 | TBD | TBD | Positive-control and smoke-run measurements | Blocked |
| Powered core | 410M/1B-class | TBD | Power result | 10+ | TBD | TBD | Pilot measurements | Blocked |
| Independent confirmation | TBD | Decisive contrast only | TBD | TBD | TBD | TBD | Powered-core measurements | Blocked |

Forecasts must state assumptions and may not be presented as actual usage.

## Actual usage template

| Run ID | Date | Commit | Model revision | Hardware | Count | Wall time | Accelerator-hours | Peak memory | Storage written | Outcome |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `fixture_joint_seed1` (toy) | 2026-08-12 | `claude/week-3-assignments-boq852` | none — toy path, no model | CPU only, no accelerator | 1 | 0.07 s | 0 | 18.2 MB RSS | 32 kB | Fixture; certifies `valid`. **Not scientific evidence** |

**No primary chain compute has been recorded on this branch.** The row above is the
toy CPU smoke chain, measured so the fixture cost is not mistaken for zero; it uses
no accelerator and no model, and generation/training/evaluation are not separable in
the toy path because none of the three is real.

The positive-control compute **was** measured — on
`week-2/khantushig-positive-control`, which is unmerged. Those measurements are not
restated here; see `docs/audits/week2_merge_gap.md` for what lives where.

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
