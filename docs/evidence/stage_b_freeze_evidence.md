# Stage B freeze — evidence package

**Purpose:** supply the evidence that `DECISIONS.md` U-001, U-003, and U-004b were waiting
on, so the July 31 design freeze can be made. **This document decides nothing.** U-001 and
U-003 are Aarav's calls per `DECISIONS.md`; U-002 is Neil's. Every value below was read from
a committed artifact of the 2026-08-17 Stage A execution or computed from one, in that
session.

**Status of the freeze:** all three primary configurations remain `AWAITING_JULY_31_FREEZE`.
`scripts/run_chain.sh` refuses them, correctly, until every `_required_from_freeze` field is
set and `_freeze_status` reads `FROZEN`.

## U-001 — continued fine-tuning or controlled from-scratch training?

**Evidence needed** (per `DECISIONS.md`): positive-control behavior, compute forecast, claim
scope. All three now exist.

**Observed behavior.** Every one of the 11 generations, in both arms, invokes upstream
`train.py` with `--model_name_or_path openai-community/gpt2`. The previous generation's
checkpoint appears only as `generate.py --model_path .../N/model/final_model`, producing
that generation's synthetic corpus. No generation resumes optimization from the previous
generation's weights.

**What that means.** The published positive control this project takes as its reference does
**not** use continued fine-tuning. Each generation fine-tunes the pretrained base on data
produced by the previous generation. Collapse in that setting is transmitted entirely
through the data distribution, not through accumulated weight drift.

**Consequence for the decision, stated without making it.** If Stage B uses continued
fine-tuning, it departs from the regime under which the positive control was validated, and
the positive control stops covering the pilot's training path. If Stage B matches upstream
and retrains from base each generation, the validation carries over, and `--prune-models`
remains sound because a checkpoint is spent once the next generation's data exists.

This is a scope question, not a performance one. Either regime is defensible; only one of
them is covered by the evidence now in hand.

## U-003 — exact lifetime budgets

**Evidence needed:** positive-control token accounting and screening feasibility. Both now
exist.

### Token accounting (measured)

| Arm | Per generation | Lifetime optimizer-consumed |
|---|---:|---:|
| `fully_synthetic` | 2,390,528 | 26,295,808 |
| `human_mixed` | 2,390,528 at gen 0; 4,781,056 thereafter | 50,201,088 |

Computed as `train_samples` x `block_size` (512) from the committed `train_results.json`
files — tokenized blocks actually consumed by the optimizer, per `PROTOCOL.md` §3.

The arm configs' `planned_estimate` values (26,400,000 total and 2,400,000 human) are each
within 0.4% of measurement. The estimate's basis is confirmed for WikiText-2.

### Screening feasibility (measured)

One RTX 4090, native bf16: `fully_synthetic` ~0.70 h, `human_mixed` 0.8236 h, ~1.52 h for
both arms. The earlier T4 execution consumed ~19.0 accelerator-hours for the same work.

### The corpus-scale question, which dominates everything else

`COMPUTE.md` forecasts the pilot at 15x the positive control by chain count. Applied to the
measured figure rather than the T4-era estimate:

| Pilot corpus scale | Est. accelerator-hours | Est. cost at $0.74/h |
|---|---:|---:|
| WikiText-2 scale (~2.4M tokens/generation) | ~23 | ~$17 |
| Full WikiText-103 (~40x by generated size) | ~900 | ~$675 |

`COMPUTE.md` assumption A7 already flags this as its weakest link. The arithmetic above puts
a number on it: **the subsample decision is worth roughly 40x the entire remaining budget.**

At a working budget near $23, a pilot at approximately WikiText-2 token scale fits with
little margin, and a full-corpus pilot does not fit by more than an order of magnitude. That
is a constraint on U-002 and U-003 jointly, and it is the single highest-leverage decision
remaining.

Storage scales the same way. `COMPUTE.md` forecasts 450-600 GB for the pilot; pruning cut
Stage A from ~11 GB to ~1.5 GB, so a retention policy must be fixed before launch, and
`PROTOCOL.md` must record it first because it constrains which resume-equivalence tests
remain possible afterwards.

## U-004b — exact `nll_threshold_candidate`

**Evidence needed:** baseline NLL distribution on the validation partition from a real
generation-0 model. **Still missing**, and it is the cheapest gap on this list.

A generation-0 model existed during the 2026-08-17 run and was deleted by `--prune-models`
before any validation-partition NLL distribution was extracted. Regenerating it is one
training invocation: roughly 50 seconds of accelerator time.

The metric *choice* is already frozen (`docs/evaluation/tail_retention_freeze.md`,
ratio-based `tail_retention`, primary). Only the numeric threshold is open.

## What this package does not supply

- **U-002** (final licensed domain) — Neil's, with a written recommendation already in
  `docs/evidence/domain_audit.md`. The cost table above bears directly on it.
- **U-005** (final contribution type) — requires human judgment about theorem strength versus
  empirical evidence.
- **U-006** (smallest scientifically meaningful effect) — requires the mentor and statistics
  review named in `DECISIONS.md`. No artifact substitutes for it.

## What this package does not establish

It does not establish that Stage B should run, that any budget is correct, or that any
regime is preferable. It establishes that U-001 and U-003 now have the evidence their
`DECISIONS.md` rows named, and that U-004b is one short job away from having its own.
