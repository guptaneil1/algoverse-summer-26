# Dataset Datasheet

**Owner:** Neil (data, evaluation, and validity lead)
**Status:** FROZEN 2026-08-08 — final licensed domain, dataset revision, partition manifests,
hashes, and mode definition are all frozen. See `DECISIONS.md` (closes U-002) and
`docs/data/mode_definition_audit.md` (closes the mode half of U-004).

---

## Primary Domain: WikiText-103

**Source:** Merity et al., *Pointer Sentinel Mixture Models* (2016).
Available at `wikitext` on the Hugging Face Hub (`wikitext-103-v1`).

**License:** Creative Commons Attribution-ShareAlike 3.0 Unported (CC-BY-SA-3.0).
This license permits use for ML training and academic publication, provided attribution is given and derivative works share under the same license.

**Version:** `wikitext-103-v1` (canonical tokenized train/valid/test splits).

**Frozen dataset revision:** Hugging Face repo `Salesforce/wikitext`, commit
`b08601e04326c79dfdd32d625aee71d232d685c3`, resolved from `main` on 2026-08-08 and pinned by
`scripts/build_wikitext103_manifests.py` so every rebuild reads the same bytes regardless of
later upstream changes.

**Size:** 100,346,007 whitespace-split training tokens across the three train-derived partitions
(base_train + rescue_candidates + prompts, post-dedup, §"Data Partitions" below), 213,886
validation tokens, 241,211 test tokens. These are whitespace-split estimates, consistent with
the Week 1 figure; optimizer-consumed counts depend on the frozen tokenizer, which is not yet
pinned (owned by the training config, not this freeze).

---

## Why WikiText-103

| Criterion | Assessment |
|---|---|
| License | CC-BY-SA — permits ML training and publication |
| Size | ~103M tokens fits a 124M–160M screening model on available compute |
| Mode diversity | Articles span broad categories (politics, science, arts, sports) enabling principled tail/common split |
| Reproducibility | Canonical release on Hugging Face; SHA-256 of the dataset card is stable |
| Benchmark standing | Widely used; positive-control reproduction against published NLL is straightforward |
| Personal data | None — Wikipedia content is encyclopedic, not personal |

**Fallback:** OpenWebText2 (Reddit-upvoted link corpus, permissive license). Not activated —
WikiText-103 access and licensing were unblocked at Week 2 (real download succeeded from the
pinned revision above), so the fallback remains documented but unused.

---

## Mode Definition (FROZEN 2026-08-08)

**Frozen: `article_length_quantile`.** Full reliability/independence audit in
`docs/data/mode_definition_audit.md`. Summary: the alternative (`wikipedia_article_category`)
requires joining in Wikipedia category metadata that is not part of the frozen dataset release
and is sourced from a live, continuously-edited system — it fails both the reliability check
(not computable from the frozen revision alone) and the independence check (not stable after the
freeze date). `article_length_quantile` needs no metadata beyond the article's own text.

- **tail**: token_count ≤ 1106 (10th percentile of the train-split token-count distribution,
  computed post-dedup).
- **common**: token_count > 2661 (50th percentile / median of the same distribution).
- **mid**: everything between the two cutoffs; retained in every manifest, excluded from the
  frozen primary tail/common contrast.
- Thresholds are fit once on the train split and applied unchanged to `validation` and `test`.

---

## Data Partitions

All five partitions are constructed from the WikiText-103 canonical release using a deterministic stable-ID hash split. Disjointness is enforced by the `assert_disjoint` function in `data/separation.py` and verified by the overlap tests in `tests/data/` (fixture scale) and `docs/data/overlap_report.md` (real corpus, frozen manifests).

| Partition | Source split | Examples | Tokens | Manifest SHA-256 (file) |
|---|---|---:|---:|---|
| `base_train` | wiki-103 train (~80%) | 22,637 | 80,669,290 | `3d30c87abb185d7be316f0f96f86dab2d6119fc3fecb226905f878279b88379f` |
| `rescue_candidates` | wiki-103 train (~15%) | 4,235 | 14,864,936 | `964fe8f7af8226b0c83a44de090ea646f8b4608563553f43aaf4d34ac57e38b6` |
| `prompts` | wiki-103 train (~5%) | 1,359 | 4,811,781 | `3440684559c2e98bce00d75713be1778053062ee4698b935e3ff1b7de7af75b5` |
| `validation` | wiki-103 valid | 60 | 213,886 | `174117c506c4bc3fef778f31d8e853bf6ae7a658ff946f0fafd0eb859227a224` |
| `test` | wiki-103 test | 60 | 241,211 | `1d48dd2679fcb249f9874d600969d52a3f3670e25f2e399a72f342f029112287` |

Per-partition manifest content hashes (over the example set, independent of file formatting) and
mode-count breakdowns are in `data/manifests/MANIFEST_HASHES.json`. `prompts` is generation
conditioning only, and is excluded from training and evaluation by convention — nothing in the
manifest schema currently enforces that mechanically; see the "Known Limitations" note below.

`purpose` for each partition: `base_train` initial model training; `rescue_candidates` pool for
human-data rescue allocation; `prompts` generation conditioning, never training or evaluation;
`validation` early stopping and configuration decisions; `test` **final held-out evaluation
only**.

The frozen tokenizer identifier (needed to convert whitespace-split counts to
optimizer-consumed tokens) is owned by the training config and is not yet pinned; see
"Token-Counting Rule" below for what is frozen without it.

Raw manifest files (`data/manifests/*.jsonl`) are not committed to git — `data/README.md`:
"Raw datasets are not committed." They are hash-only (no article text, per the same policy) and
reproducible byte-for-byte via `scripts/build_wikitext103_manifests.py` against the pinned
revision above; the hashes in this table are what's committed as the durable fingerprint.

---

## Token-Counting Rule

Optimizer-consumed tokens are counted using the frozen tokenizer with the following rule:

- Padding tokens (ID = 0 under the frozen tokenizer) are excluded.
- If an example is presented in N epochs, it contributes N × non-padding-token-count to the lifetime budget.

This rule is implemented in `data/token_accounting.py` (`consumed_tokens`) and tested in `tests/data/test_token_accounting.py`, including padding, multi-epoch repetition, batching, gradient-accumulation regrouping, and additive resume-boundary splits (Week 2 additions).

---

## Known Limitations and Biases

- WikiText-103 covers only English Wikipedia articles that reached Good or Featured status. It overrepresents topics with active Wikipedia editor communities (technology, sports, entertainment) and underrepresents others.
- **The canonical WikiText-103-v1 release contains real train/test leakage.** One article
  ("The Hustler (film)") appears verbatim in both the train and test splits, and 240 further
  articles are exact duplicates of other train articles. This project's build removes all 241
  before partitioning (`docs/data/overlap_report.md` §2); anyone using the raw HF release
  directly, without this dedup step, inherits the leak.
- The `article_length_quantile` mode definition (frozen; see above) is a structural proxy for
  topic rarity, not a semantic one — a short article and a long article can be about equally
  rare topics. This tradeoff was accepted for reliability/independence
  (`docs/data/mode_definition_audit.md`), not because length is believed to be the better
  semantic signal.
- Token counts in this datasheet are whitespace-split estimates. Optimizer-consumed counts under
  the eventual frozen tokenizer will differ and must be recomputed once that tokenizer is pinned.

---

## Access and Reconstruction

```bash
pip install huggingface_hub pyarrow  # build-time only, not a package runtime dependency
python scripts/build_wikitext103_manifests.py
```

The script downloads `Salesforce/wikitext` config `wikitext-103-v1` pinned at revision
`b08601e04326c79dfdd32d625aee71d232d685c3`, applies the frozen parsing, dedup, mode, and
partition rules above, and writes `data/manifests/*.jsonl` plus
`data/manifests/MANIFEST_HASHES.json`. Anyone with a Hugging Face account can reconstruct the
dataset; the pinned revision and deterministic stable IDs guarantee byte-identical manifests and
hashes. Per-partition manifest-file SHA-256 hashes are recorded in the Data Partitions table
above; per-example provenance (source, offset, content hash) is inside each manifest file
itself.
