# Positive control: expected versus observed

**Status: EXPECTED SIDE FROZEN, OBSERVED SIDE NOT YET COLLECTED.**

This document is the comparison ledger for Stage A. The expected column and the decision
rule below were frozen on **2026-08-03**, before either arm was executed, and are
governed by `PROTOCOL.md` §2. The observed column is empty because no arm has run — see
`failure_report.md` for why, and `docs/benchmarks/khantushig_week2.md` for the evidence.

No value in the observed column may be filled in by hand. It is regenerated from saved
artifacts by `scripts/reproduce_positive_control.sh`, which writes `observed_table.md`
alongside this file.

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

*Empty. No arm has been executed.*

| Generation | Fully synthetic | Human mixed |
|---:|---:|---:|
| 0–10 | not run | not run |

| Quantity | Fully synthetic | Human mixed |
|---|---|---|
| `perplexity_0` | — | — |
| `perplexity_10` | — | — |
| Degradation ratio | — | — |

## 4. Artifact links and hashes

*Empty. No artifacts exist.*

When the run completes, `adapt_run` records, for every generation of both arms: the model
checkpoint directory path and its SHA-256, the generated `data.json` path and SHA-256, and
the `eval_results.json` path and SHA-256. Those land in
`runs/positive_control/<arm>/checkpoints/generation_XXXX.json` and are re-verified by
`verify_recorded_hashes`, which `scripts/reproduce_positive_control.sh` runs before it will
print a success line.

| Arm | Run manifest | Checkpoints | Metrics | Logs |
|---|---|---|---|---|
| Fully synthetic | — | — | — | — |
| Human mixed | — | — | — | — |

## 5. Validity decision

**Decision: NOT YET DECIDABLE — no run has been executed.**

This is deliberately not recorded as `invalid`. `invalid` is a judgment about a run that
happened. Nothing has happened, and saying otherwise in either direction would be false.

The decision rule, frozen in advance:

| Outcome | Decision |
|---|---|
| Both arms complete; ordering holds; endpoint within the 5% engineering band | `valid` — write `report.md` |
| Both arms complete; ordering holds; endpoint outside the band | `valid_with_limitation` — write `report.md`, state the miss prominently |
| Both arms complete; ordering does not hold | `invalid` — write `failure_report.md`, classify `scientific_divergence`, **no rerun for a better number** |
| An arm fails to complete | classify per `docs/RUNBOOK.md`; rerun only if `infrastructure_failure` |

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
