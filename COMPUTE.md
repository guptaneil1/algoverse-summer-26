# Compute Ledger

> **Stage A executed 2026-08-06/07.** Measured usage is in "Actual usage" below. Every
> later stage remains a forecast.

This file separates forecasts from actual usage.

## Forecast template

| Stage | Model | Conditions | Chains | Generations | Estimated accelerator-hours | Storage | Basis of estimate | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| Positive control | GPT-2 124M (`openai-community/gpt2`) | 2 | 1 seeded chain per arm | 11 (indices 0–10) | ~10–40 T4-hours (estimate, wide) | ~12–15 GB | Formula estimate from the pinned upstream config; decoding, not training, dominates. See `docs/benchmarks/khantushig_week2.md` §4 | **Superseded by measurement.** Actual: 19.0 T4-hours, inside the forecast band but in its upper half. |
| Mechanism pilot | 160M-class | TBD | At least 5 initial | 10 | TBD | TBD | Positive-control and smoke-run measurements | Blocked |
| Powered core | 410M/1B-class | TBD | Power result | 10+ | TBD | TBD | Pilot measurements | Blocked |
| Independent confirmation | TBD | Decisive contrast only | TBD | TBD | TBD | TBD | Powered-core measurements | Blocked |

Forecasts must state assumptions and may not be presented as actual usage.

## Actual usage template

| Run ID | Date | Commit | Model revision | Hardware | Count | Wall time | Accelerator-hours | Peak memory | Storage written | Outcome |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `positive_control_fully_synthetic_seed42` | 2026-08-06/07 | `feb8511` upstream | `607a30d7…` | 1× Tesla T4 (of 2; one arm per GPU) | 11 generations | ~8.26 h | ~8.3 | not recorded | not retained (see below) | **Completed.** ppl 29.6179 → 50.9806, ratio 1.7213. `docs/positive_control/report.md` |
| `positive_control_human_mixed_seed42` | 2026-08-06/07 | `feb8511` upstream | `607a30d7…` | 1× Tesla T4 (of 2; one arm per GPU) | 11 generations | ~10.76 h | ~10.8 | not recorded | not retained (see below) | **Completed.** ppl 29.6179 → 30.3730, ratio 1.0255. `docs/positive_control/report.md` |
| `week2-infrastructure` | 2026-08-03 | `week-2/khantushig-positive-control` | n/a — no model loaded | 4 vCPU x86_64, **no GPU** | 1 | 3.78 s (full test suite) | **0.00** | 40.4 MiB | ~90 KiB (source, configs, tests, docs) | Infrastructure only. No model trained, no accelerator used. Not an experiment. |

### How the Stage A numbers were obtained, and what is missing

Read these caveats before quoting the table.

- **Wall time and accelerator-hours are derived from commit timestamps**, not from a timer.
  Each generation was committed by an auto-push monitor as it completed, so the span from
  the shared generation 0 commit (2026-08-06T17:26:43Z) to each arm's generation 10 commit
  is a close upper bound on that arm's wall time — it includes up to five minutes of
  monitor polling latency per generation. Both arms ran concurrently on separate GPUs, so
  the session's wall clock was 10.76 h while the accelerator total was ~19.0 T4-hours.
- **Training time alone is measured exactly**, from `train_results.json`: 2.99 h synthetic
  + 5.57 h mixed = 8.57 h. The remaining ~10.4 accelerator-hours is decoding, dataset
  preparation, and detector inference. Decoding dominating training is what the forecast
  predicted.
- **Peak memory was not recorded.** The measurement cell that would have captured it did
  not survive the session. Each arm ran within a 14.56 GiB T4 alongside the ModernBERT
  detector, and both arms on one card exhausted it (`FAILURE_LOG.md` `PC-2026-08-06-G`),
  which brackets per-arm peak between roughly 6 and 14.5 GiB — a bracket, not a
  measurement.
- **Storage written was not recorded and the artifacts are gone.** The container was
  reclaimed at session end (`PC-2026-08-07-H`). Only metrics were mirrored out. From
  checkpoint sizes seen during the run (~254 MB per model, 22 models) the models alone
  were ~5.6 GB, with the generated corpora on top; the forecast's ~12–15 GB is consistent
  with that but is not confirmed.

The forecast row is left in place rather than overwritten, so the estimate and the
measurement can be compared.

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
