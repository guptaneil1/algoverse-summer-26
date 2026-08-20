# primary_pilot_v2_2026-08-20 — artifacts

The corrected grid. 25 chains, 2× RTX 4090, completed 2026-08-20 08:50 UTC. Analysis and
interpretation: `docs/runs/primary_pilot_v2_2026-08-20_results.md`.

This is the run in which both budget axes of `PROTOCOL.md` §4 hold — human spread
0.0381%, total spread 0.0000%, against 0.2000% permitted — so the preregistered contrast
is admissible. The previous grid failed both (F-020, F-021).

## What is here, and what is not

**Tracked in git** (~250 KB): the 25 `chain_result.json` files, the 25
`reference_mode_scores.json` snapshots, the eleven shard summaries, `aggregate.json`,
`validation.json`, and `ARTIFACT_HASHES.json`. Every number in the results document is
computed from these and nothing else, so the analysis is reproducible from a clone.

`validation.json` and the reference snapshots are tracked here and were not for the
previous run. The first because F-021 happened by reading an aggregate exit code instead
of the per-chain report that was sitting in this file; the second because the
confirmatory tail-retention metric cannot be recomputed without the generation-0
reference it is measured against.

**Not tracked** (~162 MB): the 25 `run_manifest.json` files, at roughly 6.5 MB each.
They are provenance evidence, not analysis input, and stay verifiable through
`ARTIFACT_HASHES.json`.

**Also not here:** model checkpoints, pruned on the pod and regenerable from the frozen
config and seed.

## Eleven shard summaries for a 25-chain grid

The grid was assembled from four seed-block phases plus two abandoned launches, so the
directory holds more summaries than a single-launch run would:

| Summaries | Launch | Outcome |
|---|---|---|
| `pilot_summary_seeds404_shard{0,1}of2` | phase 1 | 2 chains, clean |
| `pilot_summary_seeds505_shard{0,1}of2` | phase 2 | 3 chains, clean |
| `pilot_summary_seeds303_shard{0,1}of2` | phase 3 | 3 chains, clean |
| `pilot_summary_seeds101-202_shard{0,1}of2` | phase 4 | 9 chains, clean |
| `pilot_summary_shard{0,1}of2` | the launch F-026 killed | 4 chains, 17 failed |
| `pilot_summary_shard1of4` | the launch F-025 killed | 0 chains |

`load_grid_chains` deduplicates by `(arm, seed)`, so a chain appearing in more than one
summary is counted once. **Wall time is the sum of per-launch maxima, not the maximum
over all summaries** — shards within a launch are concurrent, launches are sequential.
A single maximum returns 3.35 h, which is phase 4 and not the run. See
`wall_hours` in `scripts/generate_pilot_outputs.py` and F-020a for why this is written
down rather than assumed.

## Verifying an archived copy

`ARTIFACT_HASHES.json` records the SHA-256 and byte length of all 101 files, including
the untracked manifests.

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("results/runs/primary_pilot_v2_2026-08-20")
ledger = json.loads((root / "ARTIFACT_HASHES.json").read_text())["files"]
missing, bad = [], []
for rel, want in sorted(ledger.items()):
    p = root / rel
    if not p.is_file():
        missing.append(rel); continue
    if hashlib.sha256(p.read_bytes()).hexdigest() != want["sha256"]:
        bad.append(rel)
print(f"{len(ledger)-len(missing)-len(bad)}/{len(ledger)} verified")
if missing: print("MISSING:", *missing[:5], sep="\n  ")
if bad: print("MISMATCH:", *bad[:5], sep="\n  ")
PY
```

Expect `101/101` against a complete archive, or `64/101` against a fresh clone with the
manifests and logs absent — a clone reports them missing, never mismatched.

## Provenance caution

`code_commit` in the ledger is `088b7ff`. The F-026 fix and `--only-seeds` were both in
the tree for every phase. `scripts/generate_pilot_outputs.py` changed *after* the run to
gate the primary contrast on measured budget axes rather than a hardcoded refusal naming
F-020; that change reads these artifacts and does not alter them.

Eight of the 25 chains were produced by the launch F-026 killed. F-026 stopped chains
from starting and never corrupted one that finished, so those eight are ordinary
completed chains and the resume path reuses them as it would any other.
