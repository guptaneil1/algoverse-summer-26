# Week 1 Compute Benchmark — Khantushig

**Scope:** `week-1/khantushig-recursive-runner`, recorded 2026-07-25. Every number below is labeled
either **measured** (taken from a real command run in this Codespace) or **estimate** (a stated-
assumption forecast, per `COMPUTE.md`'s "forecasts must state assumptions and may not be presented
as actual usage"). Nothing measured here is a real positive-control or model-collapse result — see
`PROTOCOL.md` §5 (no-result rule).

## 1. Positive-control commit hash — pending

**Status: not pinned.** `PROTOCOL.md` §2 records:

```
Exact upstream commit: TODO(khantushig): pin exact upstream commit hash before Stage A
execution — do not invent, awaiting value from repo owner.
```

Upstream repo: `https://github.com/GeorgeDrayson/model_collapse` (Drayson, Yilmaz & Lampos,
"Machine-generated text detection prevents language model collapse," EMNLP 2025). No commit hash
is recorded here because none has been supplied yet — see "Next steps."

## 2. Environment identifiers — measured

| Field | Value |
|---|---|
| Python | 3.12.1 |
| OS | Ubuntu 24.04.4 LTS (Noble Numbat) |
| Kernel/platform | `Linux-6.8.0-1052-azure-x86_64-with-glibc2.39` |
| `jsonschema` | 4.26.0 |
| `jsonschema-specifications` | 2025.9.1 |
| `pytest` | 8.4.2 |
| `ruff` | 0.15.22 |
| `torch` | not installed |
| `transformers` | not installed |

`torch`/`transformers` are absent because this scaffold's `pyproject.toml` only declares
`jsonschema` (plus `pytest`/`ruff` as dev extras) — see `requirements-lock.txt`. Their pinned
versions should come from the upstream repo's own dependency file once its commit is set, not be
chosen independently here.

## 3. Toy CPU chain timing — measured

Command actually run in this environment:

```
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
```

Config: `configs/experiment/toy_cpu.json` — policy `joint`, horizon 3 generations, no real model.

**Cold CLI invocation** (`time python -m ...`, includes Python interpreter startup and imports):

| Metric | Value |
|---|---:|
| Wall clock (`real`) | 0.105 s |
| `user` | 0.071 s |
| `sys` | 0.018 s |

**In-process orchestration only** (`run_toy_chain(config, output_dir=...)` called directly, 5
repeated fresh runs, excludes interpreter startup):

| Metric | Value |
|---|---:|
| Per-run wall time (5 samples) | 0.0041 – 0.0095 s |
| Mean per-run wall time | 0.0057 s |
| Mean per-generation wall time | 0.0019 s |
| Peak RSS (whole Python process) | ~14.6 MiB |

This isolates the runner's own overhead (allocation, checkpoint I/O with fsync, manifest writes) at
sub-millisecond-per-generation cost — useful for knowing the orchestration layer won't be the
bottleneck once a real training step replaces the toy one, but it says nothing about real model
compute time.

## 4. Storage used by the run directory — measured

Same run as above, `runs/fixture_joint_seed1/`:

| File | Bytes |
|---|---:|
| `run_manifest.json` | 955 |
| `chain_result.json` | 582 |
| `allocation_note.txt` | 46 |
| `checkpoints/generation_0000.json` | 688 |
| `checkpoints/generation_0001.json` | 1,217 |
| `checkpoints/generation_0002.json` | 1,745 |
| **Total (apparent size)** | **5,233 bytes (~5.1 KiB)** |
| Total (disk block allocation, `du -sh`) | 32 KiB |

`runs/` is gitignored; nothing here is committed to the repository.

## 5. Hardware this Codespace reports — measured

| Field | Value |
|---|---|
| Environment | GitHub Codespaces (`CODESPACES=true`) |
| CPU | AMD EPYC 7763 64-Core Processor (host), 2 vCPUs allocated to this Codespace |
| Memory | 7.8 GiB total, ~3.0 GiB available at measurement time |
| Disk | 32 GiB overlay filesystem, 19 GiB available |
| GPU | none (`nvidia-smi` not found) |

This is a standard small Codespaces machine type, not accelerator hardware. It cannot run a real
GPT-2-class training job in a reasonable time and was never intended to — it hosts the toy
orchestration fixture only.

## 6. Forecast: full (non-toy) positive-control run — estimate, not measured

**This section is a formula-based engineering estimate, explicitly not a substitute for the real
one-generation smoke-run measurement `COMPUTE.md` requires as the forecast's actual basis.** It
exists to give an order-of-magnitude sense of scale while Stage A is blocked (see §1). Every number
below is derived from public, citable facts (GPT-2 124M parameter count; the standard
compute-per-token training rule) combined with explicitly stated example assumptions, not from
anything actually run.

**Compute, per generation, per arm.** Training FLOPs for a transformer are commonly approximated as
`C ≈ 6 × N × D` (Kaplan et al., 2020), where `N` = 124,000,000 parameters and `D` = training tokens
processed. The upstream repo's actual dataset size and step count are unknown until its commit is
pinned (§1), so two illustrative token-count scenarios are shown — **neither is the planned
experiment's real dataset size**:

| Scenario (illustrative only) | Tokens `D` | Training FLOPs (`6ND`) |
|---|---:|---:|
| Small smoke-scale | 10M tokens | 7.4 × 10^15 |
| Larger replication-scale | 300M tokens | 2.2 × 10^17 |

**Accelerator-hours, per generation, per arm**, assuming ~30% achieved utilization of peak FLOPS
(typical for small-model training, not a measured figure) on two illustrative GPU classes:

| GPU (spec-sheet peak, fp16/bf16) | Small scenario | Larger scenario |
|---|---:|---:|
| T4 (~65 TFLOPS) | 0.106 h | 3.18 h |
| A100 (~312 TFLOPS) | 0.022 h | 0.66 h |

**Full Stage A** is 2 arms × 10 generations. Generations within one arm depend on the prior
checkpoint and run sequentially; the 2 arms are independent and can run concurrently on separate
accelerators. Multiplying the per-generation figures above by 10 generations:

| GPU | Wall-clock for 10 generations, 1 arm (= both arms in parallel on 2 GPUs) | Total accelerator-hours, both arms (2 × the 1-arm figure) |
|---|---:|---:|
| T4, small scenario | 1.06 h | 2.12 GPU-h |
| T4, larger scenario | 31.8 h | 63.6 GPU-h |
| A100, small scenario | 0.22 h | 0.44 GPU-h |
| A100, larger scenario | 6.6 h | 13.2 GPU-h |

**Storage, per checkpoint**, from parameter count alone (no optimizer state): `124M params × 4
bytes` (fp32) ≈ 496 MB, or ≈ 248 MB at fp16. Saving one checkpoint per generation across 20
generation-runs gives roughly **5–10 GB** for model checkpoints alone, before generated-text and
log artifacts (expected to be small relative to checkpoints, KB–MB scale).

**Why this range is wide and non-authoritative:** the true dataset size, batch size, step count, and
GPU allocation are all unknown until the upstream commit is pinned and its config is read — that is
exactly the "measured from one-generation smoke run" step `COMPUTE.md` requires before this becomes
a real forecast rather than a formula sanity check.

## Next steps (blocked on external input)

- Repo owner supplies the exact upstream commit hash for `PROTOCOL.md`.
- Provision an environment with `torch`/`transformers` and GPU access.
- Run one real GPT-2 124M-class generation, record actual wall time/accelerator-hours/peak
  memory/storage written, and replace §6's formula estimate with that measurement as the stated
  basis for the full Stage A forecast in `COMPUTE.md`.
