# Certificates and batch verdicts

## What is here

| File | What it is |
|---|---|
| `batch_verdicts.json` | `validate_run.py` over **every chain of both grids**, 50 in total. The complete certification record |
| `primary_pilot_v2_2026-08-20_EVIDENCE_PACK.md` | Pre-gathered evidence for a certifier. **Not a certificate** — deliberately unsigned |
| `reproduction_log.md` | Each time a human has run `reproduce_pilot_table.py`, what they saw, and how independent they actually were. Append entries; do not overwrite |

No validity certificate has been issued. `docs/VALIDITY_CERTIFICATE_TEMPLATE.md` requires a
certifier who did not operate the run, and none has been available.

## Regenerating the batch verdicts

```bash
export PYTHONPATH=src
python scripts/validate_run.py \
  results/runs/primary_pilot_v2_2026-08-20/pilot/*/seed*/ \
  results/runs/primary_pilot_2026-08-18/pilot/*/seed*/ \
  --audited-at 2026-08-20T00:00:00Z \
  --report results/certificates/batch_verdicts.json
```

`--audited-at` is passed explicitly so identical inputs produce an identical file. Without it
the report carries a wall-clock timestamp and the committed copy churns on every run.

## The exit code is 2, and that does not block the freeze

`validate_run.py` exits with the **worst state across all runs**, and the template says a
non-zero exit at freeze time means at least one run needs attention before the freeze can be
tagged. Read literally, the freeze is blocked. It is not, and the reasoning belongs here
rather than in a commit message.

| Grid | Chains | Verdict |
|---|---|---|
| `primary_pilot_v2_2026-08-20` | 25 | 25 `valid_with_limitation`, **0 invalid** |
| `primary_pilot_2026-08-18` | 25 | 15 `valid_with_limitation`, **10 invalid** |

The ten invalid chains are all from the **superseded** grid. They are invalid for a reason
that is recorded, understood and closed — `joint` underspent its human budget (F-020) and
realised totals diverged across arms (F-021) — and they are **retained deliberately**.
`DECISIONS.md` D-011 and `PROTOCOL.md` both require failed and invalid runs to be preserved
and certified as such rather than deleted, and `FAILURE_LOG.md` F-020 and F-021 cite their
numbers, so removing them would break the audit trail that explains why a second grid exists.

They enter no analysis. `aggregate.json` for the analysed run records 25 included and 0
excluded, and `scripts/generate_pilot_outputs.py` reads only the run directory it is given.

**So the exit code is doing its job and the answer to it is a judgement, not a fix.** A
freeze assessed over the grid under analysis is exit 1, `valid_with_limitation`, which is the
passing state. A freeze assessed over the repository's whole history includes a grid that was
rejected on purpose. The second number is the one this file reports, because suppressing it —
by running the batch over only the good grid — would produce a clean exit that means less.

Anyone re-running the command above should expect exit 2 and should not treat it as a
regression.

## What a certifier still owes

See §8 of the evidence pack. In short: verify independence, decide whether the two known
unverified properties (near-duplicate separation, token-ledger recomputation) are acceptable
for a `valid_with_limitation` classification or whether they block, recompute a metric from
raw outputs rather than from `chain_result.json`, classify the headline result, and sign or
decline.
