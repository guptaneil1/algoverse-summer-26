# Positive control: expected versus observed

**Status: ORDERING FROZEN 2026-08-03. OBSERVED SIDE COLLECTED 2026-08-06/07.
PUBLISHED VALUES OBTAINED 2026-08-07, AFTER THE RUN. Decision: `valid_with_limitation`.**

This document is the comparison ledger for Stage A. The expected column and the decision
rule below were frozen on **2026-08-03**, before either arm was executed, and are
governed by `PROTOCOL.md` §2. Both arms completed all 11 generations on 2026-08-07; the
observed column below is filled from their saved artifacts.

**§2.2 was closed on 2026-08-07**, after the run, when the paper was obtained. Both arms
have published comparators and **both pass the 5% band on every published quantity**, worst
deviation 2.27% (§3.2). The decision is held at `valid_with_limitation` rather than `valid`
because `PC-2026-08-03-B` pre-registered that ceiling for a run completed before the
published values existed — see §5, which sets out the case rather than settling it
silently.

No value in the observed column was filled in by hand. Every number below is read from
the committed artifacts under `measurements/`, and the two `positive_control_result.json`
files were produced by `positive_control_adapter.summarize` over
`positive_control_adapter.read_eval_results` — the same functions, and the same output
shape, that `adapt_run` writes under that name.

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

### 2.2 Numeric expected values — CLOSED 2026-08-07

**These values were obtained *after* both arms ran.** They were unobtainable before
(`aclanthology.org` denied by network policy, `FAILURE_LOG.md` `PC-2026-08-03-B`), so the
freeze-before-run discipline this section originally demanded was not achieved. Stated
plainly rather than papered over: the numbers below were transcribed from the published
PDF after the observed values in §3 already existed and were committed. What protects the
comparison is that the *observed* side is immutable — committed generation by generation
between 2026-08-06T17:26Z and 2026-08-07T04:12Z, before any published value was seen —
not that the expected side was frozen first.

Both arms have a published comparator, from two different tables.

**Fully synthetic arm (α=0)** — Table 1, "Impact of decoding strategies on the model
performance and text generation quality (comparison between generations 0 and 9) in the
fully synthetic recursive training setting", GPT-2 / **top-k** row:

| Quantity | Published |
|---|---:|
| `perplexity` Gen 0 | 29.31 |
| `perplexity` Gen 9 | 48.36 |
| `eval_accuracy` Gen 0 | 38.73 |
| `eval_accuracy` Gen 9 | 33.12 |

**Human-mixed arm (α=1)** — Table S2, "Test performance (perplexity and accuracy) and data
quality at generation 0 and generation 9", GPT-2 / **baseline** / **top-k** /
**α,β,γ = 1, 1, 0** row:

| Quantity | Published |
|---|---:|
| `perplexity` Gen 0 | 29.25 |
| `perplexity` Gen 9 | 29.92 |
| `eval_accuracy` Gen 0 | 38.78 |
| `eval_accuracy` Gen 9 | 38.34 |

Three matching decisions, each checked against the paper rather than assumed:

- **`top-k` row**, because the frozen configuration is top-k with `k=50`
  (`config/decoding/top_k.yaml`).
- **`baseline`, not `ours`**, because `ours` is the paper's Sampling Importance Resampling
  mitigation. `PROTOCOL.md` deviation 1 sets `data_selection=no-selection` precisely to
  measure the collapse baseline rather than the intervention, so `baseline` is the correct
  comparator. Comparing against `ours` would compare our unmitigated run to their mitigated
  one.
- **`α,β,γ = 1, 1, 0`**, which is exactly this project's human-mixed configuration:
  `human_data_alpha=1.0`, `ai_beta=1.0`, `gamma=0.0`. The paper defines these coefficients
  at Eq. 3 / Figure 2 and calls this the partially synthetic setting.

The paper reports diversity, self-BLEU, MAUVE and readability alongside these. None is
compared: the generated corpora needed to compute them were lost with the container
(§6.1), and the self-BLEU that was computed used a reduced sample (deviation 9), so it is
not comparable to the published figure.

#### 2.2.1 The published horizon is Gen 9, not Gen 10

Every reported result in the paper ends at **generation 9**. This is not an artefact of one
table: Figure 1, Table 1, Figure 3, Figure S1 and Table S2 all report "generations 0 to 9",
and Figures S3, S4 and S5 describe the same experiments as running "for 10 generations" —
nine places in total, consistently 10 generations at indices 0–9.

`PROTOCOL.md` froze this project's primary endpoint at generation 10, derived from
upstream's `num_iterations: 10` and `main.py`'s `range(1, num_iterations+1)`, which yields
11 models at indices 0–10. The published experiment evidently ran one fewer.

**The numeric comparison is therefore performed at generation 9**, against our generation 9,
because comparing our generation 10 to their generation 9 would compare different
quantities. Our run produced generation 9 as an ordinary intermediate point; nothing was
rerun, extended, or truncated to make this comparison possible, and generation 10 remains
recorded in §3 as an observation beyond the paper's horizon.

**The index affects the fully synthetic arm's verdict, so both readings are reported
(§3.2).** Our generation 9 sits 2.27% from the published Gen 9 value — inside the 5% band.
Our generation 10 against that same value sits 5.42% — outside it. The index is selected
because the paper states its own horizon nine times over, not because of which side of the
band it falls on, and the losing reading is printed beside the winning one.

This revises a note recorded earlier under "Recorded deviation from this document's own
earlier draft" in `PROTOCOL.md`. That note concluded an earlier "generations 0 through 9"
reading was a drafting error and corrected the horizon to 0–10 on the authority of the
upstream config default. The upstream default does produce 11 models, so the horizon we
*ran* is right; but the published experiment reports 10, and the earlier note's dismissal
of "0 through 9" was wrong.

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

### 3.2 Numeric comparison against the published values

Both arms, at the paper's published horizon (Gen 9). Tolerance 5% relative, engineering
only. Sources per arm are given in §2.2.

**Fully synthetic arm (α=0)** vs Table 1, GPT-2 / top-k:

| Quantity | Published | Observed | Relative difference | Within 5% |
|---|---:|---:|---:|:--:|
| `perplexity` Gen 0 | 29.31 | 29.6179 | 1.05% | **yes** |
| `perplexity` Gen 9 | 48.36 | 49.4601 | 2.27% | **yes** |
| `eval_accuracy` Gen 0 | 38.73 | 38.7614 | 0.08% | **yes** |
| `eval_accuracy` Gen 9 | 33.12 | 32.9627 | 0.47% | **yes** |
| Degradation ratio Gen 9 / Gen 0 | 1.6499 | 1.6699 | 1.21% | **yes** |

**Human-mixed arm (α=1)** vs Table S2, GPT-2 / baseline / top-k / α,β,γ = 1, 1, 0:

| Quantity | Published | Observed | Relative difference | Within 5% |
|---|---:|---:|---:|:--:|
| `perplexity` Gen 0 | 29.25 | 29.6179 | 1.26% | **yes** |
| `perplexity` Gen 9 | 29.92 | 30.3579 | 1.46% | **yes** |
| `eval_accuracy` Gen 0 | 38.78 | 38.7614 | 0.05% | **yes** |
| `eval_accuracy` Gen 9 | 38.34 | 38.3852 | 0.12% | **yes** |
| Degradation ratio Gen 9 / Gen 0 | 1.0229 | 1.0250 | 0.20% | **yes** |

**Every published quantity for both arms falls inside the band. The worst deviation
anywhere in the comparison is 2.27%**, and eight of the ten quantities agree to better
than 1.5%. The two accuracy figures for the human-mixed arm agree to 0.05% and 0.12%.

**The alternative reading, reported because it fails.** Comparing our frozen endpoint
(generation 10) against the published Gen 9 values gives 50.9806 vs 48.36 = **5.42%,
outside the band**, for the fully synthetic arm. The human-mixed arm at generation 10
(30.3730 vs 29.92) is 1.51%, still inside. That comparison is between different generation
indices and is not the one this document adopts (§2.2.1), but a reader who holds this
project to its originally frozen endpoint index sees the fully synthetic arm miss.

**Two caveats on the agreement.** Our Gen 0 perplexity (29.6179) sits above the paper's
entire Gen 0 spread across all decoding rows and both tables (29.22–29.31), a small
systematic offset consistent with the framework-version and hardware differences recorded
in `PC-2026-08-05-D` and `PC-2026-08-06-F`. Because it is systematic, it largely cancels in
the degradation ratio, which is the paired quantity — both ratios agree far more closely
(1.21% and 0.20%) than the raw endpoints do. And the published values were read after the
observed values existed (§2.2), so this is a post-hoc comparison against immutable
observations, not a pre-registered numeric prediction.

## 4. Artifact links and hashes

Every generation of both arms carries an `artifact_record.json` written by the driver at
the moment that generation completed — before anything was deleted — recording a SHA-256
for the model directory, the generated `data.json`, and `eval_results.json`. All 22 are
committed under `measurements/`.

| Arm | Metrics + records | Summary | Generations recorded |
|---|---|---|---|
| Fully synthetic | `measurements/fully_synthetic/generation_00..10/` | `measurements/fully_synthetic/positive_control_result.json` | 11 of 11 |
| Human mixed | `measurements/human_mixed/generation_00..10/` | `measurements/human_mixed/positive_control_result.json` | 11 of 11 |

Each generation directory holds `eval_results.json`, `train_results.json`,
`all_results.json`, and `artifact_record.json`.

**The hashes cannot be re-verified, and §6.1 says why.** `verify_recorded_hashes` requires
the bytes, and the bytes are gone. The recorded hashes remain evidence of what was
produced; they are not a check anyone can now re-run.

### 4.1 Commands

`measurements/executed_commands.json` lists all 42 upstream invocations — 21 per arm, one
`train.py` at generation 0 and a `generate.py`/`train.py` pair for each of generations
1–10 — with full argument vectors and the absolute paths the run used.

It is a **reconstruction, not a transcript.** The driver's `stdout_stderr.log` was lost
with the container. The commands were regenerated by calling the same builder functions in
`scripts/run_positive_control_arm.py` against the same committed configs; those builders
are pure functions of the config, and their argument lists are pinned against upstream
`main.py` by `tests/runner/test_positive_control_driver.py`. What is reconstructed is
therefore exact, but the file cannot evidence that these commands *ran* — the per-generation
`train_results.json` and `eval_results.json` do that.

### 4.2 Frozen-interface artifacts that were not produced

Two artifacts the adapter would normally emit do not exist for this run, and neither can be
created now without inventing something:

| Artifact | Why not |
|---|---|
| `run_manifest.json` (per arm) | `adapt_run` writes it, but `adapt_run` cannot run: `ingest_generation` requires the model directories and generated corpora on disk, and it correctly refuses when they are absent and were never recorded as pruned (§6.1). Rerunning it here would also stamp `capture_environment()` with *this* machine — no GPU, no torch — which would misrepresent the run environment. |
| `ChainResult` | `build_chain_result` refuses by design, for the reason in §7 — no tail-retention measure exists. This is unchanged by the run and is not a loss. |

The metric content `adapt_run` would have written to `positive_control_result.json` **does**
exist, under that name, for both arms: `summarize` and `read_eval_results` need only the
metrics files, which survived. What is missing from those files relative to a full
`adapt_run` is the per-generation artifact-hash block, which is instead carried by the 22
committed `artifact_record.json` files.

## 5. Validity decision

**Decision: `valid_with_limitation`.**

On the numbers, this is a full quantitative reproduction. Both arms completed. All four
frozen ordering claims hold (§3.1). Every published quantity for both arms falls inside the
5% engineering band, worst deviation 2.27% (§3.2). Read against the frozen decision table
alone, that is the `valid` row.

The decision is nonetheless held at `valid_with_limitation`, for one reason that is not a
matter of taste:

> `FAILURE_LOG.md` `PC-2026-08-03-B`, recorded 2026-08-03: "The 5% engineering tolerance
> cannot be applied until the published values exist, so a run completed **before then**
> could reach at most `valid_with_limitation`."

This run was completed before the published values were obtained. That sentence was written
when nobody knew which way the numbers would fall, and it set a ceiling for exactly this
situation. Raising that ceiling now — after seeing that the numbers agree — would be the
precise move this project's rules exist to prevent: revising a pre-registered constraint
because the result turned out well. The constraint binds whether or not it is convenient.

The decision rule, frozen in advance:

| Outcome | Decision |
|---|---|
| Both arms complete; ordering holds; endpoint within the 5% engineering band | `valid` — write `report.md` |
| Both arms complete; ordering holds; endpoint outside the band | `valid_with_limitation` — write `report.md`, state the miss prominently |
| Both arms complete; ordering does not hold | `invalid` — write `failure_report.md`, classify `scientific_divergence`, **no rerun for a better number** |
| An arm fails to complete | classify per `docs/RUNBOOK.md`; rerun only if `infrastructure_failure` |

Two further limitations, both recorded and neither fatal:

1. **The comparison index is not the frozen one.** The paper's horizon is Gen 9; this
   project froze Gen 10. Gen 9 is used because the paper states its own horizon in nine
   separate places (§2.2.1), so the choice is principled rather than result-driven — but at
   Gen 10 the fully synthetic arm would sit outside the band (§3.2). A reader holding this
   project to its frozen index reaches a different verdict on that arm.
2. **Only perplexity and accuracy were compared.** The paper also reports diversity,
   self-BLEU, MAUVE and readability; none could be computed, because the generated corpora
   were lost (§6.1) and the self-BLEU that was computed used a reduced sample (deviation 9).

**What this means in practice.** The scientific content of a `valid` result is present and
documented: the published positive control reproduces both qualitatively and numerically.
The label is held one notch lower on a pre-registration technicality, and the technicality
is named so a reader can weigh it. If the team judges that `PC-2026-08-03-B`'s ceiling was
about the *absence* of a comparison rather than its *timing*, the case for `valid` is on
the table — but that is a decision to take explicitly, in writing, with this paragraph
cited, not one to make by quietly relabelling.

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

### 6.2 Deviations specific to the 2026-08-17 rerun (RTX 4090)

Deviations 1–11 above describe the **2026-08-07 T4 execution**. This subsection records the
second execution, which differs on five of them. Nothing above is edited; both runs stand.

**Carried over unchanged:** 1 (`data_selection=no-selection`), 2 (horizon 11), 3
(`wandb_disabled=true` in the arm config), 6 (one generation at a time), 9
(`--self_bleu_n_sample 50`).

| # | Deviation | Reason | Effect on the comparison |
|---|---|---|---|
| 12 | **Resolves #4.** `transformers` pinned to `4.48.3` explicitly, not installed from git main | The environment freeze in `PROTOCOL.md` §2 now names exact versions | **Improvement.** The reproducibility hazard #4 flags is closed for this run: torch 2.8.0+cu128, transformers 4.48.3, datasets 3.2.0, accelerate 1.2.1, Python 3.12.3 |
| 13 | **Resolves #5.** GPT-2 model/tokenizer revision resolved and recorded as `607a30d783dfa663caf39e06633721c8d4cfcd7e` | Verified on the run host before launch; identical to the value already pinned in both arm configs | **Improvement.** Confirms the upstream model has not moved since the first run |
| 14 | **Contradicts #7.** `--no-shared-generation-zero`: each arm computed its own generation 0 | Forced by F-008 — `--prune-models` deletes generation 0's checkpoint during the `fully_synthetic` arm, so the shared baseline was unavailable | Minor. Both arms ran upstream's identical iteration-0 command with seed 42. Observed: 29.58853 vs 29.59030, a 0.006% spread. This is an unplanned determinism check and it passed; the arms no longer share a bit-identical baseline by construction |
| 15 | **Contradicts #8.** `--prune-models` **was** passed | Host storage management | Material for verification of superseded checkpoints only. Hashes were written before deletion and `verify_recorded_hashes` passed on this execution |
| 16 | **Contradicts #10.** wandb suppressed by the `sitecustomize` shim, not by environment variables | Env vars alone did **not** work here: with none set the run crashed at `train.py:683` (F-006); `wandb.init(mode='disabled')` via shim succeeded. See F-007 for the `sys.path` shadowing that made the first shim placement inert | None on any frozen quantity. **Note:** this does not resolve `report.md` §6, because the env-var-only configuration was never cleanly tested — the one attempt failed earlier on a stale output directory (F-007). wandb version here: 0.28.2 |
| 17 | **Contradicts #11.** Artifacts retained through the run; hash verification executed and passed | Persistent volume on a non-ephemeral host, rather than a reclaimed Kaggle container | **Improvement.** Acceptance criterion 6 is satisfied by execution rather than by argument: the driver regenerated `observed_table.md` from saved metrics and verified every recorded hash |
| 18 | Hardware: 1× RTX 4090, compute capability 8.9, native bfloat16 | Available host | None on any computed quantity. The T4 (cc 7.5) has no bf16 tensor cores and emulated the dtype; this run executes it natively. Cost fell from ~19.0 accelerator-hours to ~1.52 h |

**Harness defects surfaced by this run**, all recorded in `FAILURE_LOG.md` and none affecting
computed results: F-006 (upstream wandb guard), F-007 (`sitecustomize` shadowing and a stale
output directory), F-008 (`--prune-models` destroys the shared generation 0 — these two flags
are mutually incompatible and nothing warns), F-009 (a generation is marked complete before
its artifacts are confirmed present).


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
