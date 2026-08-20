# primary_pilot_2026-08-18 — artifacts

The executed primary pilot. 25 chains, 4× RTX 4090, 2026-08-18 21:40 → 2026-08-19
05:24 UTC. Analysis and interpretation: `docs/runs/primary_pilot_2026-08-18_results.md`.

## What is here, and what is not

**Tracked in git** (~230 KB): the 25 `chain_result.json` files, the four shard
summaries, `aggregate.json`, `validation.json`, and `ARTIFACT_HASHES.json`. Every number
in the results document is computed from these and nothing else, so the analysis is
reproducible from a clone.

`validation.json` was added to tracking on 2026-08-20 and is **not in the hash ledger
below**, because it was produced during the F-021 analysis rather than by the run. It is
tracked because it is the direct evidence for this run's certification split --- 10
`invalid`, 15 `valid_with_limitation` --- and F-021 happened precisely because that
per-chain report existed and an aggregate exit code was read instead of it.

**Not tracked** (~162 MB): the 25 `run_manifest.json` files. Each carries 28,351
partition provenance records at roughly 6.5 MB. They are the provenance evidence, not
analysis input, and `results/README.md`'s policy is that git holds "only small
validated aggregates, generated tables/figures, and documentation".

**Also not here:** model checkpoints. They were pruned on the pod as each chain
completed and are regenerable from the frozen config and seed.

## Verifying an archived copy

`ARTIFACT_HASHES.json` records the SHA-256 and byte length of all 61 files, including
the untracked manifests. To check an archive against this repository:

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("results/runs/primary_pilot_2026-08-18")
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

Expect `61/61 verified` against a complete archive, or `36/61` against a fresh clone
with the manifests absent — a clone reports the manifests as missing, never as
mismatched.

## Provenance caution

`code_commit` in the ledger is `499ebbc`, the commit the chains actually ran under.
The F-020 fix in `policies/terminal.py` **post-dates this run and was not in it**.
These artifacts therefore carry the `joint` underspend that makes the primary contrast
invalid; that is a property of the data, not something a later checkout corrects.
