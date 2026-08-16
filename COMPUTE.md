# Compute Ledger

> **No experimental compute has been recorded for this repository.**

This file separates forecasts from actual usage.

## Forecast

**Every number in this section is an ESTIMATE derived from public artifact sizes and a stated
throughput model. None of it is measured usage.** It exists to answer "what should we ask for?"
before an accelerator is available. Replace each row with measured values after the first real
generation; §Assumptions records exactly what would invalidate these figures.

| Stage | Model | Conditions | Chains | Generations | Est. accelerator-hours | Est. storage | Basis | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| Positive control | GPT-2 124M | 2 arms | 2 | 10 | **1.5–7.5** | **30–40 GB** | Assumptions A1–A6, corpus `wikitext2` | ESTIMATE |
| Mechanism pilot | 124M–160M | 6 policies | 5 paired seeds (30 chains) | 10 | **25–115** | **450–600 GB** | Positive control scaled 15× by chain count | ESTIMATE |
| Powered core | 410M/1B-class | Non-dominated set | Power result | 10+ | Not estimated | Not estimated | Requires pilot variance | Blocked |
| Independent confirmation | TBD | Decisive contrast only | TBD | TBD | Not estimated | Not estimated | Requires powered-core measurements | Blocked |

### Derivation of the positive-control estimate

**Corpus size.** `wikitext-2-raw-v1` reports 36,718 train rows and 13.54 MB generated dataset size
across all splits (Hugging Face dataset card, retrieved 2026-08-15). At roughly 4 bytes per GPT-2
BPE token for English prose, the train split is on the order of **2.5–3.0 M tokens**. This is the
dominant uncertainty and is the first quantity to replace with a measured tokenized length.

**Training cost is not the bottleneck.** Using the standard `6 · N · D` training-FLOP
approximation with N = 124 M parameters and D ≈ 2.5 M tokens gives about **1.9 × 10¹⁵ FLOPs per
epoch**. On an accelerator delivering an effective 50–100 TFLOP/s in bfloat16 for a model this
small, that is well under a minute of pure training per generation.

**Generation is the bottleneck.** Each recursive generation must autoregressively decode a
synthetic corpus of comparable size under top-k sampling. Decoding is memory-bandwidth bound and
does not reach training throughput. At an assumed 2,000–10,000 generated tokens/second batched,
producing ~2.5 M tokens takes **4–20 minutes per generation**.

Across 10 generations and 2 arms that is 80–400 minutes, or **1.3–6.7 hours of decoding**. Adding
training (under a minute per generation) and detector inference (A5, under 10% of total) gives the
**1.5–7.5 hour** band in the table. The pilot row scales this by its 15× chain count.

**Detector cost.** Upstream scores candidates with a ModernBERT-base classifier under importance
sampling — one forward pass per example, small relative to decoding. Assume **under 10%** of total
and verify. (Upstream's README describes the detector as 150M-parameter; that is upstream's figure,
not one measured here — see `docs/evidence/upstream_pin.md` §3.)

**Storage.** A 124 M-parameter checkpoint is roughly 250 MB in bfloat16 and 500 MB in fp32; with
optimizer state, budget **~1.5 GB per retained checkpoint** (A6). Retaining every generation of
both arms is 1.5 GB × 10 generations × 2 arms = **30 GB of checkpoints alone**; generated corpora
and logs take the band to **30–40 GB**.

**Storage, not compute, is what scales badly.** At 30 pilot chains retaining all 10 generations,
the requirement reaches several hundred GB. Fix the checkpoint retention policy *before* launching
the pilot: keeping only generations 0, 5, and 9 cuts this by roughly two thirds, but that rule must
be recorded in `PROTOCOL.md` first, because it constrains which resume-equivalence tests remain
possible afterwards.

### Assumptions

| ID | Assumption | Invalidated if |
|---|---|---|
| A1 | wikitext-2 train ≈ 2.5–3.0 M GPT-2 BPE tokens | Measured tokenized length differs by more than ~25% |
| A2 | One epoch per recursive generation | Upstream config specifies multiple epochs per iteration |
| A3 | Effective 50–100 TFLOP/s bf16 for a 124M model | Older accelerator, no bf16 support, or severe underutilization |
| A4 | Generation throughput 2,000–10,000 tok/s batched | Unbatched decoding, long sequences, or CPU fallback |
| A5 | Detector inference under 10% of total | Detector re-scores the full corpus every generation |
| A6 | ~1.5 GB retained per checkpoint including optimizer state | fp32 checkpoints or separately retained optimizer state |
| A7 | Pilot cost scales linearly in chain count from the positive control | Larger corpus or larger model changes the base unit |

**A7 is the weakest assumption.** The pilot is planned on WikiText-103, roughly 40× larger than
wikitext-2 by generated size (549.42 MB vs 13.54 MB). If the pilot consumes the full corpus rather
than a frozen subsample, the pilot row above is low by more than an order of magnitude. Subsample
size is a Neil/Aarav decision (U-002, U-003) and must be fixed before that row means anything.

### What to measure first

One command settles most of this: run **a single generation of one arm** and record tokenized
corpus length, wall time split across train / generate / detect / evaluate, peak memory, and bytes
written. Every band above then collapses to a measured multiple. Until that runs, treat these
figures as a procurement request, not a plan.

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
