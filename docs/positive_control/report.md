# Positive control: reproduction report

**Date:** 2026-08-07
**Branch:** `week-2/khantushig-positive-control`
**Stage:** A (published positive control)
**Decision:** `valid_with_limitation`
**Upstream:** `GeorgeDrayson/model_collapse` @ `feb8511479a2e2dc868e1caf3f63cb99f1fcc746`
**Paper:** Drayson, Yilmaz & Lampos, EMNLP 2025 (`2025.emnlp-main.1506`)

## 1. What this report claims

**Claim.** The published positive control reproduces qualitatively. Recursive training on
a model's own output degrades GPT-2 on WikiText-2, and retaining human data in the training
mixture very largely prevents that degradation. Over 11 generations the fully synthetic arm
(α=0) went from perplexity 29.6179 to 50.9806, a degradation ratio of **1.7213**. The
human-mixed arm (α=1) went from the same baseline to 30.3730, a ratio of **1.0255**. All
four frozen ordering claims hold.

**Not claimed.** That the observed numbers match the paper's published numbers. That
comparison was never performed, because the published values could not be obtained (§3).
The reproduction is qualitative — direction and ordering — not numeric.

**Also not claimed.** That the recorded artifact hashes can be verified. They cannot; the
bytes are gone (§5).

## 2. Result

| Generation | Fully synthetic (α=0) | Human mixed (α=1) |
|---:|---:|---:|
| 0 | 29.6179 | 29.6179 |
| 1 | 33.3270 | 29.9270 |
| 2 | 36.0927 | 30.1084 |
| 3 | 38.3351 | 30.2194 |
| 4 | 40.3849 | 30.2904 |
| 5 | 42.3133 | 30.3224 |
| 6 | 44.1144 | 30.3292 |
| 7 | 46.0498 | 30.3426 |
| 8 | 47.6450 | 30.3628 |
| 9 | 49.4601 | 30.3579 |
| 10 | **50.9806** | **30.3730** |

| Quantity | Fully synthetic | Human mixed |
|---|---|---|
| Degradation ratio `ppl₁₀ / ppl₀` | 1.7213 | 1.0255 |
| `eval_loss` at generation 10 | 3.9314 | 3.4136 |
| `eval_accuracy` at generation 10 | 0.3254 | 0.3838 |

The two arms share generation 0 by construction, so the 29.6179 baseline is one number
computed once, not two that happen to agree. The arms diverge from generation 1 onward and
never re-cross: the synthetic arm is above the mixed arm at all ten subsequent generations.

Against the criteria frozen on 2026-08-03, before either arm ran:

| Frozen claim | Observed | Verdict |
|---|---|---|
| `ratio(fully_synthetic) > 1.0` | 1.7213 | holds |
| `ratio(human_mixed) > 1.0`, strictly below the synthetic arm | 1.0255 < 1.7213 | holds |
| `ratio(fully_synthetic) > ratio(human_mixed) > 1.0` | 1.7213 > 1.0255 > 1.0 | holds |
| Synthetic ≥ mixed for the majority of generations 1–10 | 10 of 10 | holds |

Full ledger: `expected_vs_observed.md`. Per-generation artifacts: `measurements/`.

## 3. Why this is `valid_with_limitation` and not `valid`

The 5% engineering tolerance was never applied, because the numbers to apply it against
were never obtained. `aclanthology.org` is blocked by the authoring environment's network
egress policy, so the paper's reported perplexities could not be read. No value was
invented, estimated, or reconstructed from memory to fill the gap.

This was recorded as an open item on 2026-08-03 (`FAILURE_LOG.md` `PC-2026-08-03-B`),
which stated in advance that a run completed while it remained open "could reach at most
`valid_with_limitation`". This run is that case. The limitation is pre-registered, not a
retrofit.

The frozen decision table anticipated the band being tested and either met or missed — not
untestable. That gap is resolved conservatively: recording `valid` would assert a numeric
agreement nobody checked.

**To upgrade:** obtain the published values, fill `expected_vs_observed.md` §2.2 with exact
figure/table citations, and compare against the endpoints in §2 above. No rerun is needed
or permitted — the observed numbers are fixed and committed. If the comparison falls
outside 5%, the decision stays `valid_with_limitation` on different grounds (a stated
numeric miss) and the ordering result is unaffected either way.

## 4. How it was run

| Item | Value |
|---|---|
| Model | `openai-community/gpt2` @ `607a30d783dfa663caf39e06633721c8d4cfcd7e` |
| Dataset | WikiText-2 raw v1 @ `b08601e04326c79dfdd32d625aee71d232d685c3` |
| Detector | `GeorgeDrayson/modernbert-ai-detection` @ `08f218f1d05791ad99c26ede421f69c781a50360` |
| Prepared `train.json` | `68a59c04e937e502…` (see `PC-2026-08-06-F` for why this is per-session) |
| Stack | `transformers 4.48.3`, `datasets 3.2.0`, `accelerate 1.2.1` |
| Host | Kaggle Notebooks, 2× Tesla T4, one arm per GPU |
| Seed | 42 |
| Horizon | 11 generations, indices 0–10 |
| Decoding | top-k, `k=50`, `temperature=1.0`, `top_p=1.0` |
| Data selection | `no-selection` (deviation 1) |
| Training wall time | 2.99 h synthetic + 5.57 h mixed = 8.57 h, summed from `train_results.json` |

`transformers` is unpinned upstream; 4.48.3 is this project's resolution of that ambiguity,
forced by upstream's own `check_min_version("4.48.0.dev0")` (`PC-2026-08-05-D`).

Both arms ran through `scripts/run_positive_control_arm.py`, which issues upstream's exact
`train.py` and `generate.py` commands one generation at a time so a session-capped host can
resume. The argument lists are pinned by test against upstream `main.py`. Eleven deviations
from upstream are enumerated in `expected_vs_observed.md` §6; the two that affect what was
computed are `data_selection=no-selection` (deliberate — importance sampling is the paper's
mitigation, not the collapse baseline) and the shared generation 0.

## 5. Limitation: artifacts hashed but not retained

Every generation's model checkpoint and generated corpus was hashed by the driver the
moment that generation completed, and those hashes are committed. **The bytes are gone.**
The run executed in an ephemeral Kaggle container that was reclaimed at session end, before
anything but the metrics had been copied out. 42 artifacts were lost — 22 model directories
and 20 generated corpora.

This was not pruning. `--prune-models` was never passed; every `artifact_record.json`
records `pruned: false`, which was true when it was written. The records were not
retro-edited to say otherwise. The inventory is in `measurements/artifact_retention.json`
and the incident is `FAILURE_LOG.md` `PC-2026-08-07-H`.

What this costs:

- **Nothing on the reported result.** All 22 `eval_results.json` files survived and are the
  source of every number above.
- **`verify_recorded_hashes` cannot be run** against this execution. The hashes are evidence
  of what was produced, not a check anyone can re-run.
- **No qualitative sample survives.** There is no generation-10 synthetic text to show
  beside the perplexity curve.

The metrics survived only because an auto-push monitor was committing each generation as it
completed. Any future run on an ephemeral host must mirror artifacts incrementally.

## 6. Unresolved discrepancy: wandb suppression

`FAILURE_LOG.md` `PC-2026-08-05-E` records that upstream crashes at `train.py:683` because
`main.py:25` guards `wandb.init` with `bool(str(cfg.wandb_disabled))` — always truthy — so
init never runs while `wandb.log` is called unconditionally. That entry states that setting
`WANDB_DISABLED` and `WANDB_MODE=disabled` does **not** prevent the crash, because wandb's
pre-init stub raises regardless of mode, and a `sitecustomize.py` shim was written to
perform the disabled-mode init.

The driver committed on this branch, which ran all 22 generation-arm pairs to completion,
contains **only the environment variables**. It has no shim.

Both facts are recorded and neither is deleted to make the other consistent. The likely
explanations are that the shim was present in the executing checkout but not in the
committed file, or that the installed wandb version tolerates the env-var path where the
version behind `PC-2026-08-05-E` did not. **Which one is true has not been established**,
and it is not asserted here.

Consequence for the result: none. wandb logging is dashboard reporting and touches no
scientific computation; every generation's metrics were written and recorded. Consequence
for reproduction: someone repeating this must be prepared for the crash and should apply
the shim if it occurs.

## 7. Effect on downstream stages

`PROTOCOL.md` §4 blocks Stage B until Stage A and the invariant tests pass. Stage A has now
completed with decision `valid_with_limitation`, and the suite passes (178 passed, 1
skipped).

**Stage B is unblocked**, subject to two conditions carried forward:

1. The positive control's agreement with the published result is qualitative only (§3).
   Any Stage B claim resting on numeric agreement with the paper is not supported.
2. The tail-retention measure Stage B needs does not exist yet.
   `positive_control_adapter.build_chain_result` still refuses to emit a `ChainResult`
   rather than fill `tail_retention` with a sentinel (`expected_vs_observed.md` §7). Stage A
   reports through `positive_control_result.json` instead.

## 8. Superseded document

`failure_report.md` documented Stage A as blocked and stated that this report "does not
exist and must not be created until a run actually completes". A run has now completed. That
document is retained, not deleted — `FAILURE_LOG.md` is append-only and the block it
describes genuinely happened — and is marked superseded at its head.
