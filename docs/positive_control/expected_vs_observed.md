# Positive control: expected versus observed

**Status: EXPECTED SIDE FROZEN 2026-08-03. OBSERVED SIDE COLLECTED 2026-08-06/07.
Decision: `valid_with_limitation`.**

This document is the comparison ledger for Stage A. The expected column and the decision
rule below were frozen on **2026-08-03**, before either arm was executed, and are
governed by `PROTOCOL.md` §2. Both arms completed all 11 generations on 2026-08-07; the
observed column below is filled from their saved artifacts.

The limitation is §2.2 and it is unchanged: the published numeric values were never
obtainable, so the qualitative ordering criterion was evaluated and the 5% numeric band
was not. That was recorded as an open item *before* the run (`FAILURE_LOG.md`
`PC-2026-08-03-B`), not discovered afterwards.

No value in the observed column was filled in by hand. Every number below is read from
the committed artifacts under `measurements/`, and the two `summary.json` files were
produced by `positive_control_adapter.summarize` over
`positive_control_adapter.read_eval_results`.

## 1. What is being compared

| Item | Frozen value | Source |
|---|---|---|
| Upstream repository | `https://github.com/GeorgeDrayson/model_collapse` | `PROTOCOL.md` §2 |
| Upstream commit | `feb8511479a2e2dc868e1caf3f63cb99f1fcc746` | resolved 2026-08-03 |
| Paper | Drayson, Yilmaz & Lampos, EMNLP 2025 (`2025.emnlp-main.1506`) | upstream `README.md` |
| Model | `openai-community/gpt2` | `config/model/gpt2.yaml` |
| Dataset | WikiText-2 raw v1 | `config/dataset/wikitext2.yaml` |
| Horizon | 11 generations, indices 0–10 | `config/config.yaml` (`num_iterations: 10`) |
| Seed | 42 | `config/config.yaml` |
| Primary endpoint | Test perplexity at generation 10 | `PROTOCOL.md`, "Frozen endpoint, ordering, and tolerance" |
| Paired quantity | Degradation ratio `perplexity_10 / perplexity_0` | same |
| Tolerance | 5% relative, **engineering only** | same |

## 2. Expected

### 2.1 Ordering (the primary criterion)

| Claim | Frozen expectation |
|---|---|
| Fully synthetic arm degrades | `degradation_ratio(fully_synthetic) > 1.0` |
| Human-mixed arm degrades less | `degradation_ratio(human_mixed) > 1.0` and strictly below the synthetic arm |
| Combined ordering | `degradation_ratio(fully_synthetic) > degradation_ratio(human_mixed) > 1.0` |
| Not a single-generation artifact | The fully-synthetic curve sits at or above the human-mixed curve for the majority of generations 1–10 |

This qualitative ordering — recursive training on model output degrades a model, and
retaining human data slows that degradation — is the result the positive control exists
to recover. It is the criterion that decides pass or fail.

### 2.2 Numeric expected values — OPEN ITEM

| Quantity | Expected value | Source location | Status |
|---|---|---|---|
| `perplexity_0` (both arms) | *not yet extracted* | paper figure/table, to be cited exactly | **open** |
| `perplexity_10` (fully synthetic) | *not yet extracted* | paper figure/table, to be cited exactly | **open** |
| `perplexity_10` (human mixed) | *not yet extracted* | paper figure/table, to be cited exactly | **open** |

These are blank for one reason, stated plainly: `aclanthology.org` is unreachable from
the authoring environment (the network policy denies it, same as `huggingface.co`), so
the published values could not be read. **No number was invented to fill the gap.**

Whoever runs Stage A must, *before launching*:

1. Open <https://aclanthology.org/2025.emnlp-main.1506/>.
2. Locate the figure or table reporting GPT-2 / WikiText-2 perplexity across recursive
   generations for the fully synthetic and human-mixed conditions under top-k decoding.
3. Record each value here together with its exact figure/table number and panel.
4. Commit that edit **before** running either arm, so the freeze is provable by timestamp.

If the paper reports only a curve with no tabulated values, record the read-off values,
say explicitly that they were read off a figure, and widen the tolerance accordingly with
a written justification. A figure read-off is not a published number and must not be
presented as one.

## 3. Observed

Test perplexity by generation. Both arms ran to the full horizon; no generation is missing.

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
| 10 | 50.9806 | 30.3730 |

| Quantity | Fully synthetic | Human mixed |
|---|---|---|
| `perplexity_0` | 29.6179 | 29.6179 |
| `perplexity_10` | 50.9806 | 30.3730 |
| Degradation ratio | **1.7213** | **1.0255** |
| `eval_loss` at generation 10 | 3.9314 | 3.4136 |
| `eval_accuracy` at generation 10 | 0.3254 | 0.3838 |

Generation 0 is numerically identical across arms, as designed: it is computed once and
shared (`--shared-generation-zero`, deviation 7), so the two chains provably start from
the same baseline rather than from two models that merely ought to match.

### 3.1 The four frozen ordering claims, evaluated

| Frozen claim (§2.1) | Observed | Verdict |
|---|---|---|
| `degradation_ratio(fully_synthetic) > 1.0` | 1.7213 | **holds** |
| `degradation_ratio(human_mixed) > 1.0` and strictly below the synthetic arm | 1.0255; 1.0255 < 1.7213 | **holds** |
| `ratio(fully_synthetic) > ratio(human_mixed) > 1.0` | 1.7213 > 1.0255 > 1.0 | **holds** |
| Synthetic curve at or above the human-mixed curve for the majority of generations 1–10 | 10 of 10 | **holds** |

Two observations recorded but *not* part of the frozen criteria, and so carrying no
decision weight: the synthetic arm is strictly monotonically increasing across all 11
generations, and the human-mixed arm dips once (30.3628 → 30.3579 between generations 8
and 9) inside an otherwise flat, slightly rising curve. Neither was predicted in advance
and neither is offered as evidence.

## 4. Artifact links and hashes

Every generation of both arms carries an `artifact_record.json` written by the driver at
the moment that generation completed — before anything was deleted — recording a SHA-256
for the model directory, the generated `data.json`, and `eval_results.json`. All 22 are
committed under `measurements/`.

| Arm | Metrics + records | Summary | Generations recorded |
|---|---|---|---|
| Fully synthetic | `measurements/fully_synthetic/generation_00..10/` | `measurements/fully_synthetic/summary.json` | 11 of 11 |
| Human mixed | `measurements/human_mixed/generation_00..10/` | `measurements/human_mixed/summary.json` | 11 of 11 |

Each generation directory holds `eval_results.json`, `train_results.json`,
`all_results.json`, and `artifact_record.json`.

**The hashes cannot be re-verified, and §6.1 says why.** `verify_recorded_hashes` requires
the bytes, and the bytes are gone. The recorded hashes remain evidence of what was
produced; they are not a check anyone can now re-run.

## 5. Validity decision

**Decision: `valid_with_limitation`.**

Both arms completed. The ordering criterion — the criterion frozen as deciding pass or
fail — holds on all four of its claims. The 5% numeric band was **not evaluated**, because
the published values it compares against were never obtainable (§2.2).

The decision rule, frozen in advance:

| Outcome | Decision |
|---|---|
| Both arms complete; ordering holds; endpoint within the 5% engineering band | `valid` — write `report.md` |
| Both arms complete; ordering holds; endpoint outside the band | `valid_with_limitation` — write `report.md`, state the miss prominently |
| Both arms complete; ordering does not hold | `invalid` — write `failure_report.md`, classify `scientific_divergence`, **no rerun for a better number** |
| An arm fails to complete | classify per `docs/RUNBOOK.md`; rerun only if `infrastructure_failure` |

The observed outcome matches no row exactly: the rule anticipated the band being *tested*
and either met or missed, not *untestable*. The gap is resolved the conservative way, and
it was resolved in advance rather than now — `FAILURE_LOG.md` `PC-2026-08-03-B` states
that a run completed while §2.2 remains open "could reach at most `valid_with_limitation`".
This run is that case. Recording it as `valid` would claim a numeric agreement that was
never checked.

**What would upgrade this to `valid`:** obtain the published values, fill §2.2 with exact
figure/table citations, and compare against the observed endpoints above. No rerun is
needed or permitted for that — the observed numbers are already fixed and committed. If
the comparison then falls outside 5%, the decision moves to `valid_with_limitation` on
different grounds (a stated numeric miss), and the ordering result is unaffected either
way.

## 6. Deviations from upstream

Every deviation known at freeze time. This list is append-only; anything discovered during
the run gets added here and to `FAILURE_LOG.md`.

| # | Deviation | Reason | Effect on the comparison |
|---|---|---|---|
| 1 | `data_selection=no-selection` overrides upstream's `importance_sampling` default | Importance sampling is the paper's proposed *mitigation*, not the collapse baseline | Necessary. Leaving it on would confound the arm contrast with the paper's intervention. |
| 2 | Horizon read as 11 generations (0–10), not the "0 through 9" in this repository's earlier draft | Upstream's `num_iterations: 10` is authoritative | None on the ordering; the endpoint generation index is 10, not 9. |
| 3 | `wandb_disabled=true` | Avoids requiring a Weights & Biases account; upstream logs metrics to disk regardless | None. `eval_results.json` is written either way. |
| 4 | `transformers` installed from git source, not a pinned release | Upstream's own install instruction | **Material.** Upstream pins no version, so the resolved commit must be recorded at run time or the run is not reproducible. |
| 5 | Model / tokenizer / dataset revisions unpinned upstream | Upstream names `openai-community/gpt2` with no revision | **Material.** Must be resolved and recorded on the run host; the adapter refuses to proceed otherwise. |
| 6 | Arms run one generation at a time via `scripts/run_positive_control_arm.py` instead of upstream's single-process `main.py` | Upstream has no resume; a session-capped host loses an interrupted arm entirely | None on the computation. The subprocess commands are identical and pinned by test. |
| 7 | Generation 0 computed once and shared between arms (default) | Upstream's iteration-0 command is identical for both arms | None, and it removes a nondeterminism source: both arms start from a bit-identical baseline. Disable with `--no-shared-generation-zero`. |
| 8 | Superseded model directories pruned after hashing (opt-in, `--prune-models`) | Every generation retrains from base GPT-2, so a model is spent once the next generation's data exists | **Not used.** The run did not pass `--prune-models`; every `artifact_record.json` records `pruned: false`. The bytes were nonetheless lost — see §6.1, which is a different thing. |
| 9 | `--self_bleu_n_sample 50` instead of upstream's default 1000 | The default drives an O(n²) NLTK BLEU sweep of ~10⁶ pair comparisons per generation, several times the cost of the decoding it describes. Adopted mid-run once the cost was measured. | None on any frozen quantity. Self-BLEU is computed *after* `data.json` is written and is read only by a `wandb.log` (disabled) and a diagnostic file. Applied identically to both arms from the same generation onward. |
| 10 | wandb suppressed by environment variables (`WANDB_DISABLED`, `WANDB_MODE`) in the executed driver, rather than by the `sitecustomize` shim described in `FAILURE_LOG.md` `PC-2026-08-05-E` | The shim was written after the `PC-2026-08-05-E` crash; the driver that actually executed all 22 generations does not contain it | None on any frozen quantity — wandb is dashboard reporting only. **But it contradicts `PC-2026-08-05-E`, which states env vars alone are insufficient.** All 22 generations completed and were recorded, so the env-var path evidently sufficed here. Flagged as unresolved in `report.md` §6 rather than explained away. |
| 11 | Generated corpora (`data.json`) and model checkpoints not retained after the run | The executing host was an ephemeral Kaggle container, reclaimed at session end | **Material for verification only.** See §6.1. No effect on any reported metric. |

### 6.1 Artifacts hashed but not retained

**This is not pruning.** `--prune-models` was never passed, and every `artifact_record.json`
correctly records `pruned: false` — that was true when the driver wrote it. The bytes were
lost afterwards, for a different reason: the run executed in an ephemeral Kaggle container
whose `/kaggle/working` was reclaimed when the session ended, and only the metrics files
had been mirrored to the repository by the auto-push monitor.

The run records were **not** retro-edited to claim a prune that did not happen. The
inventory of what was lost is recorded separately, in
`measurements/artifact_retention.json`.

| Arm | Artifacts hashed but not retained | Retained |
|---|---|---|
| Fully synthetic | 11 model directories, 10 generated corpora (21 total) | all 11 `eval_results.json`, `train_results.json`, `all_results.json`, `artifact_record.json` |
| Human mixed | 11 model directories, 10 generated corpora (21 total) | same |

Consequences, stated plainly:

- Every reported metric is fully backed. `eval_results.json` is committed for all 22
  generation-arm pairs and is the source of every number in §3.
- The recorded SHA-256 values remain evidence of what was produced, and are committed.
  **They can no longer be verified against the bytes**, so `verify_recorded_hashes` cannot
  be run against this execution. A future run must re-derive its own.
- Qualitative inspection of the degraded text is no longer possible for this execution. The
  perplexity curve is the evidence; there is no sample of generation-10 synthetic output to
  show alongside it.
- This is an infrastructure limitation of the executing host, not a protocol violation. It
  is recorded in `FAILURE_LOG.md` as `PC-2026-08-07-H`.

## 7. Known limitation: no tail-retention measure in Stage A

`schemas/chain_result.schema.json` and `schemas/evaluation.schema.json` both require a
`tail_retention` figure. The upstream positive control produces test perplexity and eval
loss only — it computes no tail measure — and this project's own primary tail-retention
definition is still being frozen as a separate Week 2 deliverable.

`positive_control_adapter.build_chain_result` therefore **refuses to emit a `ChainResult`
for Stage A** rather than filling `tail_retention` with a sentinel. A schema-valid artifact
carrying a meaningless tail number is exactly the "persuasive-looking but scientifically
unusable" output `PROTOCOL.md` §1 exists to prevent. Stage A reports through
`positive_control_result.json` instead, and this limitation is recorded rather than
engineered around.

## 8. Checkpoint-resume equivalence

Frozen equivalence rule and its honest scope:

| Claim | Rule | Where tested |
|---|---|---|
| Ingest is exactly reproducible | An interrupted and an uninterrupted ingest of the same upstream artifacts produce byte-identical checkpoints, metrics, and manifest history | `tests/runner/test_real_checkpoint_resume.py` — **passing** |
| Training resume is bit-identical | **Not claimed.** | — |

The second row is the honest part. This repository does not control upstream's training
loop, and non-determinism in CUDA kernel selection, cuDNN autotuning, and dataloader
worker ordering means a resumed GPT-2 training run is not guaranteed to reproduce
bit-identical weights. When Stage A runs, the frozen tolerance for that claim is:

- **Scientific state must match exactly:** generation index, token totals, config hashes,
  manifest history, and the set of artifacts produced.
- **Metric outputs must match within `1e-4` relative** on the resumed segment.
- **Weight-level and generated-text equality are not asserted.** If observed byte
  equality occurs, it is reported as an observation, never as a guarantee.

Exceeding the metric tolerance is an `implementation_defect` and blocks the run.
