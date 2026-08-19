# Runbook — the corrected grid (v2)

Complete steps, assuming nothing. **Total ~$23, roughly 7 hours, most of it unattended.**

Written for **2× RTX 4090**, which is what RunPod had available. Cost is GPU-hours, so
fewer GPUs costs the same and takes longer; the two-shards-per-GPU launch in Part 6 buys
most of the time back.

**Rule for the whole document: paste one block, wait for the `#` prompt to return, then
paste the next.** The 2026-08-18 session lost an hour to keystrokes queued behind a
running command.

**Three places to stop.** At any of them, paste me the output instead of continuing:

| Step | Stop if |
|---|---|
| 12 | Not `793 passed`, not `budget: 400`, or fewer than 2 GPUs |
| 17 | `ALL 400: False` ← **this one saves you $20** |
| 18 | You see `BUDGET_TOTAL_MISMATCH` |

---

# PART 1 — Create the pod

1. Go to **https://runpod.io** and sign in.
2. Check your balance is at least **$25** (top right).
3. **Deploy** (left sidebar) → **GPU Cloud**.
4. Find **RTX 4090**. Set count to **2**.
5. Template: any whose name contains **PyTorch**.
6. **Edit Template** → Container Disk **30 GB**, Volume Disk **80 GB**, Volume Mount Path
   **/workspace**.
7. Ensure **Start Jupyter Notebook** is checked.
8. **Deploy On-Demand**. Wait for **Running** (1–3 min).
9. **Connect** → **Start Web Terminal**. Everything below goes in that window.

---

# PART 2 — Setup (~5 min)

**Step 10.** Paste. Wait for `=== SETUP DONE ===`. Don't touch the keyboard meanwhile.

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

**Step 11.** Paste. Wait for `=== SHIM WRITTEN ===`.

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

**Step 12.** Verify. **This is stop-point one.**

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python -m pytest -q 2>&1 | tail -2
python -c "import json; print('budget:', json.load(open('configs/experiment/primary_pilot_v2.json'))['corpus_record_budget'])"
nvidia-smi -L
nproc
```

Must show: `793 passed` (or more), `budget: 400`, two lines starting `GPU 0` and `GPU 1`,
and a CPU count. **Note the CPU count** — you need it in Step 16.

---

# PART 3 — Build the data (~8 min)

**Step 13.**

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/build_base_corpus.py --partition base_train --limit 400 \
  --upstream-dir /workspace/model_collapse --out data/corpora/pilot_base.json
python scripts/build_base_corpus.py --partition prompts --limit 400 \
  --upstream-dir /workspace/model_collapse --out data/corpora/pilot_prompts.json
python scripts/build_base_corpus.py --partition test --eval \
  --upstream-dir /workspace/model_collapse --out data/corpora/pilot_test.json
ls -la data/corpora/pilot_*.json
```

Must show three files, each several MB.

---

# PART 4 — Free dry run (~2 min)

**Step 14.**

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
  --output-dir /workspace/v2_dryrun --dry-run > /workspace/v2_dryrun.log 2>&1
echo "EXIT=$?"
tail -8 /workspace/v2_dryrun.log
```

Must show `EXIT=0`, `25/25 chains complete`, `budget matching: HOLDS`.

A line saying total optimizer tokens are **not reported** is correct here — a dry run
consumes none.

---

# PART 5 — The $3 validation chain (~30–60 min)

Money starts here. This is the step that decides whether the grid is safe.

**Step 15.** Note the time before you start.

**Step 16.** Set `--preprocessing-workers` to **half your `nproc` from Step 12, capped at 8**.
If `nproc` said 16 or more, use 8.

```bash
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
  --output-dir /workspace/v2_smoke --preprocessing-workers 8 \
  --only-arm selection_only --shard-index 0 --shard-count 5 --cuda-device 0
echo "EXIT=$?"
```

Prints a lot. Leave it. Ends with `1/5 chains complete` and `EXIT=0`.

**Note how long it took.** It was 57.9 min with 1 worker; whatever it is now is the real
speed-up, measured rather than guessed.

**Step 17. THE CRITICAL CHECK — stop-point two.**

```bash
python - <<'PY'
import json, glob
sizes = [len(json.load(open(f))) for f in sorted(glob.glob(
    "/workspace/v2_smoke/selection_only/seed101/upstream/*/data.json"))]
print("sizes:", sizes)
print("ALL 400:", all(s == 400 for s in sizes[1:]))
PY
```

- **`ALL 400: True`** → continue.
- **`ALL 400: False`** → **STOP.** Send me the `sizes:` line. The grid would waste $20.

**Step 18. Stop-point three.**

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/validate_run.py /workspace/v2_smoke/selection_only/seed101/
echo "EXIT=$?"
```

Want `EXIT=0` or `EXIT=2`, and **no `BUDGET_TOTAL_MISMATCH`** anywhere in the output.

---

# PART 6 — The $20 grid (~5–7 h)

Only if Step 17 said `True` and Step 18 was clean.

**Step 19.** Four shards, two per GPU.

```bash
rm -rf /workspace/v2_smoke /workspace/v2_dryrun
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
for i in 0 1 2 3; do
  dev=$(( i / 2 ))
  nohup python scripts/run_pilot.py \
    --config configs/experiment/primary_pilot_v2.json \
    --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
    --output-dir /workspace/v2 --preprocessing-workers 4 \
    --shard-index $i --shard-count 4 --cuda-device $dev \
    > /workspace/v2_shard$i.log 2>&1 &
done
sleep 120
nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
tail -n 2 /workspace/v2_shard*.log
```

Want four blocks each showing a `src/train.py` command — not a traceback.

**Watch the memory line.** Two chains share each 24 GB card. If `memory.used` exceeds
**~21000 MiB** on either GPU, kill it and fall back to the safe launch below.

<details>
<summary>Safe fallback: one shard per GPU (slower, no OOM risk)</summary>

```bash
pkill -f "scripts/run_pilot.py"; sleep 5
rm -rf /workspace/v2
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
for i in 0 1; do
  nohup python scripts/run_pilot.py \
    --config configs/experiment/primary_pilot_v2.json \
    --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
    --output-dir /workspace/v2 --preprocessing-workers 8 \
    --shard-index $i --shard-count 2 --cuda-device $i \
    > /workspace/v2_shard$i.log 2>&1 &
done
sleep 120 && tail -n 2 /workspace/v2_shard*.log
```

Change `/ 4 alive` to `/ 2 alive` in Step 20.
</details>

**Step 20.** Status checker:

```bash
cat > /workspace/status.sh <<'EOF'
echo "=== $(date +%T) ==="
echo "complete : $(grep -h 'complete,' /workspace/v2_shard*.log 2>/dev/null | wc -l) / 25"
echo "failed   : $(grep -h 'FAILED' /workspace/v2_shard*.log 2>/dev/null | wc -l)"
echo "shards   : $(pgrep -fc 'scripts/run_pilot.py') / 4 alive"
echo "on disk  : $(du -sh /workspace/v2 2>/dev/null | cut -f1)"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
EOF
echo saved
```

Check any time:

```bash
bash /workspace/status.sh
```

Healthy: `complete` climbing, `failed` at 0, shards alive, memory under ~21000 MiB.

**Free up disk every few hours** (checkpoints are large and regenerable):

```bash
for d in /workspace/v2/*/seed*/; do
  if [ -f "$d/chain_result.json" ]; then rm -rf "$d"upstream/*/model; fi
done
du -sh /workspace/v2
```

**You can close the browser now.** It keeps running. **Set an alarm** — the pod bills while
idle, and the last run sat idle for an hour after finishing.

---

# PART 7 — Finish (~5 min)

When `status.sh` shows `complete : 25 / 25`:

**Step 21. THE RESULT.**

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --output-dir /workspace/v2 --check-only
echo "EXIT=$?"
```

**Copy everything it prints and send it to me.** `EXIT=0` with `HOLDS` on both axes means
the primary contrast is valid and the paper gains an empirical result.

**Step 22.** Package:

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/validate_run.py /workspace/v2/*/seed*/ --report /workspace/v2/validation.json
python scripts/aggregate_chain_results.py /workspace/v2/*/seed*/chain_result.json \
  --output /workspace/v2/aggregate.json --label provisional
cd /workspace && tar czf v2_results.tar.gz \
  v2/*/seed*/chain_result.json v2/*/seed*/run_manifest.json \
  v2/pilot_summary*.json v2/validation.json v2/aggregate.json v2_shard*.log
ls -lh /workspace/v2_results.tar.gz
```

**Step 23.** Download: RunPod console → your pod → **Connect** → **Jupyter Lab** → click
into `workspace` → right-click `v2_results.tar.gz` → **Download**.

**Step 24. STOP THE POD.** Console → **Stop**, then **Terminate**. Then check **Storage**
in the sidebar and delete any leftover volume.

**Step 25.** Send me the Step 21 output and confirm the tarball downloaded.

---

## What I do from there

- Extract into `results/runs/primary_pilot_v2_2026-08-19/` with a hash ledger
- Regenerate table, figure and macros from the new artifacts
- Recompute the primary contrast and its interval
- Update §7, abstract, conclusion to whatever the run supports
- Update `CLAIMS.md` C-002, `STATUS.md`, `FAILURE_LOG.md`
- Reproduce every published value independently, re-run the coherence checks

No number typed by hand. `paper/outcome_contingent_language.md` covers every outcome
including a null or a harmful one.

## If something goes wrong mid-run

| Symptom | What to do |
|---|---|
| A shard disappears from `status.sh` | Re-run the Step 19 block. Completed chains are skipped; you lose one chain, not the run |
| `failed` count above 0 | `grep -h FAILED /workspace/v2_shard*.log` and send it to me |
| Memory near 24000 MiB | Kill and use the safe fallback launch |
| Disk filling | Run the prune command in Step 20 |
