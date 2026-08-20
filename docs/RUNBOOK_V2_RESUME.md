# Runbook — finishing the interrupted v2 grid, one seed block at a time

Written 2026-08-19, after the v2 grid's second launch lost 17 of 25 chains to F-026.
Use this instead of `RUNBOOK_V2_CORRECTED_GRID.md` Part 6. Parts 1–5 are already done and
must not be repeated: the pod exists, the data is built, and the $3 validation chain
passed. **Part 7 of the corrected-grid runbook is still how you finish.**

## Why this is not just "re-run Step 19"

Two things changed.

**The resume defect.** F-026: the checkpoint is written at the end of a generation, so a
resumed chain restarts on the generation it was interrupted in, whose `model/` directory
the dead attempt had already filled. Upstream refuses a non-empty output directory. The
fix is in `runner/real_chain`; the pod's checkout must be pulled before anything is
launched, or 17 chains fail again in seconds.

**The order is now worth choosing.** The owner authorised the full five-seed grid on
2026-08-19 (`DECISIONS.md` P-012), so the destination is the whole preregistered design.
But `docs/decisions/powered_design_sizing_2026-08-19.md` sizes **three chains per arm**
against the preregistered 2% threshold at 80% power, using the conservative paired SD
measured in the first pilot — which means a three-seed subset is already a complete
experiment at the preregistered sensitivity. Running the seed blocks in order of cost puts
that subset in hand early, so the money running out stops being a way to lose the run.

## What is on disk

8 chains completed and are skipped automatically. 17 are incomplete, holding 140 of their
170 generations still to run — most were killed early, so resume saves 30 generations,
about 18%.

Complete: `joint` 303 404 · `no_rescue` 303 404 · `schedule_only` 505 ·
`selection_only` 101 404 505.

## The order, and why

Seed blocks run cheapest-first. Each phase ends with one more **fully crossed** seed block
— all five arms at that seed — so every stopping point is a design rather than a ragged
set of arms.

| Phase | Seeds | Chains it runs | Shard loads | Wall | Design after it |
|---|---|---|---|---|---|
| 1 | 404 | `random`, `schedule_only` | 9 / 9 | 9 gens | crossed, n=1 |
| 2 | 505 | `no_rescue`, `random`, `joint` | 11 / 9 | 11 gens | crossed, n=2 |
| 3 | 303 | `random`, `schedule_only`, `selection_only` | 9 / 14 | 14 gens | **crossed, n=3 — meets the sizing** |
| 4 | 101,202 | the remaining nine chains | 39 / 40 | 40 gens | **the full preregistered grid, n=5** |

**74 generations against 72 for one undifferentiated launch.** Two generations, about ten
minutes, is what the four stopping points cost.

**Phases 1–3 are one seed each; phase 4 is both remaining seeds together.** Splitting 101
from 202 costs 15 extra generations — `selection_only` 101 is already complete and the
arms left at each seed are lopsided, so neither seed shards evenly on its own while the
pair does.

**Seed order is outcome-independent and must stay that way.** 404, 505 and 303 come first
because their chains were furthest along when the OOM hit, and how far a chain got is
decided by shard scheduling and wall-clock alone. No chain was stopped, kept or dropped on
account of anything it measured, and no seed was chosen after seeing a result. Say so in
the paper if the run ends before phase 4.

## Step R1 — pull the fix (free)

```bash
cd /workspace/algoverse-summer-26 && git fetch origin stage-a/env-freeze && git checkout stage-a/env-freeze && git pull --ff-only origin stage-a/env-freeze && git log --oneline -1 && grep -c stale_model_dir src/human_data_budget/runner/real_chain.py
```

Want a commit that mentions F-026 and a count of `1`. If the count is `0` the fix is not
there and the launch will fail exactly as before.

## Step R2 — run one phase

Change `SEED` only. Nothing else varies between phases. The four values, in order, are
`404`, `505`, `303`, `101,202` — the last one has a comma and no space.

```bash
cd /workspace/algoverse-summer-26
export SEED=404
export TAG=$(echo $SEED | tr ',' '-')
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
for i in 0 1; do
  CUDA_VISIBLE_DEVICES=$i nohup python scripts/run_pilot.py \
    --config configs/experiment/primary_pilot_v2.json \
    --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
    --output-dir /workspace/v2 --preprocessing-workers 8 \
    --only-seeds $SEED \
    --shard-index $i --shard-count 2 --cuda-device 0 \
    > /workspace/v2_seed${TAG}_shard$i.log 2>&1 &
done
sleep 120
nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
tail -n 3 /workspace/v2_seed${TAG}_shard*.log
```

`CUDA_VISIBLE_DEVICES=$i` with `--cuda-device 0` is F-025's isolation. Keep both.

Want two blocks each showing a `src/train.py` command, and chains this phase does not need
reported as `already complete, skipping`.

## Step R3 — watch

```bash
cat > /workspace/status2.sh <<'EOF'
echo "=== $(date +%T) ==="
echo "results on disk : $(ls /workspace/v2/*/seed*/chain_result.json 2>/dev/null | wc -l) / 25"
echo "failed this run : $(grep -h FAILED /workspace/v2_seed*_shard*.log 2>/dev/null | wc -l)"
echo "shards alive    : $(pgrep -fc 'scripts/run_pilot.py')"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
EOF
bash /workspace/status2.sh
```

`results on disk` counts `chain_result.json` files, which is the only count that cannot
lie. The old `status.sh` grepped for the word `complete,`, which also matches
`already complete, skipping`, and globbed logs from an abandoned launch — that is how the
last run was reported as 10 chains when it had 8 (F-026).

**Any `FAILED` line: stop and send it.** Do not start the next phase.

## Step R4 — after each phase

Pass the seeds completed **so far**, not just this phase's — the check should cover the
whole crossed design that now exists.

| After phase | Use |
|---|---|
| 1 | `--only-seeds 404` |
| 2 | `--only-seeds 404,505` |
| 3 | `--only-seeds 303,404,505` |
| 4 | omit the flag — the grid is whole |

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --output-dir /workspace/v2 --only-seeds 404 --check-only
echo "EXIT=$?"
```

**`run_pilot --check-only` exits `0` if both budget axes hold and `1` if either does not.**
Two codes, not four. It is not `validate_run.py`, whose codes are `0 valid / 1 limited /
2 invalid / 3 usage` (F-024) and which runs later, at Part 7 Step 22. Confusing the two is
how F-024 happened; they are different tools with different contracts.

Want `budget matching: HOLDS` on both the human and total lines, and a chain count equal to
five times the number of seeds checked. An `INCOMPLETE` note means a chain is missing —
send it rather than continuing.

Then either start the next phase, or stop and go to Part 7 of
`RUNBOOK_V2_CORRECTED_GRID.md`. **Both are legitimate endings.** One complete seed block is
a crossed design at n=1 and supports no interval; two support a weak one; three meet the
preregistered sizing; four gets the full preregistered grid.

Free disk between phases if it ever matters — it did not last time, 537 T were free:

```bash
for d in /workspace/v2/*/seed*/; do
  if [ -f "$d/chain_result.json" ]; then rm -rf "$d"upstream/*/model; fi
done
```

## Step R5 — finish

`RUNBOOK_V2_CORRECTED_GRID.md` Part 7, Steps 21–25, with one change: Step 21's
`--check-only` and Step 22's `validate_run.py` should cover the seeds actually completed.
If all five ran, nothing changes at all.

**The pod bills while idle.** Set an alarm for each phase's expected end. The last run sat
idle for an hour after finishing, and the one before that was noticed 59 minutes late.
