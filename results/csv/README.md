# Generated CSV Exports

**Everything in this directory is fixture output and may not be cited.**

Produced by `scripts/export_csv.py`. Every input is validated against
`schemas/chain_result.schema.json` before it contributes a row; invalid inputs
are refused rather than skipped.

## Files

| File | Shape |
|---|---|
| `chain_level_long.csv` | One row per (chain, generation) |
| `policy_summary.csv` | One row per policy: chain count and mean regret AUC |

## Why long format

`PROTOCOL.md` §4 is explicit that generations within a chain are repeated
observations, not independent samples. The long file keeps `chain_seed` and
`generation` as columns so that structure survives into whatever tool an analyst
opens next. A wide format that averaged generations away would silently invite
treating 10 generations of one chain as 10 independent data points — the exact
error the protocol names.

Uncertainty is computed across chains by `analysis/metrics.py`, not from these
files.

## Exclusions

An invalid chain still appears in `chain_level_long.csv`, carrying its
`exclusion_reason`. It is omitted from `policy_summary.csv`. Excluded chains are
retained, never deleted (`FAILURE_LOG.md` entry rules).

## Regenerating

```bash
make fixture-artifacts
```
