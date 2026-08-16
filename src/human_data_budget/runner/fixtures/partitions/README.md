# Toy partition fixtures

Five disjoint partitions in the vocabulary `validation/audit.py` requires, used by
`configs/experiment/toy_cpu.json` so the toy smoke chain produces a certifiable run
manifest.

**These are fixtures, not data.** `source_dataset` is `runner-fixture/toy-v1`. No real
corpus is implied and no scientific value may be read from them.

They live here rather than in `data/fixtures/` because `data/` is @Neil's and this is
runner-owned test material. They are written in the `data/manifest.py` record shape
(`example_id`, `origin`, `mode`, `source`, `source_offset`, `token_count`) so they load
through Neil's `load_manifest_from_jsonl` and exercise the real translation path in
`runner/manifest.py` — the same path a real chain uses — rather than an inline shortcut.

`data/fixtures/toy_corpus.jsonl` cannot serve this purpose: it holds 4 examples, all
`origin: human`, and omits `source`, `source_offset`, and `token_count`, so
`Example.from_dict` raises `ProvenanceError` on it.
