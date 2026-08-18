# Tail-Retention Metric Freeze Audit

**Owner:** Neil (data, evaluation, and validity lead)
**Status:** FROZEN 2026-08-08
**Closes:** the metric-choice half of `DECISIONS.md` U-004 ("Exact tail-retention metric?").
**Does not close:** `nll_threshold_candidate` (`configs/evaluation/primary.json`) — see §4.

## 1. The two candidates

Both are implemented and unit-tested since Week 1 (`src/human_data_budget/evaluation/tail.py`,
`tests/evaluation/test_metrics.py`, `tests/evaluation/test_logit_nll.py`):

- **`tail_retention`** (ratio-based): mean of `clip(current_mode_nll / reference_mode_nll, 0, 1)`
  over the frozen tail modes. Requires a **reference mode-score snapshot** — per-mode mean NLL
  captured from the baseline model at generation 0 of a real chain.
- **`nll_gap`**: mean tail NLL minus mean common NLL on the *same* checkpoint. Requires no
  reference; computable from any single evaluation run.

## 2. Reliability and independence audit

| Criterion | `tail_retention` (ratio) | `nll_gap` |
|---|---|---|
| **Independence from policy selection score** | Yes — signature takes only mode-score mappings, never touches `models.py`'s `undercoverage_score`. Docstring states this explicitly; behavior is not separately unit-tested against the policy module because the two modules have no import relationship to violate. | Yes — same argument; verified by `test_nll_gap_independent_of_policy_score`. |
| **Determinism / reliability of the formula itself** | Deterministic pure function; clipping to `[0, 1]` bounds it against reference-NLL noise. 4 unit tests (`test_metrics.py`, `test_logit_nll.py`) cover normal, missing-mode, and non-positive-reference cases. | Deterministic pure function; unbounded. 6 unit tests cover positive/negative/zero gap and empty-input rejection. |
| **Data availability right now** | **Blocked.** No reference mode-score snapshot exists yet — Stage A (positive control) evaluates only aggregate perplexity/eval_loss with no mode breakdown (`docs/positive_control/measurements/generation_0/eval_results.json`), and the Stage 4 pilot baseline has not been run. This is why `positive_control_adapter.build_chain_result` currently refuses rather than emit a `ChainResult` (`src/human_data_budget/runner/positive_control_adapter.py:681`). | Computable immediately from any checkpoint with mode-labeled held-out examples — no missing input. |
| **What it measures** | Retention of tail capability *relative to a fixed starting point* — directly the quantity `DECISIONS.md` D-006 names as a primary outcome ("tail retention... rare-mode loss"), bounded and comparable across conditions since it is normalized to `[0, 1]`. | Asymmetry *within one checkpoint* (is tail harder than common right now). Related but distinct question; unbounded scale makes cross-condition effect-size comparison harder. |

`nll_gap` is more *immediately computable* — that is a real advantage and the reason it stays in
the schema as a required field (`schemas/evaluation.schema.json`), not a reason to make it
primary. `tail_retention`'s blocker is data availability (a reference snapshot that does not
exist yet), not a defect in the metric's reliability or independence. The research question this
project is built around is retention across recursive generations relative to a starting point
— `nll_gap` cannot answer that question even once a reference exists, because it never uses one.

## 3. Decision

**Frozen primary: `tail_retention` (ratio-based). Frozen secondary: `nll_gap`.** This matches
the Week 1 provisional labeling in `configs/evaluation/primary.json`; Week 2 makes it a decision
rather than a placeholder, on the reliability/independence grounds in §2.

**Frozen reference-snapshot contract**, so this decision is actually actionable once a baseline
exists: `reference_mode_scores: Mapping[str, float]` maps each tail mode name (`tail.py`'s
`tail_modes` parameter, drawn from the frozen `article_length_quantile` definition —
`docs/data/mode_definition_audit.md`) to a **monotone-decreasing transform of** that mode's
mean held-out NLL on the generation-0 baseline checkpoint, measured over the `validation`
partition.

> **Orientation correction, 2026-08-18 (`FAILURE_LOG.md` F-011).** This clause previously
> read "to that mode's mean held-out NLL", i.e. the raw figure. That is inconsistent with
> the metric it feeds and would invert the primary outcome. `tail.py` computes
> `clip(current / reference, 0, 1)`; NLL *rises* as a model degrades, so a degraded model
> yields a ratio above 1 that clips to **1.0** — reporting perfect retention for the worst
> case, and rewarding degradation up to the clip.
>
> Four artifacts fix the orientation as higher-is-better and one did not: the implementation
> in `evaluation/tail.py`; its docstring ("1.0 means the model preserves all tail coverage");
> `tests/evaluation/test_metrics.py`, which asserts `tail_retention({"rare": 0.5},
> {"rare": 1.0}, {"rare"}) == 0.5`, so a lower current score must give lower retention; and
> the toy path in `runner/chain.py`, which passes `1.0 - undercoverage`. The wording here was
> the outlier, so the wording is what changes.
>
> **What is not changed:** the frozen decision itself. `tail_retention` remains primary,
> `nll_gap` secondary, the snapshot is still captured from the generation-0 baseline over the
> `validation` partition, and the timing clause below still applies. Only the orientation of
> the quantity is corrected.
>
> **Reference implementation:** `evaluation.real.mode_nll_to_retention_scores`, the
> reciprocal `1 / max(nll, 1e-6)`. Any monotone-decreasing transform satisfies the contract;
> the reciprocal is the one in the tree and is applied explicitly by the caller, never
> implicitly. `evaluation.real.score_examples` continues to emit raw per-mode NLL so the
> underlying measurement stays available unconverted. It must be captured immediately
after the generation-0 evaluation and before generation 1 begins, and persisted before it can be
overwritten by later-generation state. Wiring that capture and persistence into the runner
(where the file lives, what triggers the write) is a runner-ownership implementation task, not
decided here — this section fixes only the shape and timing every implementation must satisfy.

## 4. What remains open

`nll_threshold_candidate` (`configs/evaluation/primary.json`) stays `pending_week2_freeze`. It is
explicitly defined as data derived from "the baseline NLL distribution on the validation
partition" of a real trained model — that model doesn't exist yet. Freezing a number here without
that input would be exactly the sentinel-filling `PROTOCOL.md` §1 and
`positive_control_adapter.build_chain_result`'s docstring both refuse to do. This is downstream
of this freeze (blocked on a real baseline run), not blocked by it.

**Stage A is unaffected by this freeze.** `build_chain_result`'s refusal for the positive-control
reproduction is not primarily about the metric being unfrozen — Stage A's upstream pipeline
(GPT-2 / WikiText-2, `docs/positive_control/report.md`) produces no mode-level evaluation at all,
so it has no `current_mode_scores` to feed either metric regardless of which is primary. This
freeze unblocks the Stage 4 Human Data Budget pilot's evaluation contract, not Stage A.
