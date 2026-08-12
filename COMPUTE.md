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
| `fixture_joint_seed1` (toy) | 2026-08-12 | `week-3/khantushig-reference-runs` | none — toy path, no model | CPU only, no accelerator | 1 | 0.07 s | 0 | 18.2 MB RSS | 32 kB | Fixture; certifies `valid`. **Not scientific evidence** |
| `positive_control_fully_synthetic_seed42` | 2026-08-06/07 | upstream `feb8511` | `607a30d7…` | 1× Tesla T4 | 11 gens | ~8.26 h | ~8.3 | not recorded | not retained | **Completed.** ppl 29.6179 → 50.9806, ratio 1.7213 |
| `positive_control_human_mixed_seed42` | 2026-08-06/07 | upstream `feb8511` | `607a30d7…` | 1× Tesla T4 | 11 gens | ~10.76 h | ~10.8 | not recorded | not retained | **Completed.** ppl 29.6179 → 30.3730, ratio 1.0255 |
| `week2-infrastructure` | 2026-08-03 | `week-2/khantushig-positive-control` | none — no model loaded | 4 vCPU, no GPU | 1 | 3.78 s | **0.00** | 40.4 MiB | ~90 kB | Infrastructure only. Not an experiment |

**No primary chain compute has been recorded.** The row above is the toy CPU smoke
chain, measured so the fixture cost is not mistaken for zero; it uses no accelerator
and no model, and generation/training/evaluation are not separable in the toy path
because none of the three is real.

## Positive control — generation, training, and evaluation separately

Source: `week-2/khantushig-positive-control` (PR #16, merged into
`integration/week-2-jul25-jul31`). Both arms, GPT-2 124M on WikiText-2, 11
generations each, one Tesla T4 per arm running concurrently.

| Arm | Training | Evaluation | Generation | Arm total | Basis |
|---|---:|---:|---:|---:|---|
| `positive_control_fully_synthetic_seed42` | **2.99 h** | **0.14 h** | ~5.13 h | ~8.26 h | train/eval measured; generation residual |
| `positive_control_human_mixed_seed42` | **5.57 h** | **0.13 h** | ~5.05 h | ~10.76 h | same |
| **Total** | **8.56 h** | **0.27 h** | ~10.18 h | **~19.0 T4-hours** | |

**How each column was obtained, and how far to trust it:**

- **Training and evaluation are measured.** Summed from the `train_runtime` and
  `eval_runtime` fields the HuggingFace trainer wrote into each generation's
  `train_results.json` and `eval_results.json` — 11 generations per arm, all
  committed to git. These are timer values, not estimates.
- **Generation is a residual**, computed as arm total − training − evaluation.
  There is no decode timer in the upstream artifacts, so this column inherits all
  the uncertainty in the arm total.
- **Arm totals derive from commit timestamps, not a timer.** Each generation was
  committed by an auto-push monitor as it completed, so the span from the shared
  generation-0 commit to each arm's generation-10 commit is a close *upper bound*,
  including up to five minutes of monitor polling latency per generation. Treat the
  generation column as accurate to roughly ±1 h, not to two decimals.

Two things support the residual despite that. Generation lands at ~5.1 h on both
arms independently, which is what a fixed decode workload should cost — the arms
decode the same sample count and differ only in training mixture. And it is
consistent with `docs/benchmarks/kaggle_smoke_test_runbook.md` §0.5, which predicted
before the run that decoding, not training, would dominate cost. That prediction
holds for the synthetic arm (5.13 h vs 2.99 h) and inverts for the human-mixed arm
(5.05 h vs 5.57 h), because α=1 appends the full human train split to every
generation and roughly doubles its training set.

**Aborted-run cost:** none recorded. Neither arm was aborted and restarted.

**Peak memory:** not recorded — the sampler in runbook §5 was not run during the
full arms. **Storage:** ~12–15 GB peak with pruning enabled; not retained (see
`docs/positive_control/week3_verification.md` §6).

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
