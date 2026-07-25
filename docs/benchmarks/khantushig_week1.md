# Week 1 Compute Benchmark — Khantushig

**Scope:** `week-1/khantushig-recursive-runner`. Two things are reported separately and must not be
conflated: (1) measured toy-runner orchestration overhead, and (2) the real positive-control
generation benchmark, which is **not yet possible in this environment** and remains blocked.

## 1. Toy CPU chain — measured

This is an engineering smoke measurement of the runner's own overhead (allocation, checkpointing,
manifest I/O). It uses no real model and is not scientific evidence of anything about recursive
training — see `docs/RUNBOOK.md` and `PROTOCOL.md` §5 (no-result rule).

- Command: `python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json`
- Config: `configs/experiment/toy_cpu.json` — policy `joint`, horizon 3 generations.
- Environment: `Linux-6.8.0-1052-azure-x86_64`, Python 3.12.1, 2 vCPU, 7.8 GiB RAM, no GPU.
- Method: 5 repeated fresh runs via `run_toy_chain(config, output_dir=...)`, wall time via
  `time.perf_counter()`, peak resident set size via `resource.getrusage`.

| Metric | Value |
|---|---:|
| Per-run wall time (5 samples) | 0.0018 – 0.0023 s |
| Mean per-run wall time | 0.0020 s |
| Mean per-generation wall time | 0.00065 s |
| Peak RSS (whole process) | ~14.6 MiB |
| On-disk artifacts per run (manifest + 3 checkpoints + chain_result) | ~5.1 KB |

This confirms the checkpoint/manifest/resume machinery adds negligible, sub-millisecond overhead
per generation — useful for knowing the runner itself won't be the bottleneck once a real training
step is substituted in, but it says nothing about real model compute.

## 2. Real positive-control generation — blocked, not run

`PROTOCOL.md` Stage A calls for one measured generation of the GPT-2 124M-class positive control
(Drayson, Yilmaz & Lampos, EMNLP 2025) to forecast accelerator-hours and storage for the full
10-generation, 2-arm reproduction. That measurement **has not been taken** because three
prerequisites are unmet in this environment as of 2026-07-25:

1. **Upstream commit is not pinned.** `PROTOCOL.md` records a `TODO(khantushig)` placeholder for
   the exact commit hash of `https://github.com/GeorgeDrayson/model_collapse`, pending a value
   supplied by the repo owner — not invented here.
2. **No ML framework is installed.** This dev environment only carries `jsonschema`/`pytest`/`ruff`
   (see `requirements-lock.txt`); `torch` and `transformers` are absent, and their pinned versions
   should come from the upstream repo's own dependency file once the commit above is set.
3. **No accelerator is present.** This environment has 2 vCPUs and no GPU.

Per `COMPUTE.md`, the positive-control forecast row's basis is explicitly "must be measured from
one-generation smoke run" — extrapolating accelerator-hours/storage without that measurement would
mean presenting an invented number as an estimate, which `PROTOCOL.md` §5 and `COMPUTE.md`'s
"Forecasts must state assumptions and may not be presented as actual usage" both rule out. The
`COMPUTE.md` forecast row therefore stays `TBD`/`Not estimated` until the commit is pinned and a
real one-generation smoke run executes on accelerator hardware.

## Next steps (blocked on external input)

- Repo owner supplies the exact upstream commit hash for `PROTOCOL.md`.
- Provision an environment with `torch`/`transformers` and GPU access.
- Run one real GPT-2 124M-class generation, record wall time/accelerator-hours/peak memory/storage
  written, and use that single measurement as the stated basis for the full Stage A forecast in
  `COMPUTE.md`.
