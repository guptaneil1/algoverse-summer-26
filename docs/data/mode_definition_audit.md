# Mode Definition Freeze Audit

**Owner:** Neil (data, evaluation, and validity lead)
**Status:** FROZEN 2026-08-08
**Decides:** `DECISIONS.md` U-002's dependent question — the tail/common mode definition used by
`tail_retention` and `nll_gap` (`docs/interfaces/evaluation.md`).

## The two candidates (from `data/datasheet.md`, Week 1)

1. **`wikipedia_article_category`** — each article's top-level Wikipedia category defines its
   mode; categories covering < 5% of training tokens are tail.
2. **`article_length_quantile`** — bottom decile of articles by token count is tail; top 50%
   is common; the middle 40% is retained as `mid` and excluded from the frozen primary contrast.

## Reliability and independence audit

The datasheet framed this as an empirical choice ("whichever produces cleaner tail/common
separation under the validation NLL distribution"). That comparison needs a trained baseline
model's per-example NLL, which does not exist yet — Stage 4's baseline model is downstream of
this freeze, not an input to it (`docs/weekly/WEEK_2.md`: Neil's deliverables have "no
current-week dependency" and work from dataset assets alone). Freezing the definition on a
metric that depends on a model that does not exist would not be a real audit, so this freeze is
decided on the two properties that *are* checkable now, before any model exists: reliability
(can the definition be computed at all, deterministically, from the frozen dataset revision?)
and independence (does it depend on anything outside the frozen, licensed corpus?).

| Criterion | `wikipedia_article_category` | `article_length_quantile` |
|---|---|---|
| **Reliability** — computable from the frozen `wikitext-103-v1` release alone | **No.** The HF `Salesforce/wikitext` release (pinned revision `b08601e04326c79dfdd32d625aee71d232d685c3`) ships plain article text only — no category metadata. Category labels would have to be joined in from a live Wikipedia API/dump query, keyed by article title. | **Yes.** Token count is computed directly from each article's own text; no external join. |
| **Independence** — decision doesn't depend on an external system that can drift after the freeze | **No.** Wikipedia's category taxonomy is edited continuously; a title-keyed join made today would not reproduce identically if re-run later, and a small number of WikiText-103 article titles do not resolve cleanly to a single current Wikipedia page (renames, disambiguation, merges since the ~2016 dump). That non-determinism is exactly what a frozen definition must not have. | **Yes.** Depends only on the pinned dataset revision and the tokenizer/whitespace-split rule, both already frozen artifacts. |
| **Coverage** | Would be incomplete for any article whose title join fails; those articles would need a fallback mode anyway. | Every article has a token count; coverage is total by construction. |
| Simplicity noted in Week 1 datasheet | — | "does not require category metadata" — already flagged as the simpler option. |

`wikipedia_article_category` fails reliability and independence outright: it requires data that
is not part of the frozen, licensed dataset revision, sourced from a system (live Wikipedia)
that is not pinned and can change after the freeze date. That is disqualifying on its own,
independent of which produces a "cleaner" split — a definition that cannot be recomputed
identically from the frozen corpus cannot be frozen.

## Decision

**Frozen primary mode definition: `article_length_quantile`.**

- **tail**: token_count ≤ 10th percentile of the *train*-split article token-count distribution
  (computed post-exact-dedup; see `docs/data/overlap_report.md`).
- **common**: token_count > 50th percentile (median) of that same distribution.
- **mid**: everything between the two cutoffs — retained in every manifest with `mode: "mid"`,
  excluded from the frozen `tail_retention` / `nll_gap` primary contrast.
- Thresholds are computed once from `base_train` + `rescue_candidates` + `prompts` (i.e. the
  full train split) and applied unchanged to `validation` and `test` — the definition is frozen
  from train and never re-derived per split, matching standard practice for any frozen boundary.
- Exact frozen threshold values are recorded in `configs/data/wikitext103.json` and
  `data/manifests/MANIFEST_HASHES.json` (`tail_cutoff_tokens`, `common_cutoff_tokens`), produced
  by `scripts/build_wikitext103_manifests.py`.

## What this does not decide

This freezes the mode *definition* only. It does not freeze a `nll_threshold_candidate`
(`configs/evaluation/primary.json`) — that number is explicitly baseline-model-dependent and
stays `pending_week2_freeze` until a real generation-0 baseline exists, which is downstream of
this freeze, not blocked by it.
