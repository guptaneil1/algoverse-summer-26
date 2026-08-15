# Generated Tables

**Everything in this directory is fixture output and may not be cited.**

Produced by `scripts/generate_fixture_tables.py` from `analysis.simulator`, which
trains no language model. Each `.tex` file opens with a banner saying so, and
`table_provenance.json` records the SHA-256 of every file plus the chain seeds
used.

## Why these are not in `paper/tables/`

`paper/tables/primary_results.tex` is the manuscript's result table and stays at
`RESULT_PENDING` until real chain artifacts exist (`PROTOCOL.md` §5). Writing a
simulated number there would put it one `\input` away from the abstract. The two
locations are deliberately separate, and
`tests/scripts/test_artifact_generation.py` fails if fixture generation ever
touches the manuscript copy.

## Purpose

To freeze the *format* — columns, ordering, rounding, captions — before results
exist, so that when real chains complete the only change is the input path.

## Regenerating

```bash
make fixture-artifacts
```

Output is deterministic: the same seeds produce byte-identical files, so the
recorded digests are meaningful.
