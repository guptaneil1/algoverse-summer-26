# Week 3 Data and Evaluation Appendix

> **STATUS: METHODS COMPLETE, DATA IDENTITY UNRESOLVED.**
> Everything describing *how* data is partitioned and *how* metrics are defined
> is final and unit-tested. Everything naming *which* corpus, revision, or
> example counts is TODO, because `docs/STATUS.md` records the data manifests as
> fixture-only and the final licensed domain as unresolved.

Reproduce the evidence cited here with:

```bash
pytest tests/data tests/evaluation -q
```

---

## 1. Data identity — TODO

| Field | Value |
|---|---|
| Corpus | TODO(neil): the licensed domain, once chosen |
| Source revision | TODO(neil): dataset revision or snapshot date |
| Licence | TODO(neil) |
| Total examples | TODO(neil) |
| Manifest sha256 | TODO(neil) |
| Tokenizer and revision | TODO(neil) |

`configs/data/wikitext103.json` exists as a candidate configuration; it is not a
decision. Nothing below can be instantiated until this table is filled.

## 2. Partitions — method final

Five partitions, pairwise disjoint:

| Partition | Purpose |
|---|---|
| `base_human_train` | Initial human training data for generation 0 |
| `rescue_candidates` | The pool human rescue tokens are bought from |
| `generation_prompts` | Prompts used to produce synthetic text |
| `validation` | Monitoring and any tuning the protocol permits |
| `final_human_test` | Held-out human evaluation. **Radioactive.** |

**Splitting rule.** Assignment happens on a stable normalized content hash
(`src/human_data_budget/data/hashing.py`: NFKC normalize, collapse whitespace,
SHA-256) computed **before** any partition is used. Hashing first means an
example cannot drift between partitions when its formatting changes.

**The test-partition rule.** No `final_human_test` example may influence
prompting, selection, thresholds, early stopping, or hyperparameters. Violating
this invalidates everything downstream while leaving all tests green, which is
why it is checked structurally rather than by review.

| Forbidden pair | Enforced in |
|---|---|
| `base_human_train` / `final_human_test` | `validation/audit.py`, `tests/data/test_overlap.py` |
| `rescue_candidates` / `final_human_test` | same |
| `generation_prompts` / `final_human_test` | same |
| `validation` / `final_human_test` | same |
| `base_human_train` / `rescue_candidates` | same |

**Counts:** TODO(neil) — one row per partition once the corpus is fixed.

## 3. Overlap detection — method final, one gap

Exact-duplicate detection compares normalized content hashes and is wired into
the validator. **Near-duplicate detection is implemented in
`src/human_data_budget/data/overlap.py` but the auditor does not yet call it**,
so a paraphrased leak currently passes. This is logged as a severe blind spot in
`docs/validity/week3_adversarial_audit.md` section 8 and must be closed before
any real chain is certified.

## 4. Provenance — method final

Every training example carries: `stable_id`, `content_hash`, `source_dataset`,
`origin` (human or synthetic), recursive generation, selection policy and score,
whether selected, and number of optimizer presentations.

The validator returns `SEPARATION_MISSING_ID` or
`SEPARATION_MISSING_PROVENANCE` when any of the first four is absent.

**Open defect:** `run_manifest.json` does not currently emit a `data.partitions`
block, so provenance cannot be verified on a real run. Confirmed against the toy
chain. See the runner integrity report section 2.

## 5. Token accounting — method final

Counted from **realized batches actually consumed by the optimizer**, never from
character or document estimates (`data/token_accounting.py`).

| Rule | Consequence |
|---|---|
| Padding does not count | Positions with `attention_mask == 0` are excluded |
| Repeated exposure counts every time | Showing one example twice costs twice |
| Gradient accumulation is neutral | Split batches total exactly as one batch |
| Human and synthetic ledgers are separate | `origin` selects the ledger |

**Budget matching.** Two conditions are comparable only if they consumed
identical lifetime human-origin tokens **and** identical total optimizer tokens
(`validate_matched_budgets`). Enforced at three points: config
(`tests/runner/test_reference_configs.py`), preflight before launch, and audit
(`BUDGET_HUMAN_MISMATCH`, `BUDGET_TOTAL_MISMATCH`).

**Known limitation:** the validator compares recorded totals against the frozen
budget; it cannot recompute them from realized batches. An internally consistent
but wrong ledger would pass.

## 6. Held-out NLL — method final

Negative log-likelihood on `final_human_test`, from target-token log
probabilities (`evaluation/logit_nll.py`). Padding excluded; the evaluated token
count is recorded so two runs are comparable; invalid inputs are rejected rather
than silently coerced. The validator rejects non-finite values
(`EVALUATION_NLL_NOT_FINITE`) but never judges magnitude — a high NLL is a
finding, not a validity failure.

## 7. Primary tail metric — method final

`tail_retention` (`evaluation/tail.py`): the mean clipped ratio of current to
reference coverage over frozen tail modes, in `[0, 1]`. 1.0 means full tail
coverage relative to the reference.

Properties, each with a test in `tests/evaluation/test_tail_metric.py`:

| Property | Why it matters |
|---|---|
| Deterministic | Same inputs, same value |
| Directional on controlled fixtures | Worse coverage scores lower |
| Bounded in `[0, 1]` | Overshoot clips to 1.0 |
| Finite on allowed edge cases | Zero coverage gives 0.0, not a crash |
| **Independent of the policy score** | Computed from a frozen reference, not the policy's own undercoverage score — a policy cannot score well by gaming its own selection signal |

Non-positive reference scores and missing modes raise rather than return a
plausible number.

`nll_gap` is a secondary candidate: mean tail NLL minus mean common NLL,
computed from held-out values only.

**Which modes are tail modes:** TODO(neil) — the frozen tail-mode set depends on
the corpus.

## 8. Reliability evidence

| Check | State |
|---|---|
| Metric unit tests | ✅ `tests/evaluation/` passing |
| Determinism on identical inputs | ✅ at unit level |
| Evaluator determinism on real model outputs | ❌ NOT TESTED |
| Directionality on real data | ❌ NOT TESTED |
| Inter-run stability | ❌ no runs exist |

## 9. Known limitations

1. Data identity unresolved — everything in section 1 is TODO.
2. Near-duplicate overlap not wired into the auditor (section 3).
3. Token ledgers compared, not recomputed (section 5).
4. Manifest emits no partition provenance (section 4).
5. Tail-mode set undefined until the corpus is fixed (section 7).
6. No evaluator evidence from a real model (section 8).

Items 2 and 3 are the severe ones: each allows an invalid chain to be classified
`valid`. Neither may be closed by relaxing a rule at the freeze — stop and report
instead.
