# Kaggle runbook — Stage A smoke test

Procedure for measuring the official one-generation smoke run on Kaggle Notebooks, so
`COMPUTE.md`'s forecast can rest on a measurement instead of a formula.

**This runbook produces a compute measurement, not a scientific result.** The smoke test
runs one recursive iteration on 100 generated samples. It is not a positive-control arm and
must never be reported as one (`PROTOCOL.md` §5).

Upstream commit under test: `feb8511479a2e2dc868e1caf3f63cb99f1fcc746`.

## 0. Findings that shape this procedure

Each was read from the upstream source at the pinned commit, not assumed.

### 0.1 Upstream is single-GPU; the second T4 will idle

`main.py:33` sets `os.environ["CUDA_VISIBLE_DEVICES"] = str(cfg.cuda_device)` before every
`subprocess.run`, and `src/generate.py` defaults `--device` to `cuda:0` (`main.py` never
passes `--device`). Each subprocess therefore sees exactly one device and Hugging Face
`Trainer` reports `n_gpu: 1`.

Consequences for a `T4 x2` session:

- **Do not set `CUDA_VISIBLE_DEVICES` in the notebook to select a GPU.** `main.py`
  overwrites it, and the child interprets the new value against the physical device list,
  so a notebook-level `"1"` still lands on physical GPU 0. Use the Hydra override
  `cuda_device=0` or `cuda_device=1` instead — that is the only working selector.
- A single arm gains nothing from the second GPU. For the *full* Stage A run later, the
  two arms are independent and can run concurrently with `cuda_device=0` and
  `cuda_device=1`.
- For a clean benchmark number, run the smoke test alone on `cuda_device=0` with nothing
  else on the device.

### 0.2 `smoke_test=true` shrinks generation only, not training

`main.py:48-52` sets `num_samples = "100"` and `num_iterations = 1`, but `num_samples` is
appended **only** to the `src/generate.py` command (`main.py:104-105`). Neither
`src/train.py` invocation receives it.

So the smoke test performs:

| Phase | Scale |
|---|---|
| Iteration 0 training | **full** WikiText-2 train split |
| Iteration 0 evaluation | full test split |
| Iteration 1 generation | **100 samples only** |
| Iteration 1 training | the 100 generated texts |
| Iteration 1 evaluation | full test split |

Multiplying total smoke wall time by 22 therefore **underestimates Stage A badly**: real
generations decode every example in the split, not 100. §5 measures the decode rate
separately and scales it properly.

### 0.3 `wandb.init` is never reached

`main.py:25` guards initialisation with `if not bool(str(cfg.wandb_disabled))`. In Python
`bool("False")` is `True`, so the negation is always `False` and `wandb.init` never runs —
yet `src/train.py:683` and `src/generate.py` call `wandb.log` regardless. Set
`WANDB_DISABLED` and `WANDB_MODE` at the notebook level as insurance (cell 2). If a wandb
call still raises, that is an upstream defect: record it in `FAILURE_LOG.md` as an
`implementation_defect` in the upstream code, with the traceback.

### 0.4 Where artifacts actually land

`src/train.py:652` saves the model with
`trainer.save_model(os.path.join(training_args.output_dir, "final_model"))`, and
`trainer.save_metrics("train"|"eval", ...)` writes `train_results.json` and
`eval_results.json` into the same `output_dir`. `main.py` sets `output_dir` to
`{experiment_path}/{iteration}/model/`, and `src/generate.py` writes
`{experiment_path}/{iteration}/data.json`.

`eval_results.json` contains `eval_loss`, `perplexity`, `eval_accuracy`, and
`eval_runtime`; `train_results.json` contains `train_runtime`. Those runtime fields are
measured by `Trainer` itself and are the trustworthy timing source — more reliable than
wall-clock subtraction, which at smoke scale is dominated by model downloads and
tokenisation.

### 0.5 Decoding batch size, and why it sets the cost

`src/generate.py:32` defaults `--batch_size` to `32`, and `main.py` never overrides it, so
every generation decodes the training split in batches of 32 with `max_new_tokens=256`
(`src/generate.py:90`). For a ~4,600-block WikiText-2 split that is roughly 145 batches ×
256 sequential decode steps per generation.

Decoding is sequential and memory-bandwidth bound, so it dominates the per-generation cost
— training the same split is a few hundred optimizer steps and finishes in minutes. Any
useful estimate of Stage A is therefore an estimate of decode throughput, which is what §7
measures.

### 0.6 bfloat16 on a T4 — check this before trusting any timing

Upstream sets `torch_dtype: bfloat16` (`config/config.yaml`). The T4 is Turing, compute
capability 7.5, which has **no bfloat16 tensor cores** — bf16 tensors work but fall back to
slower paths, and `torch.cuda.is_bf16_supported()` typically reports `False`. Cell 1
captures both values.

If `torch_bf16_supported` is `False`, decoding may run several times slower than the same
work in fp16, and the §7 measurement will reflect that. Three responses, in order of
preference:

1. **Accept it and measure.** The frozen config stays intact; Stage A simply costs more.
   This is the default and it keeps the reproduction faithful.
2. **Run on a bf16-capable accelerator** (A100, L4, or Kaggle's TPU-adjacent options are
   not equivalent — an Ampere-or-later GPU is what is needed). No deviation, faster.
3. **Change `torch_dtype` to `float16`.** This is a **scientific deviation** from the
   pinned upstream configuration: fp16 has a narrower exponent range than bf16 and can
   change training dynamics and generated text. If chosen, it must be recorded in
   `PROTOCOL.md` and in `expected_vs_observed.md` §6 *before* running, and the reproduction
   reported as `valid_with_limitation` at best. Do not make this change to save time and
   then describe the run as a faithful reproduction.

### 0.7 Kaggle-specific constraints

| Constraint | Effect |
|---|---|
| `/kaggle/working` is 20 GB and persists **only** via *Save & Run All (Commit)* | Every artifact worth keeping must be written there before the commit ends |
| Internet is off by default | pip and git fail until *Settings → Internet → On* (needs a phone-verified account) |
| 12 h hard cap, no idle disconnect | Ample for the smoke test; not enough for a full arm |
| Hugging Face cache defaults to `/root/.cache` | Ephemeral, and not counted against `/kaggle/working`. Leave it there for the smoke test to preserve working space |

Storage and session limits used to rule Kaggle out for the full Stage A run. Section 12
resolves both: arms advance one generation at a time and can be resumed across sessions,
and superseded model directories are pruned after hashing, cutting peak storage from
roughly 11 GB to roughly 1.5 GB.

## 1. Cell 1 — GPU and environment record

Writes `/kaggle/working/environment.json`. Every value is read from the machine; none is
assumed.

```python
# CELL 1 — environment capture
import json, os, platform, subprocess, sys
from pathlib import Path

WORK = Path("/kaggle/working")
WORK.mkdir(parents=True, exist_ok=True)

def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception as exc:
        return f"unavailable: {exc}"

env = {
    "captured_at_utc": sh("date -u +%Y-%m-%dT%H:%M:%SZ"),
    "host": "kaggle-notebooks",
    "python": platform.python_version(),
    "platform": platform.platform(),
    "cpu_count": os.cpu_count(),
    "nvidia_smi_query": sh(
        "nvidia-smi --query-gpu=index,name,driver_version,memory.total "
        "--format=csv,noheader"
    ),
    "cuda_version_from_smi": sh("nvidia-smi | sed -n 's/.*CUDA Version: \\([0-9.]*\\).*/\\1/p'"),
}

for mod in ("torch", "transformers", "datasets", "accelerate", "hydra"):
    try:
        m = __import__(mod)
        env[mod] = getattr(m, "__version__", "unknown")
    except ImportError:
        env[mod] = "not_installed"

try:
    import torch
    env["torch_cuda_available"] = torch.cuda.is_available()
    env["torch_cuda_version"] = torch.version.cuda
    env["torch_device_count"] = torch.cuda.device_count()
    env["torch_device_names"] = [
        torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
    ]
    env["torch_compute_capability"] = [
        ".".join(map(str, torch.cuda.get_device_capability(i)))
        for i in range(torch.cuda.device_count())
    ]
    # Upstream sets torch_dtype=bfloat16. Turing (T4, capability 7.5) has no bf16
    # tensor cores, so bf16 falls back to slow paths. See section 0.6.
    env["torch_bf16_supported"] = bool(torch.cuda.is_bf16_supported())
except Exception as exc:
    env["torch_probe_error"] = str(exc)

(WORK / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
print(json.dumps(env, indent=2))
```

**Stop if** `torch_cuda_available` is `False` or `nvidia_smi_query` is empty — the
accelerator is not attached. Fix *Settings → Accelerator → GPU T4 x2* before continuing.

Expect `torch_device_count` to be `2`. That is fine; §0.1 explains why only one is used.

## 2. Cell 2 — upstream checkout and dependencies

```python
# CELL 2 — upstream at the pinned commit
import os, subprocess
from pathlib import Path

os.environ["WANDB_DISABLED"] = "true"
os.environ["WANDB_MODE"] = "disabled"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

UPSTREAM = Path("/kaggle/working/model_collapse")
COMMIT = "feb8511479a2e2dc868e1caf3f63cb99f1fcc746"

if not (UPSTREAM / ".git").exists():
    subprocess.run(
        ["git", "clone", "https://github.com/GeorgeDrayson/model_collapse", str(UPSTREAM)],
        check=True,
    )
subprocess.run(["git", "-C", str(UPSTREAM), "checkout", COMMIT], check=True)

head = subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
assert head == COMMIT, f"upstream is at {head}, expected {COMMIT}"
print("upstream pinned at", head)
```

```python
# CELL 2b — dependencies (slow; several minutes)
!pip install -q "git+https://github.com/huggingface/transformers" 2>&1 | tail -5
!pip install -q -r /kaggle/working/model_collapse/requirements.txt 2>&1 | tail -5
```

**Watch this step.** `requirements.txt` declares `torch >= 1.3`, and installing
`transformers` from source can pull a different `torch` than Kaggle preinstalls. Re-run
cell 1 afterwards and compare `torch` and `torch_cuda_available`. If CUDA stopped working,
that is an infrastructure failure: record the before/after versions in `FAILURE_LOG.md`
rather than silently pinning something upstream does not pin.

## 3. Cell 3 — prepare the dataset

```python
# CELL 3 — dataset preparation
import json, subprocess
from pathlib import Path

UPSTREAM = Path("/kaggle/working/model_collapse")
result = subprocess.run(["python", "src/load_data.py"], cwd=UPSTREAM,
                        capture_output=True, text=True)
print(result.stdout[-3000:])
print(result.stderr[-3000:])
result.check_returncode()

data_dir = UPSTREAM / "data" / "wikitext2"
for split in ("train", "test"):
    path = data_dir / f"{split}.json"
    assert path.is_file(), f"missing {path}"
    records = json.loads(path.read_text(encoding="utf-8"))
    print(f"{split}.json: {len(records)} records, {path.stat().st_size/1e6:.1f} MB")
```

`src/utils/utils.py:145` writes these as a JSON array of `{"text": ...}` objects, so
`len(json.load(...))` is the example count. **The record counts are not known until this
cell runs** — they are the `N` that §5's extrapolation scales by.

## 4. Cell 4 — your repository

The PAT comes from *Add-ons → Secrets* (add a secret named `GITHUB_PAT`). It is never
written into a cell, and the clone URL with the token embedded is never printed.

```python
# CELL 4 — project repo
import subprocess
from pathlib import Path
from kaggle_secrets import UserSecretsClient

REPO = Path("/kaggle/working/algoverse-summer-26")
BRANCH = "week-2/khantushig-positive-control"

if not (REPO / ".git").exists():
    token = UserSecretsClient().get_secret("GITHUB_PAT")
    url = f"https://x-access-token:{token}@github.com/guptaneil1/algoverse-summer-26.git"
    subprocess.run(["git", "clone", url, str(REPO)], check=True,
                   capture_output=True)   # capture_output keeps the token out of the log
    del token, url

subprocess.run(["git", "-C", str(REPO), "checkout", BRANCH], check=True)
subprocess.run(["git", "-C", str(REPO), "remote", "set-url", "origin",
                "https://github.com/guptaneil1/algoverse-summer-26.git"], check=True)
print(subprocess.run(["git", "-C", str(REPO), "log", "--oneline", "-3"],
                     capture_output=True, text=True).stdout)
```

The `remote set-url` scrubs the token from `.git/config`, so committing the notebook does
not publish the credential. Re-supply it from the secret when you push.

```python
# CELL 4b — editable install
!pip install -q -e /kaggle/working/algoverse-summer-26 --no-deps
!pip install -q jsonschema
!cd /kaggle/working/algoverse-summer-26 && python -m pytest tests/runner -q 2>&1 | tail -3
```

The test run confirms the adapter imports correctly in this environment before any GPU
time is spent.

## 5. Cell 5 — the smoke test, timed, with peak GPU memory

```python
# CELL 5 — smoke test with a background memory sampler
import json, subprocess, time
from pathlib import Path

UPSTREAM = Path("/kaggle/working/model_collapse")
SMOKE = Path("/kaggle/working/smoke")
SMOKE.mkdir(parents=True, exist_ok=True)
EXP = SMOKE / "exp"
LOG = SMOKE / "smoke_stdout_stderr.log"
MEMLOG = SMOKE / "gpu_memory_samples.csv"

sampler = subprocess.Popen(
    ["nvidia-smi",
     "--query-gpu=timestamp,index,memory.used,utilization.gpu",
     "--format=csv,noheader,nounits", "-l", "5"],
    stdout=open(MEMLOG, "w"), stderr=subprocess.DEVNULL,
)

start = time.perf_counter()
try:
    with open(LOG, "w") as log:
        proc = subprocess.run(
            ["python", "main.py",
             "smoke_test=true",
             "wandb_disabled=true",
             "data_selection=no-selection",
             "cuda_device=0",
             f"hydra.run.dir={EXP}"],
            cwd=UPSTREAM, stdout=log, stderr=subprocess.STDOUT,
        )
finally:
    elapsed = time.perf_counter() - start
    sampler.terminate()
    sampler.wait(timeout=10)

print(f"exit code: {proc.returncode}")
print(f"total wall time: {elapsed:.1f} s ({elapsed/60:.2f} min)")
print(open(LOG).read()[-4000:])
```

Notes on this invocation:

- `cuda_device=0` is the Hydra override, per §0.1. Do not substitute an env var.
- `hydra.run.dir={EXP}` makes the output path deterministic. Without it, `config.yaml`
  routes output to a timestamped directory you would have to hunt for.
- If the run fails with `can't open file 'src/train.py'`, your Hydra version is changing
  the working directory. Add `hydra.job.chdir=False` to the override list.

```python
# CELL 5b — peak GPU memory from the samples
import csv
from pathlib import Path

MEMLOG = Path("/kaggle/working/smoke/gpu_memory_samples.csv")
peaks = {}
with open(MEMLOG) as handle:
    for row in csv.reader(handle):
        if len(row) < 4:
            continue
        index, used = row[1].strip(), int(row[2])
        peaks[index] = max(peaks.get(index, 0), used)

for index, used in sorted(peaks.items()):
    print(f"GPU {index}: peak {used} MiB used")
print("\nGPU 1 staying near idle confirms the single-GPU behaviour in section 0.1.")
```

The sampler polls every 5 s, so it can miss a shorter spike. It is a lower bound on peak
memory, and should be recorded as such.

## 6. Cell 6 — artifacts, timings, storage

```python
# CELL 6 — what the run actually produced
import json
from pathlib import Path

EXP = Path("/kaggle/working/smoke/exp")

print("=== tree ===")
for path in sorted(EXP.rglob("*")):
    if path.is_file():
        print(f"{path.relative_to(EXP)}  ({path.stat().st_size/1e6:.2f} MB)")

timings = {}
for iteration in sorted(p.name for p in EXP.iterdir() if p.name.isdigit()):
    model_dir = EXP / iteration / "model"
    entry = {}
    for name in ("train_results.json", "eval_results.json"):
        path = model_dir / name
        if path.is_file():
            entry[name] = json.loads(path.read_text(encoding="utf-8"))
        else:
            entry[name] = None
            print(f"MISSING: {path}")
    timings[iteration] = entry

print("\n=== Trainer-reported metrics ===")
print(json.dumps(timings, indent=2)[:4000])

Path("/kaggle/working/smoke/timings.json").write_text(
    json.dumps(timings, indent=2), encoding="utf-8"
)
```

```python
# CELL 6b — storage
!du -sh /kaggle/working/smoke/exp
!du -sh /kaggle/working/model_collapse/data
!du -sh /root/.cache/huggingface 2>/dev/null || echo "no HF cache at /root/.cache"
!df -h /kaggle/working | tail -1
```

Expected keys are `train_runtime` in `train_results.json` and `eval_runtime`,
`eval_loss`, `perplexity`, `eval_accuracy` in `eval_results.json` (§0.4). **If a key is
absent, do not substitute a guess** — print the file and record what upstream actually
produced.

## 7. Cell 7 — decode rate (required before extrapolating)

Per §0.2 the smoke test decodes only 100 samples. This measures decode cost as a function
of sample count with a two-point fit `t(n) = a + b·n`, so `b` (per-sample seconds) can be
scaled to the real split size. Without it, any Stage A estimate is wrong.

The arguments replicate `main.py:88-107` exactly, against a throwaway experiment path so
the smoke artifacts are not clobbered.

```python
# CELL 7 — two-point decode measurement
import subprocess, time
from pathlib import Path

UPSTREAM = Path("/kaggle/working/model_collapse")
EXP = Path("/kaggle/working/smoke/exp")
SCRATCH = Path("/kaggle/working/smoke/decode_probe")
SCRATCH.mkdir(parents=True, exist_ok=True)

MODEL_PATH = EXP / "0" / "model" / "final_model"
assert MODEL_PATH.is_dir(), f"no trained model at {MODEL_PATH}; cell 5 must succeed first"

def time_generation(num_samples, iteration):
    command = [
        "python", "src/generate.py",
        "--model_name", "openai-community/gpt2",
        "--model_path", str(MODEL_PATH),
        "--input_token_length", "256",          # block_size - loss_on_last_n_tokens
        "--block_size", "512",
        "--iteration", str(iteration),
        "--experiment_path", str(SCRATCH),
        "--dataset_filepath", str(UPSTREAM / "data/wikitext2/train.json"),
        "--seed", "42",
        "--temperature", "1.0",
        "--top_p", "1.0",
        "--top_k", "50",
        "--torch_dtype", "bfloat16",
        "--low_cpu_mem_usage", "True",
        "--classify_text", "1",
        "--detector_tokenizer_name", "GeorgeDrayson/modernbert-ai-detection",
        "--detector_path", "GeorgeDrayson/modernbert-ai-detection",
        "--detector_threshold", "0.8674598932266235",
        "--detector_temperature", "1.359828233718872",
        "--num_samples", str(num_samples),
    ]
    log = SCRATCH / f"generate_{num_samples}.log"
    start = time.perf_counter()
    with open(log, "w") as handle:
        proc = subprocess.run(command, cwd=UPSTREAM, stdout=handle,
                              stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        print(open(log).read()[-3000:])
        raise RuntimeError(f"generation failed for n={num_samples}")
    print(f"n={num_samples}: {elapsed:.1f} s")
    return elapsed

t_100 = time_generation(100, 901)
t_300 = time_generation(300, 902)

per_sample = (t_300 - t_100) / 200.0
fixed_overhead = t_100 - per_sample * 100
print(f"\nper-sample decode+classify: {per_sample:.3f} s")
print(f"fixed overhead per generation call: {fixed_overhead:.1f} s")

import json
Path("/kaggle/working/smoke/decode_rate.json").write_text(json.dumps({
    "t_100_seconds": t_100, "t_300_seconds": t_300,
    "per_sample_seconds": per_sample, "fixed_overhead_seconds": fixed_overhead,
}, indent=2), encoding="utf-8")
```

A two-point fit assumes decode cost is linear in sample count. That is reasonable here
(each sample decodes a fixed 256 tokens), but it is an assumption — state it wherever you
quote the result. If `per_sample` comes out negative or near zero, the run was dominated by
fixed overhead; add a third point at `n=600` before trusting it.

## 8. Cell 8 — extrapolation to a full arm and to Stage A

```python
# CELL 8 — extrapolate, with every assumption printed
import json
from pathlib import Path

SMOKE = Path("/kaggle/working/smoke")
UPSTREAM = Path("/kaggle/working/model_collapse")

timings = json.loads((SMOKE / "timings.json").read_text(encoding="utf-8"))
decode = json.loads((SMOKE / "decode_rate.json").read_text(encoding="utf-8"))
n_train = len(json.loads(
    (UPSTREAM / "data/wikitext2/train.json").read_text(encoding="utf-8")))

train_full = timings["0"]["train_results.json"]["train_runtime"]
eval_full = timings["0"]["eval_results.json"]["eval_runtime"]

gen_full = decode["fixed_overhead_seconds"] + decode["per_sample_seconds"] * n_train

HORIZON = 11          # generations 0..10, PROTOCOL.md
GENERATING = 10       # iterations 1..10 each decode once

synthetic_arm = (train_full + eval_full) + GENERATING * (gen_full + train_full + eval_full)
mixed_arm = (train_full + eval_full) + GENERATING * (gen_full + 2 * train_full + eval_full)
stage_a = synthetic_arm + mixed_arm

def hours(seconds):
    return seconds / 3600.0

print(f"measured  train (full split)      : {train_full:8.1f} s")
print(f"measured  eval  (full test split) : {eval_full:8.1f} s")
print(f"measured  decode per sample       : {decode['per_sample_seconds']:8.3f} s")
print(f"measured  train.json record count : {n_train:8d}")
print(f"derived   generation decode cost  : {gen_full:8.1f} s  ({hours(gen_full):.2f} h)")
print()
print(f"fully synthetic arm ({HORIZON} generations): {hours(synthetic_arm):6.2f} GPU-h")
print(f"human mixed arm     ({HORIZON} generations): {hours(mixed_arm):6.2f} GPU-h")
print(f"STAGE A TOTAL (both arms, sequential)     : {hours(stage_a):6.2f} GPU-h")
print(f"STAGE A WALL CLOCK (arms in parallel, 2 GPUs): {hours(max(synthetic_arm, mixed_arm)):6.2f} h")
print()
print("Assumptions, all of which must travel with these numbers:")
print(" - decode cost is linear in sample count (two-point fit, cell 7)")
print(" - the human-mixed arm's training set is ~2x the synthetic arm's, because")
print("   human_data_alpha=1.0 appends the full human split (src/train.py:548);")
print("   training time is assumed proportional to training-set size")
print(" - per-generation eval cost equals the measured iteration-0 eval cost")
print(" - no host preemption, no retries, no download time after the first generation")
print(" - measured on this GPU only; see environment.json for which one")

Path(SMOKE / "extrapolation.json").write_text(json.dumps({
    "measured_train_runtime_seconds": train_full,
    "measured_eval_runtime_seconds": eval_full,
    "measured_per_sample_decode_seconds": decode["per_sample_seconds"],
    "measured_train_record_count": n_train,
    "derived_generation_decode_seconds": gen_full,
    "estimated_fully_synthetic_arm_hours": hours(synthetic_arm),
    "estimated_human_mixed_arm_hours": hours(mixed_arm),
    "estimated_stage_a_total_gpu_hours": hours(stage_a),
}, indent=2), encoding="utf-8")
```

The arm figures are **derived**, not measured: they combine measured per-phase costs under
the stated assumptions. Only `train_runtime`, `eval_runtime`, the decode timings, and the
record count are measurements. Label them that way in
`docs/benchmarks/khantushig_week2.md`, which already separates the two.

## 9. Cell 9 — preserve everything for the notebook commit

```python
# CELL 9 — collect the record
import json, shutil, subprocess
from pathlib import Path

WORK = Path("/kaggle/working")
OUT = WORK / "stage_a_smoke_record"
OUT.mkdir(parents=True, exist_ok=True)

for name in ("environment.json",):
    shutil.copy(WORK / name, OUT / name)
for name in ("timings.json", "decode_rate.json", "extrapolation.json",
             "smoke_stdout_stderr.log", "gpu_memory_samples.csv"):
    source = WORK / "smoke" / name
    if source.is_file():
        shutil.copy(source, OUT / name)
    else:
        print(f"missing (record why): {source}")

EXP = WORK / "smoke" / "exp"
for path in EXP.rglob("*.json"):
    if path.name in ("train_results.json", "eval_results.json", "all_results.json"):
        target = OUT / f"iter{path.parent.parent.name}_{path.name}"
        shutil.copy(path, target)

manifest = {
    "upstream_commit": subprocess.run(
        ["git", "-C", str(WORK / "model_collapse"), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip(),
    "project_commit": subprocess.run(
        ["git", "-C", str(WORK / "algoverse-summer-26"), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip(),
    "files": sorted(p.name for p in OUT.iterdir()),
    "note": "Compute measurement only. Not a positive-control result (PROTOCOL.md section 5).",
}
(OUT / "record_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
```

**Then click *Save Version → Save & Run All (Commit)*.** Nothing under `/kaggle/working`
survives otherwise. Model checkpoints are large and are deliberately excluded from
`stage_a_smoke_record/`; only metrics, logs, and the environment record are preserved.

## 10. Cell 10 — resolve the deferred identifiers

The committed configs carry `resolve_at_runtime` in four places, and the adapter refuses to
run until they are filled. This host has Hugging Face access, so resolve them here and
commit the result **before** any arm runs.

```python
# CELL 10 — resolve model, tokenizer, and dataset revisions
import hashlib, json, subprocess
from pathlib import Path
from huggingface_hub import HfApi

REPO = Path("/kaggle/working/algoverse-summer-26")
UPSTREAM = Path("/kaggle/working/model_collapse")
api = HfApi()

gpt2_sha = api.model_info("openai-community/gpt2").sha
detector_sha = api.model_info("GeorgeDrayson/modernbert-ai-detection").sha
wikitext_sha = api.dataset_info("wikitext").sha

digest = hashlib.sha256()
with open(UPSTREAM / "data/wikitext2/train.json", "rb") as handle:
    while chunk := handle.read(1024 * 1024):
        digest.update(chunk)
train_sha = digest.hexdigest()

print("gpt2            :", gpt2_sha)
print("detector        :", detector_sha)
print("wikitext        :", wikitext_sha)
print("train.json      :", train_sha)

resolutions = {
    ("model", "revision"): gpt2_sha,
    ("model", "tokenizer_revision"): gpt2_sha,
    ("data", "revision"): wikitext_sha,
    ("data", "train_manifest_sha256"): train_sha,
}

for arm in ("fully_synthetic", "human_mixed"):
    path = REPO / f"configs/experiment/positive_control_{arm}.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    for (section, key), value in resolutions.items():
        assert config[section][key] == "resolve_at_runtime", (
            f"{arm}: {section}.{key} is already {config[section][key]!r}; "
            "refusing to overwrite an existing pin"
        )
        config[section][key] = value
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print("resolved", path.name)

# The detector revision is recorded for the record; upstream pins no detector revision
# either, and the adapter does not gate on it.
(REPO / "docs/positive_control/resolved_identifiers.json").write_text(
    json.dumps({
        "gpt2": gpt2_sha, "detector": detector_sha,
        "wikitext": wikitext_sha, "train_json_sha256": train_sha,
    }, indent=2) + "\n", encoding="utf-8")

print(subprocess.run(["git", "-C", str(REPO), "diff", "--stat"],
                     capture_output=True, text=True).stdout)
```

The assertion is deliberate: re-running this cell after the identifiers are pinned will
fail rather than silently re-resolve them against whatever Hugging Face serves that day.

Verify the refusal is now lifted, then commit:

```python
# CELL 10b — confirm the configs are runnable, then commit
import subprocess, sys
from pathlib import Path
sys.path.insert(0, "/kaggle/working/algoverse-summer-26/src")
from human_data_budget.runner.positive_control_adapter import assert_resolved, load_arm_config

REPO = Path("/kaggle/working/algoverse-summer-26")
for arm in ("fully_synthetic", "human_mixed"):
    assert_resolved(load_arm_config(REPO / f"configs/experiment/positive_control_{arm}.json"))
print("both arm configs are fully resolved")

for command in (
    ["git", "-C", str(REPO), "add", "-A"],
    ["git", "-C", str(REPO), "-c", "user.email=khantushig@example.invalid",
     "-c", "user.name=khantushig", "commit", "-m",
     "chore(positive-control): resolve runtime identifiers on the run host"],
):
    print(subprocess.run(command, capture_output=True, text=True).stdout)
```

Push it with the secret re-supplied (the remote was scrubbed in cell 4):

```python
# CELL 10c — push the freeze
import subprocess
from pathlib import Path
from kaggle_secrets import UserSecretsClient

REPO = Path("/kaggle/working/algoverse-summer-26")
token = UserSecretsClient().get_secret("GITHUB_PAT")
url = f"https://x-access-token:{token}@github.com/guptaneil1/algoverse-summer-26.git"
result = subprocess.run(
    ["git", "-C", str(REPO), "push", url, "week-2/khantushig-positive-control"],
    capture_output=True, text=True,
)
del token, url
print("push ok" if result.returncode == 0 else "push failed; see returncode")
print(result.returncode)
```

The push output is not printed, because the URL containing the token appears in git's
progress messages.

**The published expected values are still missing at this point.** Fill
`docs/positive_control/expected_vs_observed.md` §2.2 from the paper and commit that too
before running any arm — a frozen expectation is only frozen if its timestamp precedes the
run.

## 11. After the notebook

1. Download `stage_a_smoke_record/` from the committed notebook's *Output* tab.
2. Replace §4 of `docs/benchmarks/khantushig_week2.md` with the measured numbers, keeping
   the measured/estimate labelling.
3. Update the Positive control row of `COMPUTE.md`'s forecast table, and change its Basis
   column from a formula to this measurement.
4. If the smoke test failed at any point, append the failure to `FAILURE_LOG.md` with the
   traceback and its classification. A failed smoke test is a finding, not a setback to be
   retried silently.

The smoke test does not unblock Stage A on its own. The remaining prerequisites are
unchanged: resolve the four `resolve_at_runtime` identifiers, extract the published
expected values into `docs/positive_control/expected_vs_observed.md` §2.2, and commit both
before either arm runs.

## 12. Running the full Stage A across several Kaggle sessions

Stage A no longer needs to fit in one session. `scripts/run_positive_control_arm.py`
advances one generation at a time and records each completion, so any number of sessions
can chip away at it. Section 0.1's two source facts are what make this sound; `PROTOCOL.md`
records both as declared deviations.

### 12.1 The unit of work

| Work unit | Count |
|---|---|
| Generation 0 (computed once, shared by both arms) | 1 |
| Fully synthetic, generations 1–10 | 10 |
| Human mixed, generations 1–10 | 10 |
| **Total** | **21** |

Each unit is one `generate` + one `train` (generation 0 is train only). Multiply your §8
per-generation measurement by 21 to see how many units fit in a 12 h session, then set
`--time-budget-seconds` a little under the cap so the session ends on a recorded boundary
instead of being killed mid-generation.

### 12.2 The command, run once per session

Identical every time. It resumes on its own; there is no "continue" flag to remember.

```python
# CELL 11 — one session's worth of Stage A
import subprocess
from pathlib import Path

REPO = Path("/kaggle/working/algoverse-summer-26")
UPSTREAM = Path("/kaggle/working/model_collapse")
RUNS = Path("/kaggle/working/runs/positive_control")

result = subprocess.run([
    "bash", str(REPO / "scripts/reproduce_positive_control.sh"),
    "--repo-root", str(REPO),
    "--upstream-dir", str(UPSTREAM),
    "--config-fully-synthetic",
        str(REPO / "configs/experiment/positive_control_fully_synthetic.json"),
    "--config-human-mixed",
        str(REPO / "configs/experiment/positive_control_human_mixed.json"),
    "--output-root", str(RUNS),
    "--cuda-device", "0",
    "--time-budget-seconds", "39600",   # 11 h, leaving headroom under the 12 h cap
    "--prune-models",
])

print("exit code:", result.returncode)
if result.returncode == 20:
    print("Stopped on a recorded boundary. Re-run this cell in the next session.")
elif result.returncode == 0:
    print("Stage A complete: both arms finished and every hash verified.")
```

**Exit 20 is not a failure.** It means generations remain. Completed generations are
recorded and will not be recomputed.

### 12.3 Carrying state between sessions

Kaggle does not persist `/kaggle/working` across notebook versions by itself. Between
sessions:

1. *Save Version → Save & Run All (Commit)* at the end of each session.
2. In the next version, *Add Data → Your Work → Notebook Output*, selecting the previous
   version's output.
3. Copy the state back before running cell 11:

```python
# CELL 11-PRE — restore the previous session's progress
import shutil
from pathlib import Path

PREVIOUS = Path("/kaggle/input/<previous-notebook-output-slug>/runs")
RUNS = Path("/kaggle/working/runs")

if PREVIOUS.exists() and not RUNS.exists():
    shutil.copytree(PREVIOUS, RUNS)
    print("restored from", PREVIOUS)
else:
    print("nothing to restore; this is either the first session or state already present")
```

The `<previous-notebook-output-slug>` is visible in the *Add Data* panel once attached —
**it depends on your notebook's name and cannot be predicted here.**

With `--prune-models` the carried state is small: metrics, generated data, hash sidecars,
logs, and one live model directory. Without pruning it is tens of gigabytes and will not
fit as a notebook input.

### 12.4 What pruning costs you

Pruned model directories are hashed before deletion and their SHA-256 values survive in
the run record, but the bytes do not — so those hashes can never be re-verified. That is a
genuine weakening of the evidence chain, not a technicality.

After the final session, list them and copy the result into
`docs/positive_control/expected_vs_observed.md` §6.1:

```python
# CELL 12 — disclose pruned artifacts
import json, sys
sys.path.insert(0, "/kaggle/working/algoverse-summer-26/src")
from pathlib import Path
from human_data_budget.runner.positive_control_adapter import (
    pruned_artifacts, verify_recorded_hashes,
)

for arm in ("fully_synthetic", "human_mixed"):
    run_dir = Path("/kaggle/working/runs/positive_control") / arm
    print(f"--- {arm}")
    print("hash mismatches:", verify_recorded_hashes(run_dir) or "none")
    print(json.dumps(pruned_artifacts(run_dir), indent=2))
```

If you would rather keep every artifact re-verifiable, drop `--prune-models` and run on a
host with more than 20 GB. That is the honest trade: storage against verifiability.

## 13. Halving wall clock: both arms at once on the two T4s

§0.1 established that an arm uses one GPU. On a `T4 x2` session the second GPU is idle, and
the two arms are independent, so they can run concurrently — turning Stage A's wall clock
from *two arms* into *one arm*.

The only ordering constraint is the shared generation 0: arm B reuses it, so it must exist
first. It is a single training run of a few minutes.

```python
# CELL 13 — generation 0 once, then both arms in parallel
import subprocess, time
from pathlib import Path

REPO = Path("/kaggle/working/algoverse-summer-26")
UPSTREAM = Path("/kaggle/working/model_collapse")
RUNS = Path("/kaggle/working/runs/positive_control")
DRIVER = REPO / "scripts/run_positive_control_arm.py"
CONFIGS = {
    "fully_synthetic": REPO / "configs/experiment/positive_control_fully_synthetic.json",
    "human_mixed": REPO / "configs/experiment/positive_control_human_mixed.json",
}
BUDGET = "39600"   # 11 h, leaving headroom under the 12 h cap

# Step 1 — generation 0, once, on GPU 0.
step_one = subprocess.run([
    "python", str(DRIVER),
    "--config", str(CONFIGS["fully_synthetic"]),
    "--upstream-dir", str(UPSTREAM),
    "--work-dir", str(RUNS / "fully_synthetic"),
    "--cuda-device", "0",
    "--stop-after-generation", "0",
])
assert step_one.returncode in (0, 20), f"generation 0 failed: {step_one.returncode}"

# Step 2 — both arms concurrently, one per GPU.
processes = {}
for index, (arm, config) in enumerate(CONFIGS.items()):
    command = [
        "python", str(DRIVER),
        "--config", str(config),
        "--upstream-dir", str(UPSTREAM),
        "--work-dir", str(RUNS / arm),
        "--cuda-device", str(index),
        "--time-budget-seconds", BUDGET,
        "--prune-models",
    ]
    if arm != "fully_synthetic":
        command += ["--shared-generation-zero", str(RUNS / "fully_synthetic" / "upstream")]
    log = RUNS / arm / "driver.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    processes[arm] = (subprocess.Popen(command, stdout=open(log, "w"),
                                       stderr=subprocess.STDOUT), log)
    print(f"launched {arm} on GPU {index}, log: {log}")

started = time.perf_counter()
for arm, (process, log) in processes.items():
    code = process.wait()
    print(f"{arm}: exit {code} after {(time.perf_counter()-started)/3600:.2f} h")
    if code == 20:
        print(f"  {arm} has generations remaining — re-run this cell next session")
    elif code != 0:
        print(f"  {arm} FAILED — see {log}")
```

Both arms writing to the same working disk at once roughly doubles the I/O and storage
rate, so keep `--prune-models` on for this path. Re-running the cell is safe: completed
generations are skipped and step 1 becomes a no-op.

**One caveat worth stating.** Running two jobs on one machine means they share host RAM,
disk bandwidth, and dataloader workers, so each arm may be somewhat slower than it would be
alone. The wall-clock win is still large, but the per-arm timings from this path are not
clean single-job benchmarks — if you want the numbers for `COMPUTE.md` to be clean
measurements, take them from the §7 measurement rather than from a parallel run.
