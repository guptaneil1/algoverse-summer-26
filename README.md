# Geometry of Collapse Rescue Data

**Which properties of human-written text actually prevent model collapse?**

[![CI](https://img.shields.io/badge/ci-github_actions-blue)](.github/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-TBD-b31b1b)]()

Models trained recursively on their own outputs collapse (Shumailov et al., 2023). Mixing in real human data prevents it (Gerstgrasser et al., 2024). Kovač et al. (2025) showed *semantic diversity* of that rescue data is what matters — on short-form social media text — and warned their finding may not generalize. **This repo tests that warning directly**, on long-form formal text, while independently manipulating three properties of a fixed-budget rescue set:

| Axis | Levels | Where it's implemented |
|---|---|---|
| **Dose** | 1% / 5% / 10% of training tokens | `rescue_sets.build_rescue_set` |
| **Document length** | short / medium / long (token-matched) | `rescue_sets.LENGTH_BUCKETS` |
| **Character noise** | 0% / 1% / 5% CER | `rescue_sets.inject_noise` |

Model: Pythia-160M. Loop: 5 generations, each trained on the previous generation's synthetic output plus the fixed rescue set. Metrics: SelfBLEU, embedding cosine diversity (MiniLM), held-out perplexity, tail retention, optional LLM-judge quality — matched to Kovač et al. so numbers are directly comparable.

## Status (updated Jul 9)

**The loop is closed.** `configs/dev_tiny.yaml` has been run end-to-end (CPU): train → generate → mixture audit → retrain → evaluate → `summary.csv`, surviving a hard mid-run kill via resume. Even at toy scale the expected collapse signatures appear after one generation: held-out PPL 111→116, tail retention 0.012→0.007. Next: `scripts/timing_test.py` on a real GPU, then `scripts/run_pilot.sh`.

## Quickstart

```bash
pip install -r requirements.txt && pip install -e .

# 0. Smoke test — one closed loop, tiny budget, all metrics (~minutes on CPU)
python -m collapse_rescue.loop --config configs/smoke.yaml

# 1. Prepare the real corpus (once; cache data/ to Drive on Colab)
python scripts/prepare_data.py --config configs/base.yaml

# 2. Measure real runtimes on your GPU (replaces the plan's estimates)
python scripts/timing_test.py

# 3. Run the pilot (4 corners + control×2 seeds + random baseline)
bash scripts/run_pilot.sh          # ends with the automated go/no-go check

# 4. If GO: generate + run the reduced sweep, then analyze
python scripts/make_sweep_configs.py
for f in configs/sweep/*.yaml; do python -m collapse_rescue.loop --config "$f"; done
python scripts/analyze.py          # -> results/all_runs.csv + ANOVA + figures
```

Every run is **resumable**: each stage (train / generate / evaluate) skips itself if its output exists, so a dead Colab session costs the current stage, not the run. One condition = one YAML = one command.

## Repository layout

```
configs/           one YAML per experimental condition
  base.yaml          defaults — sampling params live ONLY here (confound guard)
  smoke.yaml         end-to-end loop in minutes; run this first
  pilot/             the Week-7 pilot: corners + control + baseline
src/collapse_rescue/
  loop.py            THE experiment: recursive train→generate→evaluate loop
  rescue_sets.py     the manipulation: dose, length buckets, noise injection
  train.py           one generation of training (HF Trainer, resumable)
  generate.py        synthetic corpus sampling (params fixed grid-wide)
  data.py            corpus prep, held-out split, rare n-gram list
  evaluate.py        runs all metrics per generation → metrics.json
  metrics/           self_bleu, embedding_diversity, perplexity,
                     tail_retention, llm_judge
scripts/
  prepare_data.py    download/clean corpus, print length percentiles
  run_pilot.sh       the 7 pilot runs, sequential, resumable
  go_no_go.py        automated decision-tree check (2× seed-SD criterion)
  make_sweep_configs.py  reduced grid: 27 cells @1 seed + corners @3 seeds
  timing_test.py     measure train/generate throughput on this GPU
  analyze.py         collect all runs, two-way ANOVA + BH-FDR, figures
tests/test_smoke.py  invariant guards (noise CER, metric direction,
                     sampling-param immutability, dose audit) — run in CI
```

## Design invariants (what makes the comparisons valid)

1. **Total training tokens per generation are constant** across all conditions; dose changes only the human/synthetic ratio. `verify_mixture` audits the realized dose by counting tokens and hard-fails the run if it drifts >1pp.
2. **Length buckets are token-matched** — each bucket delivers the same token budget, so "length" never smuggles in "amount".
3. **Sampling parameters never vary across conditions.** They exist only in the defaults; the sweep generator cannot emit them; `test_sampling_params_never_vary_across_configs` enforces it in CI.
4. **Noise is measured, not assumed**: `inject_noise` returns realized CER, tested to ±0.1% of target.
5. **The held-out split never trains anything** — it exists solely for perplexity and generation prefixes.
6. **Gen-0 human text gets scored first** (`gen0/human_reference_metrics.json`): those are the plot baselines and the cheapest pipeline-bug detector.

## Results layout

```
results/<run_id>/
  config.yaml           frozen exact config for this run
  gen{k}/model/          weights
  gen{k}/synthetic.jsonl generated corpus
  gen{k}/metrics.json    all metrics
  gen{k}/mixture_audit.json  realized-dose audit
  summary.csv            one row per generation — analyze.py's input
```

## Key references

- Shumailov et al. (2023), *The Curse of Recursion*, [arXiv:2305.17493](https://arxiv.org/abs/2305.17493)
- Gerstgrasser et al. (2024), *Is Model Collapse Inevitable?*, [arXiv:2404.01413](https://arxiv.org/abs/2404.01413)
- Kovač et al. (2025), *Recursive Training Loops in LLMs*, [arXiv:2504.03814](https://arxiv.org/abs/2504.03814) — the gap this project fills
- *Escaping Collapse: The Strength of Weak Data*, [arXiv:2502.08924](https://arxiv.org/abs/2502.08924)

## Team

KNAR / Algoverse Research, Summer 2026. See `PLAN.md` for the claims map, week-by-week execution plan, figure specifications, and go/no-go decision tree this repo implements.
