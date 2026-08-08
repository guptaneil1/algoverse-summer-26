# Week 2 Compute Benchmark — Khantushig

**Scope:** `week-2/khantushig-positive-control`, recorded 2026-08-03. Every number below is
labeled either **measured** (from a command actually run in this environment) or
**estimate** (a stated-assumption forecast), per `COMPUTE.md`: "forecasts must state
assumptions and may not be presented as actual usage."

> **Updated 2026-08-07.** This document was written on 2026-08-03, when Stage A could not
> be executed. Stage A has since run to completion; §7 records what the forecasts below
> got right and wrong. **Sections 1–6 are left exactly as written on 2026-08-03** so the
> pre-run estimates stay comparable against the measurement, which is the point of keeping
> a forecast at all. Read §7 before quoting any number from §4 or §5.
>
> The result itself is in `docs/positive_control/report.md`; measured compute is in
> `COMPUTE.md`.

**Nothing in §§1–6 is a positive-control result.** They were written before any arm ran —
see `docs/positive_control/failure_report.md`, now superseded. `PROTOCOL.md` §5 (no-result
rule) applied at the time of writing.

## 1. Upstream commit — now pinned

Week 1 recorded this as blocked. It is resolved.

| Field | Value |
|---|---|
| Repository | `https://github.com/GeorgeDrayson/model_collapse` |
| Commit | `feb8511479a2e2dc868e1caf3f63cb99f1fcc746` |
| Commit date | 2026-03-13 |
| Resolved on | 2026-08-03, as `HEAD` of the default branch |
| Clone size | 432 KiB (code and configs only; no weights or data) |

`github.com` is reachable from this environment, so every frozen setting in `PROTOCOL.md`
was read from the upstream working tree rather than inferred.

## 2. Environment — measured

| Field | Value |
|---|---|
| Python | 3.11.15 |
| Platform | `Linux-6.18.5-x86_64-with-glibc2.39` |
| CPU | x86_64, 4 vCPUs |
| Memory | 15 GiB total, ~14 GiB free at measurement |
| Disk | 252 GiB volume, 30 GiB available |
| GPU | **none** — `nvidia-smi` not present |
| `torch` | not installed |
| `transformers` | not installed |
| `datasets` | not installed |
| `jsonschema` | 4.26.0 |
| `pytest` | 9.1.1 |
| `ruff` | 0.16.1 |

Captured programmatically by `positive_control_adapter.capture_environment()`, which is the
same function that will stamp the environment block into a real run manifest.

### 2.1 Network policy — measured

| Host | Needed for | Result |
|---|---|---|
| `github.com` | upstream code | reachable |
| `huggingface.co` | GPT-2, WikiText-2, ModernBERT detector, revision SHAs | `403` on `CONNECT` |
| `aclanthology.org` | published expected values | `403` on `CONNECT` |

This is why the model/tokenizer/dataset revisions are carried as `resolve_at_runtime`
sentinels rather than pinned, and why the numeric expected values in
`expected_vs_observed.md` §2.2 are marked open rather than filled in.

## 3. Week 2 infrastructure cost — measured

The only compute actually consumed this week was development and testing. No model was
trained and no accelerator was used.

| Workload | Wall time | Peak RSS |
|---|---:|---:|
| Full suite (`pytest tests -q`, 158 passed / 1 skipped) | 3.78 s | 40.4 MiB |
| Runner suite (`pytest tests/runner -q`, 99 passed / 1 skipped) | 3.93 s | — |
| `ruff check .` | < 1 s | — |
| `python scripts/audit_repository.py --strict-structure` | < 1 s | — |

**Accelerator-hours consumed this week: 0.00.** Storage written to the repository:
approximately 90 KiB of source, configs, tests, and documentation. The upstream clone
(432 KiB) lives outside the repository and is not committed.

The `tests/runner` figure being marginally above the full-suite figure is process-startup
noise at this scale, not a real inversion; both are dominated by interpreter startup.

## 4. Forecast for the unexecuted Stage A — estimate

**This is a formula-based engineering estimate, not the measured one-generation smoke-run
basis `COMPUTE.md` requires.** It is carried forward and refined from Week 1 §6, now that
the upstream configuration is known. It remains an estimate until someone runs
`python main.py smoke_test=true` on real hardware and replaces it.

### 4.1 What the pinned config actually specifies

| Parameter | Value | Source |
|---|---|---|
| Model | GPT-2, 124M parameters | `config/model/gpt2.yaml` |
| Dataset | WikiText-2 raw train split | `config/dataset/wikitext2.yaml` |
| Block size | 512 | `config/train/default.yaml` |
| Batch size | 8 | `config/train/default.yaml` |
| Epochs per generation | 1 | `config/train/default.yaml` |
| Generations | 11 (indices 0–10) | `config/config.yaml` |
| Precision | bfloat16 | `config/config.yaml` |

Knowing the dataset is WikiText-2 rather than an unknown corpus narrows Week 1's two
illustrative scenarios to one. WikiText-2's raw train split is commonly cited at roughly
2.4M GPT-2 tokens — **this figure is an assumption carried from public description, not a
measurement**, because the dataset could not be downloaded here to count it.

### 4.2 Training compute

Using `C ≈ 6ND` (Kaplan et al., 2020) with `N = 1.24 × 10^8`:

| Arm | Tokens per generation | Total tokens (11 generations) | Training FLOPs |
|---|---:|---:|---:|
| Fully synthetic (`alpha=0`) | ~2.4M | ~26.4M | 2.0 × 10^16 |
| Human mixed (`alpha=1`) | ~4.8M from generation 1 | ~50.4M | 3.8 × 10^16 |

At ~30% achieved utilization (an assumption, not measured):

| GPU | Fully synthetic | Human mixed | Both arms |
|---|---:|---:|---:|
| T4 (~65 TFLOPS bf16) | 0.29 h | 0.54 h | 0.83 GPU-h |
| A100 (~312 TFLOPS bf16) | 0.06 h | 0.11 h | 0.17 GPU-h |

### 4.3 Generation and detection dominate — the important correction

Training is **not** the bottleneck, and Week 1's estimate missed this because the upstream
pipeline had not yet been read. At the pinned commit, each generation `i ≥ 1` also runs
`src/generate.py`, which autoregressively decodes `loss_on_last_n_tokens = 256` new tokens
per training example with `top_k=50`, and then classifies every generated text with the
150M-parameter ModernBERT detector (`main.py` passes `--classify_text 1` unconditionally).

Autoregressive decoding is sequential and memory-bandwidth bound, not FLOP bound, so the
`6ND` rule does not apply to it. Decoding ~4,600 blocks × 256 tokens per generation, an
order-of-magnitude expectation is **tens of minutes to a few hours per generation on a
T4**, versus minutes for the training step. Across 10 generating iterations × 2 arms, the
realistic total is plausibly **10–40 GPU-hours on a T4**, or roughly a quarter of that on
an A100.

**The spread on that range is wide enough that it should not be used for planning without
the smoke-run measurement.** It is stated here to correct the impression left by §4.2 that
Stage A is a sub-GPU-hour job. It is not.

### 4.4 Storage

| Item | Estimate |
|---|---:|
| One GPT-2 checkpoint (fp32, no optimizer state) | ~496 MB |
| 11 checkpoints × 2 arms | ~11 GB |
| Generated `data.json` per generation | MB-scale |
| Detector model (downloaded once) | ~600 MB |
| **Total working set** | **~12–15 GB** |

Free Colab's disk is adequate; its session limit is not. Each arm plausibly exceeds a
single free-tier session, which makes the checkpoint-resume path a practical requirement
rather than a formality.

## 5. Pilot forecast

Stage B (mechanism pilot) stays blocked behind Stage A per `PROTOCOL.md` §4. What Week 2
changes for the pilot forecast:

- The runner's own orchestration overhead remains negligible — Week 1 measured
  sub-millisecond per generation, and the Stage A adapter adds only file hashing, which is
  I/O bound and small relative to a training step.
- Per-generation *decoding* cost, not training cost, is the quantity that will set the
  pilot's feasible chain count. The pilot's compute gate should be written against decode
  throughput.
- At least 5 independent chains × 11 generations, at the §4.3 range, is **on the order of
  100+ T4-hours** for a single treatment family. That number is soft until the smoke run
  lands, and it is the number that should drive the compute-gate decision in `COMPUTE.md`.

## 6. Next steps

Blocked on external provisioning, unchanged from Week 1 in kind but now fully specified:

1. Obtain an accelerator host with `huggingface.co` access.
2. Resolve the deferred revision identifiers and commit them into both arm configs.
3. Extract the published expected values into `expected_vs_observed.md` §2.2 and commit
   before launching.
4. Run `python main.py smoke_test=true wandb_disabled=true data_selection=no-selection`,
   measure it, and replace §4's estimate with that measurement.
5. Run both arms via `scripts/reproduce_positive_control.sh` and append actual usage to
   `COMPUTE.md`.

## 7. Forecast versus measurement — recorded 2026-08-07

Stage A ran on 2026-08-06/07 on Kaggle, 2× Tesla T4, one arm per GPU. Sections 1–6 above
are unedited; this section scores them.

### 7.1 What the forecast got right

| §4.3 claim | Outcome |
|---|---|
| Decoding, not training, dominates | **Correct, and by more than stated.** Training was 8.57 h of ~19.0 accelerator-hours; everything else — decoding, dataset preparation, detector inference — was the remaining ~10.4 h. |
| Total 10–40 T4-hours for both arms | **Correct.** Measured ~19.0 T4-hours, inside the band. |
| Each arm plausibly exceeds one free-tier session, so checkpoint-resume is a practical requirement | **Correct, and load-bearing.** The human-mixed arm took ~10.76 h. The run survived three prior session losses only because the driver resumes per generation. |
| §4.2's sub-GPU-hour training figure | **Correct in kind, wrong in size.** Predicted 0.83 GPU-h of training; measured 8.57 h, about 10× high. The `6ND` estimate assumed ~30% utilization; actual utilization on a T4 at batch size 8 was far lower. The *conclusion* §4.2 was used to draw — that training is not the bottleneck — still holds. |

### 7.2 What the forecast got wrong

- **§4.4 storage could not be checked.** The container was reclaimed before storage was
  measured (`FAILURE_LOG.md` `PC-2026-08-07-H`). The ~12–15 GB estimate is neither
  confirmed nor refuted.
- **§6 step 4 was impossible.** `python main.py smoke_test=true` aborts at `main.py:55`
  with a `TypeError` at the pinned commit (`PC-2026-08-05-C`). The compute basis was
  measured from a full generation 0 instead. Anyone following §6 literally will hit this.
- **§6 step 3 was never completed.** The published expected values remain unobtainable, and
  that is why the reproduction is `valid_with_limitation` rather than `valid`.
- **A cost the forecast missed entirely:** upstream's self-BLEU diagnostic defaults to
  `--self_bleu_n_sample 1000`, an O(n²) NLTK sweep of ~10⁶ pair comparisons per generation,
  which ran several times longer than the decoding it describes. Capped at 50 mid-run. §4.3
  modelled decoding and detection but not this.

### 7.3 Effect on the §5 pilot forecast

§5's "on the order of 100+ T4-hours" for 5 chains × 11 generations scales from the §4.3
range. Substituting the measurement: ~19.0 T4-hours for 2 chains gives ~9.5 T4-hours per
chain, so 5 chains is **~48 T4-hours** for one treatment family — roughly half the §5
figure, and now grounded in measurement rather than a range.

Two caveats before that number is used for the compute gate. It carries the self-BLEU cap,
without which it would be substantially higher. And the two arms are not equal cost: the
human-mixed arm took 10.76 h against the synthetic arm's 8.26 h, because `alpha=1` trains
on roughly twice the tokens per generation. A pilot's cost therefore depends on its mixture
schedule, not on chain count alone.
