# Runbook — the corrected grid (v2)

Everything is prepared. This is the whole remaining experimental task: a validation chain,
a check, then the grid. **Roughly $23 and eight hours, most of it unattended.**

**What changed since the 2026-08-18 run.** Two defects made that run's comparison invalid,
and both are closed:

- **F-020** — `joint` under-spent its human budget by 10.1%. Fixed in `policies/terminal.py`.
  No config change needed.
- **F-021** — realised total optimizer tokens differed 2.26% across arms, because human
  data was *added* to the corpus rather than displacing part of it, so training volume
  tracked how much a policy spent. Fixed by `corpus_record_budget` in
  `configs/experiment/primary_pilot_v2.json` (decision P-011).

**The one thing a dry run cannot check.** Displacement only equalises volume when there is
a decoded corpus to displace into, and a dry run performs no decode. So the dry run below
is still worth running — it catches config and path faults for free — but **it cannot
validate P-011**. Step 3 is what does that, and it is why the grid is not the first paid
step. This limitation is recorded in `FAILURE_LOG.md` and pinned by
`tests/data/test_corpus_displacement.py`.

---

## 1. Pod and setup

Identical to `docs/RUNBOOK_PILOT_LAUNCH.md` sections 1 through 4: provision 4x RTX 4090,
clone both repos, write the shim, build the three corpora. Nothing there has changed.

Confirm you have the fixes before spending:

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python -m pytest -q 2>&1 | tail -2
python -c "import json; print(json.load(open('configs/experiment/primary_pilot_v2.json'))['corpus_record_budget'])"
```

Expect the suite green, and `400`.

## 2. Dry run — free

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
  --output-dir /workspace/v2_dryrun --dry-run > /workspace/v2_dryrun.log 2>&1
echo "EXIT=$?"; tail -8 /workspace/v2_dryrun.log
```

Expect `25/25 chains complete`, exit 0, `budget matching: HOLDS` on the human axis, and a
line saying total optimizer tokens are **not reported**. That last line is correct here and
is not a warning: a dry run consumes no optimizer tokens.

## 3. One real chain — about an hour, ~$3. This is the step that matters.

```bash
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
  --output-dir /workspace/v2_smoke \
  --only-arm selection_only --shard-index 0 --shard-count 5 --cuda-device 0
echo "EXIT=$?"
```

`selection_only` deliberately, not `no_rescue`: it is the arm whose totals ran 1.7% high
under the old assembly, so it is the one that demonstrates displacement working.

**Then check the corpora are the size the budget specifies:**

```bash
python - <<'PY'
import json, glob
sizes = [len(json.load(open(f))) for f in sorted(glob.glob(
    "/workspace/v2_smoke/selection_only/seed101/upstream/*/data.json"))]
print("assembled corpus sizes:", sizes)
print("all 400:", all(s == 400 for s in sizes[1:]))
PY
```

**Every generation after the first must read 400.** If they do, displacement works and the
grid is safe to launch. If they do not, stop and report the sizes — the budget does not
match what the decode produces, and the grid would reproduce F-021.

Also certify the chain:

```bash
python scripts/validate_run.py /workspace/v2_smoke/selection_only/seed101/
echo "EXIT=$?"
```

Want exit 0 or 2, and **no** `BUDGET_TOTAL_MISMATCH`.

## 4. The grid — about seven hours, ~$20

Only after step 3 passes.

```bash
rm -rf /workspace/v2_smoke /workspace/v2_dryrun
cd /workspace/algoverse-summer-26
export WANDB_MODE=disabled WANDB_SILENT=true STAGE_A_WANDB_SHIM=1 PYTHONPATH=/workspace/shim:src
for i in 0 1 2 3; do
  nohup python scripts/run_pilot.py \
    --config configs/experiment/primary_pilot_v2.json \
    --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim \
    --output-dir /workspace/v2 \
    --shard-index $i --shard-count 4 --cuda-device $i \
    > /workspace/v2_shard$i.log 2>&1 &
done
sleep 90 && tail -n 2 /workspace/v2_shard*.log
```

Monitor with the same `status.sh` as before, pointed at `/workspace/v2`. Prune completed
chains' checkpoints periodically.

## 5. When it finishes — the gate

```bash
cd /workspace/algoverse-summer-26 && export PYTHONPATH=src
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --output-dir /workspace/v2 --check-only
echo "EXIT=$?"
```

**This is the decision point.** Exit 0 with `budget matching: HOLDS` on *both* axes means
the primary contrast is valid and the paper gains an empirical result. Exit 1 means it does
not, and the run is reported the way the last one was.

Then:

```bash
python scripts/validate_run.py /workspace/v2/*/seed*/ --report /workspace/v2/validation.json
python scripts/aggregate_chain_results.py /workspace/v2/*/seed*/chain_result.json \
  --output /workspace/v2/aggregate.json --label provisional
cd /workspace && tar czf v2_results.tar.gz \
  v2/*/seed*/chain_result.json v2/*/seed*/run_manifest.json \
  v2/pilot_summary*.json v2/validation.json v2/aggregate.json v2_shard*.log
ls -lh /workspace/v2_results.tar.gz
```

Download `v2_results.tar.gz` through Jupyter, **then stop the pod.**

## 6. Hand it back

Send me the tarball path and the `--check-only` output. Everything downstream is already
built and will be run for you:

- extract into `results/runs/primary_pilot_v2_2026-08-19/` with a hash ledger
- regenerate the table, figure and macro file from the new artifacts
- recompute the primary contrast and its interval
- update §7, the abstract and the conclusion to whatever the run supports
- update `CLAIMS.md` C-002, `STATUS.md`, and the failure log
- reproduce every published value independently and re-run the coherence checks

No number will be typed by hand, and the outcome-contingent templates in
`paper/outcome_contingent_language.md` cover every case including a null or a harmful
result.

## What could still go wrong

| Symptom | Meaning |
|---|---|
| Step 3 corpora not 400 | The record budget does not match the decode size. Stop; the grid would reproduce F-021 |
| `BUDGET_TOTAL_MISMATCH` on the smoke chain | Displacement is not taking effect. Check `corpus_record_budget` reached the chain config |
| `--check-only` exit 1 on the human axis | F-020's fix did not apply; confirm the checkout has it |
| `--check-only` exit 1 on the total axis | Displacement worked per-chain but totals still diverge, meaning the divergence has a second cause. That is a finding, not a failure — report it |
