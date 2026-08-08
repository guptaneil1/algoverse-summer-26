# WikiText-103 Overlap Report

**Owner:** Neil (data, evaluation, and validity lead)
**Status:** FROZEN 2026-08-08
**Produced by:** `scripts/build_wikitext103_manifests.py`, dataset revision
`b08601e04326c79dfdd32d625aee71d232d685c3` (`Salesforce/wikitext`, config `wikitext-103-v1`,
pinned 2026-08-08).

This is the overlap validation for the five frozen partition manifests
(`data/manifests/*.jsonl`, hashes in `data/manifests/MANIFEST_HASHES.json`). It covers exact
duplication and near-duplication, both within the raw upstream release and across the
partitions this project constructs from it.

## 1. Exact overlap

`assert_disjoint` (`src/human_data_budget/data/separation.py`) was run over all five partitions'
`example_id`s and, separately, over all five partitions' `content_hash`es (normalized-text
SHA-256). Both checks passed after the deduplication in §2 — **zero exact overlap** by ID or by
content across `base_train`, `rescue_candidates`, `prompts`, `validation`, and `test`.

## 2. Exact duplicates found in the raw upstream release

Before partitioning, the pinned WikiText-103-v1 release itself contains exact-duplicate
articles: **241 articles** whose normalized text exactly matches another article elsewhere in
the release (`data/manifests/MANIFEST_HASHES.json` → `exact_duplicates_dropped`). This is not a
parsing artifact — see `_is_article_title_row` in `scripts/build_wikitext103_manifests.py` for
the article-boundary rule, which was itself hardened against a real false-positive mode
(infobox/table legend lines like `= Position ; GP = ` inside sports-roster articles matching the
naive top-level-heading pattern; fixed by requiring blank-line isolation on both sides).

**One of the 241 crosses the train/test boundary**: *"The Hustler (film)"* appears verbatim at
train row 239010 and test row 4303 of the canonical release. Left unhandled, this is train/test
leakage baked into the upstream dataset, independent of anything this project does.

**Resolution, applied in `_dedup_exact`:** articles are deduplicated by content hash processing
splits in priority order `test → validation → train`; the first occurrence wins and later
duplicates are dropped entirely (not reassigned to another partition). This guarantees:

- `validation` and `test` are exactly the canonical HF splits, unchanged (60 articles each,
  matching the published article counts for WikiText-103).
- No article present in `validation` or `test` can also appear in any train-derived partition.
- The 240 remaining duplicate pairs, which are train-internal, are collapsed to one copy each
  (redundant training data, not a validity threat, but removed for a clean token count).

## 3. Near-duplicate scan

Full pairwise Jaccard is O(n·m) and intractable at this scale (28,231 deduplicated train
articles). The scan is scoped to the leakage-critical boundary — every train-family article
(`base_train`, `rescue_candidates`, `prompts`) against every eval-family article (`validation`,
`test`) — prefiltered to articles within ±20% token count of each other, then scored with exact
(non-sampled) word-8-gram Jaccard at the same 0.8 threshold used for fixture-scale checks in
`data/overlap.py`.

**Result: 0 pairs at or above 0.8 Jaccard.** Scan ran in 331s.

**Documented scope limitation:** near-duplicate scanning within the train family
(`base_train` vs `rescue_candidates` vs `prompts`) was not run at full corpus scale — pairwise
cost there is an order of magnitude larger than the train-vs-eval boundary and redundancy
between two training-only partitions is not a validity threat the way train/eval leakage is (it
would only mean some training tokens are duplicated, not that evaluation is contaminated). Exact
duplication within the train family *is* fully covered (§2, deduplicated corpus-wide before
partitioning). If a future stage needs fuzzy within-train dedup (e.g. to reduce memorization),
that is a separate, explicitly scoped pass — not silently assumed to be covered by this freeze.

## 4. Reproducibility

Every number above is deterministic given the pinned dataset revision: article boundaries,
stable IDs (`sha256(f"wikitext103-v1:{revision}:{split}:{start_row}")[:16]`), the train/rescue/
prompts hash-modulo split, and the dedup priority order are all fixed in
`scripts/build_wikitext103_manifests.py`. Re-running the script reproduces byte-identical
manifest files and hashes.
