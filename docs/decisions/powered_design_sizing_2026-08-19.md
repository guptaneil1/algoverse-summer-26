# Powered experiment sizing — the compute gate's input

**Date:** 2026-08-19
**Status:** Derived from measurement. Releases the input the compute gate was waiting on;
does **not** authorise the powered run, which remains an owner decision.
**Source:** `results/runs/primary_pilot_2026-08-18/`, 25 chains, all measured this session.

`COMPUTE.md`'s compute gate reads:

> The powered experiment may begin only when observed pilot variance and measured runtime
> imply a feasible design. If compute is insufficient, narrow the research claim or
> strengthen the theory-led path; do not replace powered independent chains with a larger
> unpowered condition grid.

Both inputs now exist. This document supplies them and the design they imply.

## Variance

Between-chain variance is estimated from the **budget-matched arms only**. `joint` is
excluded throughout: F-020 left it spending 10.1% less than the others, so its paired
differences carry a data-quantity term and would understate or overstate the noise
unpredictably.

Paired-by-seed differences in the primary outcome, five seeds:

| pair | paired SD |
|---|---|
| `random` vs `schedule_only` | 0.02972 |
| `random` vs `selection_only` | 0.01884 |
| `schedule_only` vs `selection_only` | 0.02472 |

**Conservative estimate: 0.02972**, the largest of the three. Sizing on the largest rather
than the mean means the design is not undersized if the joint contrast turns out noisier
than the pairs measured here.

Reference baseline (mean AUC regret for `random`): **2.52454**. The preregistered 2%
practical threshold is therefore **0.05049** in outcome units.

## Chains required

Paired design, 80% power, two-sided α = 0.05, using the conservative SD above:

| smallest effect to detect | relative | chains per arm |
|---|---|---|
| 0.05049 | 2.0% (preregistered) | **3** |
| 0.02525 | 1.0% | 11 |
| 0.01262 | 0.5% | 44 |
| 0.00505 | 0.2% | 272 |

**The frozen five-seed set already exceeds what the preregistered threshold requires.**
This is the pilot's substantive finding and it inverts the design assumption: chain count
was expected to be the binding constraint and is not.

## Runtime and cost

Measured: the longest shard ran **6.75 h** over 7 chains — **57.9 min per chain** — on a
4× RTX 4090 pod at an observed **$3/hour**. Cost figures below use that rate, which was
observed once and is not a quoted price.

| seeds/arm | chains | rounds on 4 GPUs | wall time | cost |
|---|---|---|---|---|
| 5 (2%) | 25 | 7 | 6.8 h | ~$20 |
| 11 (1%) | 55 | 14 | 13.5 h | ~$40 |
| 44 (0.5%) | 220 | 55 | 53.0 h | ~$159 |

Adding accelerators buys wall time, not budget: GPU-hours are roughly constant, so the 1%
design costs about $40 whether it runs 13.5 h on four GPUs or 6.8 h on eight.

## What this implies

**A design powered at the preregistered threshold is affordable.** Re-running the frozen
grid with F-020 fixed costs about $20 and 6.8 hours, and at the measured variance that is
already a powered test of C-002 at 2%, not merely a pilot.

That is the recommendation this evidence supports: **re-run the frozen grid rather than
design a larger one.** Enlarging to 11 seeds would buy detection down to 1% for roughly
double the cost, which is only worth it if the team judges effects between 1% and 2%
scientifically interesting — a question for the U-006 statistics review, not for this
document.

## What this does not do

- **It does not authorise the run.** The gate says the powered experiment *may* begin when
  a feasible design exists. Whether to begin is an owner decision.
- **It does not settle the threshold.** Every row scales with the 2% figure, which P-007
  adopted as a stopgap and which the U-006 review has never examined. A threshold change
  moves the whole table.
- **It does not cover C-003.** The monitoring-bias intervention is a separate design with
  its own arms and is not sized here.
- **It assumes the pilot's variance transfers.** Measured at one budget, one horizon, one
  corpus and one model. A powered run at different settings should re-estimate.

## Reproduction

Every number above is computed from `chain_result.json` files under
`results/runs/primary_pilot_2026-08-18/` and from `wall_seconds` in the shard summaries.
Nothing is estimated or carried over from a prior document; the two figures this project
previously carried by estimate (P-004's cost, P-005's token projection) were both
contradicted by measurement, which is why this one states its source for each quantity.
