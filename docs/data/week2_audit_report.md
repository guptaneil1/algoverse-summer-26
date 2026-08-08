# Neil — Week 2 Data & Evaluation Audit Report

**Branch:** `week-2/neil-frozen-data-metrics`
**Date:** 2026-08-08
**Deliverable (per `docs/weekly/WEEK_2.md`):** immutable manifest bundle plus frozen evaluator
and validation report.

This report is the single entry point for everything frozen this week. It links out to the
detailed audits rather than repeating them.

## 1. What is frozen

| Item | Frozen value | Evidence |
|---|---|---|
| Licensed domain | WikiText-103-v1, `Salesforce/wikitext` revision `b08601e04326c79dfdd32d625aee71d232d685c3` | `DECISIONS.md` D-019, `data/datasheet.md` |
| Mode definition | `article_length_quantile` (tail ≤ 1106 tokens, common > 2661 tokens) | `DECISIONS.md` D-020, `docs/data/mode_definition_audit.md` |
| Dataset preprocessing | Blank-line-isolated top-level-heading article boundaries; exact-dup removal (test>validation>train priority) | `scripts/build_wikitext103_manifests.py`, `docs/data/overlap_report.md` |
| Five disjoint partitions | `base_train` (22,637 ex / 80.67M tok), `rescue_candidates` (4,235 ex / 14.86M tok), `prompts` (1,359 ex / 4.81M tok), `validation` (60 ex / 213.9k tok), `test` (60 ex / 241.2k tok) | `data/manifests/MANIFEST_HASHES.json`, `data/datasheet.md` |
| Stable IDs & content hashes | `sha256(f"wikitext103-v1:{revision}:{split}:{start_row}")[:16]`; SHA-256 of NFKC-normalized text | `src/human_data_budget/data/hashing.py`, `scripts/build_wikitext103_manifests.py` |
| NLL implementation | `evaluation/nll.py` (from log-probs), `evaluation/logit_nll.py` (from raw logits, padding-excluded) — unchanged since Week 1, re-verified this week | `tests/evaluation/` (24 tests) |
| Primary tail-retention metric | `tail_retention` (ratio-based), secondary `nll_gap` | `DECISIONS.md` D-022, `docs/evaluation/tail_retention_freeze.md` |
| Token accounting | Padding exclusion, multi-epoch repetition, batching, gradient-accumulation regrouping, resume-boundary additivity | `src/human_data_budget/data/token_accounting.py`, `tests/data/test_token_accounting.py` (10 tests) |
| Manifest loading | Now accepts both text-bearing records (fixtures) and frozen hash-only records (immutable manifests), with a mismatch check between them | `src/human_data_budget/data/manifest.py`, `tests/data/test_manifest.py` |

## 2. What is explicitly not frozen (and why)

- **`nll_threshold_candidate`** (`configs/evaluation/primary.json`): needs the baseline NLL
  distribution on `validation` from a real generation-0 model, which does not exist yet.
  Tracked as `DECISIONS.md` U-004b.
- **The optimizer tokenizer**: owned by the training config, not this freeze. Token counts in
  this freeze are whitespace-split estimates, consistently labeled as such everywhere they
  appear (`data/datasheet.md`, `configs/data/wikitext103.json`).
- **`reference_mode_scores` capture/persistence wiring**: this freeze fixes the *contract*
  (`docs/evaluation/tail_retention_freeze.md` §3) but the runner implementation that captures and
  persists it during a real chain run is a separate, runner-owned task.
- **Fuzzy near-duplicate screening within the train family** (`base_train` vs
  `rescue_candidates` vs `prompts`): scoped out of this freeze for cost reasons; exact-hash
  dedup *is* full-corpus. See `docs/data/overlap_report.md` §3.

## 3. Real findings from this week's work

Two things were discovered while building the real manifests, not assumed in advance:

1. **The canonical WikiText-103-v1 release contains train/test leakage.** One article appears
   verbatim in both train and test, plus 240 further train-internal exact duplicates. This is
   fixed by deduplication before partitioning (`docs/data/overlap_report.md` §2) — but anyone
   using the raw HF release directly inherits the leak.
2. **A naive top-level-heading parser over-splits real articles.** Infobox/table legend lines
   (e.g. `= Position ; GP = `) match the same textual pattern as a real article title but are not
   isolated by blank lines; the fix (`_is_article_title_row`) requires blank-line isolation on
   both sides. Verified against the published WikiText-103 article counts (60 validation / 60
   test articles) as a correctness check.

## 4. Validation performed

- `assert_disjoint` over all five partitions' example IDs and, separately, content hashes: passes
  (`docs/data/overlap_report.md` §1).
- Near-duplicate scan, train-family vs eval-family, word-8-gram Jaccard ≥ 0.8, ±20% token-count
  prefilter: 0 pairs found (§3 of the same report).
- Full test suite for owned modules: `pytest tests/data/ tests/evaluation/ tests/contracts/` —
  61 passed.
- `ruff check` clean on all changed/added files.
- Manifest rebuild is deterministic: dataset revision, parsing rule, stable-ID scheme, and
  partition/mode thresholds are all pinned in `scripts/build_wikitext103_manifests.py`;
  re-running reproduces the same hashes.

## 5. Handoff notes for the team

- **Aarav** (`PREREGISTRATION.md`, not edited here per `.github/CODEOWNERS`): please incorporate
  the frozen primary/secondary tail-retention choice and the `reference_mode_scores` contract
  from `docs/evaluation/tail_retention_freeze.md`.
- **Khantushig** (runner): the `reference_mode_scores` capture/persistence wiring described in
  §2 above is needed before `positive_control_adapter`-style code can emit a real `ChainResult`
  for a Stage 4 pilot chain. Stage A itself is unaffected (see `DECISIONS.md` D-022 scope note).
- Raw manifest files under `data/manifests/*.jsonl` are intentionally not committed
  (`data/README.md`); rebuild locally with `python scripts/build_wikitext103_manifests.py`
  (`pip install huggingface_hub pyarrow` first) if you need the actual per-example data.
