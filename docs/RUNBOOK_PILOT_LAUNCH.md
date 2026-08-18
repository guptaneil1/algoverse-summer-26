# Runbook — launching the primary pilot on RunPod

Step-by-step, from a RunPod account to validated chain artifacts on your laptop.
Written to be followed literally. Every command is copy-pasteable in order.

**What this runs:** `configs/experiment/primary_pilot.json` — 5 arms × 5 seeds = 25
chains, horizon 10.
**Prior estimate:** ~$8 and ~2.8 hours on 4× RTX 4090 (`docs/HANDOVER_2026-08-18.md`).
Not measured this session; treat as an estimate, not a quote.
**What you get:** per-generation curves, between-chain variance for sizing a powered
study, feasibility numbers, and a Gate D artifact. Not a verdict — see
[What to expect](#12-what-to-expect-from-the-result).

---

## 0. Before you start

You need:

- A RunPod account with credit on it. Provisioning and paying is yours to do.
- The repo pushed. As of 2026-08-18 `stage-a/env-freeze` is at `3b4f81b`, and the
  fixed budget guard is in it. A fresh clone of that branch is all the pod needs.
- ~30 minutes of attention at the start, then it runs unattended.

You do **not** need to copy anything from your laptop to the pod. The pod clones from
GitHub and builds its own corpora.

---

## 1. Provision the pod

In the RunPod web console:

1. **Deploy → GPU Cloud**.
2. GPU type **RTX 4090**, count **4**.
3. Template: any recent **PyTorch** template.
4. **Container disk: 30 GB.** **Persistent volume: 80 GB**, mounted at `/workspace`.
5. Enable **Jupyter** (you will use its file browser to pull results off at the end).
6. Deploy, and wait for the pod to report *Running*.

Then **Connect → Start Web Terminal** (or Jupyter → Terminal). Everything below runs in
that shell.

> **Why 4 GPUs.** The launch shards 25 chains four ways, one shard pinned per device.
> Fewer GPUs works — change `--shard-count` and the loop bounds to match — but the wall
> clock scales roughly inversely.

---

## 2. Setup

Paste as one block. Takes a few minutes, mostly `pip`.

```bash
cd /workspace
git clone https://github.com/GeorgeDrayson/model_collapse
cd model_collapse && git checkout feb8511479a2e2dc868e1caf3f63cb99f1fcc746 && cd /workspace
git clone -b stage-a/env-freeze https://github.com/guptaneil1/algoverse-summer-26
pip install -q -r /workspace/model_collapse/requirements.txt
pip install -q transformers==4.48.3 datasets==3.2.0 accelerate==1.2.1 huggingface_hub jsonschema pytest pyarrow hf_transfer
cd /workspace/algoverse-summer-26 && pip install -q -e . --no-deps
echo "=== SETUP DONE ==="
```

Then the wandb shim, as its own block:

```bash
mkdir -p /workspace/shim && cat > /workspace/shim/sitecustomize.py <<'PY'
import os, sys
try:
    import importlib.util
    _p = "/usr/lib/python3.12/sitecustomize.py"
    if os.path.exists(_p):
        _s = importlib.util.spec_from_file_location("_d", _p)
        _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
except Exception:
    pass
if os.environ.get("STAGE_A_WANDB_SHIM") == "1":
    try:
        import wandb
        wandb.init(mode="disabled")
    except Exception as e:
        sys.stderr.write("SHIM FAILED %s\n" % e)
PY
echo "=== SHIM WRITTEN ==="
```

> **Paste this one directly into the pod terminal.** The `<<'PY'` heredoc is quoted, so
> bash writes it literally — but some intermediaries strip backslashes, which would turn
> the `\n` on the last line into a literal newline and break the file. If you routed it
> through anything, check it: `tail -3 /workspace/shim/sitecustomize.py` should show
> `\n` as two characters. This exact class of corruption is recorded in the handover.

Confirm the checkout is the branch you think it is:

```bash
cd /workspace/algoverse-summer-26 && git log --oneline -3
```

You should see `Correct the handover runbook for the P-008 budget check` at the top. If
you don't, you are on the wrong branch and the budget guard will be the broken one.

---

## 3. Sanity-check the environment before spending anything

Free, ~2 minutes, and it catches a bad install before the GPUs matter:

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python -m pytest -q 2>&1 | tail -3
nvidia-smi -L
```

Expect `719 passed, 13 skipped` and four `GPU 0..3` lines. If tests fail here but pass
on your laptop, the environment is wrong — stop and fix it, don't proceed.

---

## 4. Build the corpora

~8 minutes. This downloads WikiText-103 and tokenizes the three partitions.

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/build_base_corpus.py --partition base_train --limit 400 \
  --upstream-dir /workspace/model_collapse --out data/corpora/pilot_base.json
python scripts/build_base_corpus.py --partition prompts --limit 400 \
  --upstream-dir /workspace/model_collapse --out data/corpora/pilot_prompts.json
python scripts/build_base_corpus.py --partition test --eval \
  --upstream-dir /workspace/model_collapse --out data/corpora/pilot_test.json
```

`--eval` on the test partition is required, not optional: upstream loads `train_file`
and `test_file` together and rejects a column present in one and absent from the other.
That is `FAILURE_LOG.md` F-013.

Check all three exist and are non-trivial:

```bash
ls -la data/corpora/pilot_*.json
```

---

## 5. Dry run

Free. Simulated training, but real allocation, real manifests, real budget arithmetic.
It has caught three confounds so far.

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot.json \
  --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
  --output-dir /workspace/pilot_dryrun --dry-run > /workspace/dryrun.log 2>&1
echo "EXIT=$?"
tail -8 /workspace/dryrun.log
```

> Note the redirect rather than a pipe into `tail`. In bash `$?` after a pipeline is the
> exit status of the *last* command in it, so `... --dry-run | tail -8` followed by
> `echo $?` reports `tail`'s success and would print `EXIT=0` even when the dry run
> exits non-zero on a budget violation. Verified: `(exit 7) | tail -1` leaves `$?` at 0.

**Required output.** `25/25 chains complete`, exit 0, and:

```
budget matching: HOLDS
   spending arms: 749,709 to 749,995 against a 750,000 ceiling (0.0381% spread, 0.2000% permitted)
   control arms held to an exact zero: 1 arm(s), 5 chain(s)
```

Those exact spend figures were measured on 2026-08-18 and are deterministic given the
frozen seeds — **if your numbers differ, something upstream of the policies changed**
(manifests, tokenizer, corpus build). Stop and find out why before spending.

If it prints `BUDGET MATCHING VIOLATED`, it now also exits non-zero. Stop.

This dry run is **not** made redundant by the one already run on a laptop. That one
proved the arithmetic. This one proves the upstream checkout, the shim, and the corpora
you just built are wired correctly — F-007 and F-014 were both environment faults a
laptop cannot see.

A dry run is necessary and **not sufficient**. It prints the upstream command instead
of executing it, so anything depending on the subprocess's working directory,
filesystem or environment still passes. F-017 was exactly that: a passing dry run
followed within seconds by 25 chains dying on a path that could never resolve. The
next step is what closes that gap.

---

## 5a. One real chain, before the grid

Roughly an hour of one GPU. It is the cheapest thing that exercises the real
subprocess path end to end, and it is what would have caught F-017 for about a minute
of compute.

```bash
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
python scripts/run_pilot.py --config configs/experiment/primary_pilot.json \
  --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
  --output-dir /workspace/pilot_smoke \
  --only-arm no_rescue --shard-index 0 --shard-count 5 --cuda-device 0
echo "EXIT=$?"
```

Want: exit 0, `1/5 chains complete`, a `chain_result.json`, and `consumed_human_tokens:
0` — this is the control arm, so zero is correct.

Watch that `--model_path` is populated on the second and later generations and that
`nvidia-smi` actually moves. An empty `--model_path` means checkpoints are not
chaining.

Then certify that one chain before committing to 24 more:

```bash
python scripts/validate_run.py /workspace/pilot_smoke/no_rescue/seed101/
echo "EXIT=$?"
```

Exit 0 or 2. If it exits 1, stop — the grid would produce 25 chains that certify the
same way, which is F-018.

**Measured 2026-08-18:** 3,393 s (56.6 min) for this chain, and
`consumed_total_tokens` 16,678,912. Seven chains land on the busiest shard, so the
grid is roughly **7 × your measured chain time** — about 6.6 h at that rate, and
`no_rescue` is the cheapest arm. Check that against your pod's hourly rate before
launching. The handover's 2.8 h / ~$8 and P-004's ~$9.80 were estimates made before
any chain existed, and the measurement is well above both.

```bash
rm -rf /workspace/pilot_smoke
```

---

## 6. Launch

This is the point money starts being spent.

```bash
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
for i in 0 1 2 3; do
  nohup python scripts/run_pilot.py \
    --config configs/experiment/primary_pilot.json \
    --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
    --output-dir /workspace/pilot \
    --shard-index $i --shard-count 4 --cuda-device $i \
    > /workspace/pilot_shard$i.log 2>&1 &
done
sleep 60 && tail -n 3 /workspace/pilot_shard*.log
```

`nohup ... &` means the shards survive the terminal closing. After the `sleep 60`, each
log should show a chain *starting*, not a traceback.

---

## 7. Monitor

Progress across all four shards:

```bash
grep -h "complete," /workspace/pilot_shard*.log | wc -l    # chains done, of 25
nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv
```

Watch one shard live:

```bash
tail -f /workspace/pilot_shard0.log
```

Check for failures at any time:

```bash
grep -h "FAILED" /workspace/pilot_shard*.log
```

A chain that fails does **not** end the pilot by design — the other 24 continue. Note
which failed; you decide afterwards whether to resume.

**Resuming.** Re-running the exact launch command skips completed chains
(`chain_result.json` present) and resumes interrupted ones from their last checkpoint.
A session that dies at chain 17 costs the 17th chain, not the run.

---

## 8. The whole-grid budget check

**Do not skip this.** Each shard judges only the ~6 chains it ran, so no shard's verdict
covers the comparison. This is the one that gates it.

Once all four shards have exited:

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot.json \
  --output-dir /workspace/pilot --check-only
echo "EXIT=$?"
```

Expect `25 of 25 chains found` and `budget matching: HOLDS`, exit 0.

It is free and reads only the shard summaries, so run it mid-flight too — it reports
`INCOMPLETE` and judges what exists so far.

If it fails, the comparison is confounded and the chains cannot support a C-002
contrast. That is a finding, not a crash: record it in `FAILURE_LOG.md` (append-only)
before doing anything else.

---

## 9. Validate the runs

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/validate_run.py /workspace/pilot/*/seed*/ --report /workspace/pilot/validation.json
echo "EXIT=$?"
```

Exit 0 `valid`, 2 `valid_with_limitation`, 1 `invalid`. The validator never inspects
treatment outcomes, so it cannot be swayed by whether a result is favourable.

> **Steps 9 and 10 only work on a real run.** Against dry-run artifacts both exit 2:
> simulated training consumes no optimizer tokens, so `consumed_total_tokens` is 0 and
> fails `chain_result.schema.json`, which requires a minimum of 1. Verified this
> session. That is correct behaviour, not a defect — a chain that trained on nothing
> should not validate. Do not try to "fix" it by validating the dry run.

---

## 10. Aggregate

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/aggregate_chain_results.py /workspace/pilot/*/seed*/chain_result.json \
  --output /workspace/pilot/aggregate.json --label provisional
```

Keep `--label provisional`. `frozen` is only correct after the results freeze, which has
not happened.

---

## 11. Get the artifacts off the pod

**Do this before you stop the pod.** Persistent volumes can be lost.

```bash
cd /workspace && tar czf pilot_results.tar.gz \
  pilot/*/seed*/chain_result.json \
  pilot/*/seed*/run_manifest.json \
  pilot/pilot_summary*.json pilot/validation.json pilot/aggregate.json \
  pilot_shard*.log
ls -lh /workspace/pilot_results.tar.gz
```

Download it through the Jupyter file browser (navigate to `/workspace`, right-click →
Download).

Deliberately excluded: model checkpoints. They are large and regenerable from the
frozen config and seeds; the manifests and chain results are the evidence.

**Then stop the pod in the RunPod console.** It bills while running, including idle.

---

## 12. What to expect from the result

**Not a verdict.** `PREREGISTRATION.md` freezes five seeds and the practical effect
threshold is 2%, so the joint-versus-baseline interval will very likely straddle the
practically equivalent region. `COMPUTE.md`'s compute gate makes the powered experiment
wait on *pilot variance*, not a pilot result. Expect "inconclusive" —
`paper/outcome_contingent_language.md` has a precommitted template for exactly that.

Budget matching holding makes the contrast *interpretable*. It says nothing about what
the contrast will show.

---

## Failure modes

| Symptom | Cause | Do |
|---|---|---|
| Tests fail on pod, pass on laptop | Bad install | Re-run the `pip` block; check `python -c "import human_data_budget"` |
| Dry-run spend figures differ from §5 | Manifests, tokenizer or corpus build changed | Stop. Diff `data/manifests/` against the frozen hashes in the config |
| `BUDGET MATCHING VIOLATED` | Realised spend outside the P-008 bound | Stop. Do not launch. Record in `FAILURE_LOG.md` |
| `SHIM FAILED` in a log | `sitecustomize.py` corrupted in transit | Rewrite it; check the `\n` survived |
| A chain FAILED, others continue | By design | Note it; re-run the launch command to resume just that chain |
| All four shards die instantly | Wrong `PYTHONPATH`, or corpora missing | Check `ls data/corpora/pilot_*.json` and that the export line ran |
| Pod OOM | Another process on the GPU | `nvidia-smi`; confirm one shard per `--cuda-device` |

---

## Constraints that hold throughout

- **No invented numbers.** Anything not read from a real command's output is
  `TODO(owner): awaiting <source>`.
- **`FAILURE_LOG.md` is append-only.** Correct an entry by appending another.
- **Banned words** in any claim: first, optimal, prevents collapse, solves, state of the
  art, unqualified novel.
- **`primary_no_rescue.json` and `primary_fresh_random.json` stay
  `AWAITING_JULY_31_FREEZE`** and must stay refused. Tests assert this.
- **Do not push to `main`.** Branch and PR.
- Decisions P-001 through P-008 are **proposed, not ratified**. Nothing here ratifies
  them.
