# Toy partition fixtures — NOT SCIENTIFIC DATA

Five toy partitions backing the CPU smoke chain
(`configs/experiment/toy_cpu.json`). They exist so the runner can emit a
`data.partitions` provenance block and the validity auditor can exercise
partition disjointness and per-example provenance without a GPU, a licensed
corpus, or a frozen data decision.

These are **contract fixtures**, not a dataset. The real partitions come from the
domain decision recorded as U-002 in `DECISIONS.md`, which is still open —
`docs/STATUS.md` records `data/manifests/` as containing no real manifest.

## Fields, and what they do and do not mean

| Field | Meaning here |
|---|---|
| `example_id` | Fixture-local stable ID. |
| `text` | Invented fixture prose. Not drawn from any corpus. |
| `origin` | Always `human` in these files. |
| `mode` | Fixture-local `common` / `tail` label, not a measured coverage statistic. |
| `source` | `toy-fixture-corpus/v1` — deliberately not a real dataset identifier, so no row here can be mistaken for licensed corpus content. |
| `source_offset` | Position within this fixture file only. |
| `token_count` | **Placeholder: a whitespace word count, not a tokenizer measurement.** |

### `token_count` is not a token count

`human_data_budget.data.manifest.Example` requires the field, so it is populated,
but no tokenizer has been run on this text and none is pinned
(`PROTOCOL.md` §2 leaves the GPT-2 tokenizer revision an open `TODO`).

`CLAUDE.md` and `PROTOCOL.md` §3 both require optimizer token counts to come from
tokenized batches actually consumed by the optimizer, never from character or
document estimates. The value here is a document estimate and therefore must not
be used for budget accounting, budget matching, or any reported figure.

Nothing currently does: `build_partition_provenance`
(`src/human_data_budget/runner/provenance.py`) emits only `stable_id`,
`content_hash`, `source_dataset`, `origin`, and `text`, so `token_count` never
reaches the run manifest, the auditor, or any ledger. The toy chain's budgets come
from `configs/experiment/toy_cpu.json` instead.

## What is real about these files

The `content_hash` values in the run manifest are genuinely recomputed from the
`text` above by `human_data_budget.data.hashing.content_hash`. They are real
SHA-256 digests of this fixture text — real measurements of fixture content, not
of anything scientific.

## Disjointness

The five partitions are mutually disjoint by content hash, and carry no
cross-partition near-duplicates at the similarity threshold implemented in
`src/human_data_budget/data/overlap.py`. Both properties are asserted by
`tests/runner/test_partition_provenance.py`.
