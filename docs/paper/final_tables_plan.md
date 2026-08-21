# Table plan for the final experiment

**Status:** Implemented and run against the corrected grid. `scripts/generate_final_tables.py`
produces the tables and the figure in `docs/paper/final_tables/` from
`results/runs/primary_pilot_v2_2026-08-20`, the 25-chain run in which both budget axes
hold. Whether any of it may be quoted in the manuscript is `PROTOCOL.md` §5's question,
not this file's.
**Date:** 2026-08-20
**Author:** drafted for owner review; `paper/` is `@Ronit`'s under `.github/CODEOWNERS`, so
nothing under `paper/` is edited by this document.

## What this is

The grid is the frozen design re-run with both budget axes asserted and P-011
displacement in force: five arms × five preregistered seeds = 25 chains, horizon 10, GPT-2
at a pinned revision, WikiText-103 subsampled to 400 articles, 750,000 human-origin
optimizer tokens per chain (`configs/experiment/primary_pilot.json`). This document fixes
the *shape* of every table that run can support — columns, ordering, rounding, captions,
and the gate that decides whether a cell holds a number or a refusal — so that when the
chains land the only change is the input path. It is the same discipline
`results/tables/README.md` already applies to the fixture tables.

## What the run will actually yield

Tracked, one file per chain, `results/runs/<RUN_ID>/<arm>/seed<N>/chain_result.json`,
schema `schemas/chain_result.schema.json`:

| field | type | feeds |
|---|---|---|
| `policy`, `chain_seed` | label | row identity in every table |
| `consumed_human_tokens` | int | T1 (human axis) |
| `consumed_total_tokens` | int | T1 (total axis) |
| `generations_completed` | int | completeness column |
| `valid`, `exclusion_reason` | bool / str | T5 certification column |
| `metrics[g].human_nll` | float, g = 0..9 | primary outcome, T2/T3/T6 |
| `metrics[g].tail_retention` | float in [0,1] | confirmatory outcome, T2/T3 |

Derived in the analysis, never typed: NLL-regret AUC (trapezoid over
`human_nll[g] - human_nll[0]`, `scripts/generate_pilot_outputs.py:64`), paired-by-seed
differences with a t-interval at 4 df, between-chain SD and CV.

Not in `chain_result.json`, but written per generation to the checkpoints by
`runner/real_chain.py:321-336`: `allocations` (per-example presentations and scores) and
`mode_statistics`. Those are what T7 and T8 need, and they live in the untracked 162 MB
manifest tree — **if the final run's checkpoints are not archived, T7 and T8 cannot be
built afterwards.** That is the one collection decision this plan asks for before launch,
not after.

Mode vocabulary is three-valued in the frozen manifests — `common` 2,105, `mid` 1,697,
`tail` 433 rescue candidates — while `tail_modes` is `["tail"]`. So a per-mode table has
three rows, not two.

## The tables

Ordering is the frozen presentation order everywhere: `no_rescue`, `random`,
`schedule_only`, `selection_only`, `joint` (`generate_pilot_outputs.py:36`). Booktabs
rules, caption above, `\input{tables/...}` from the section. Rounding: outcome quantities
4 dp, percentages 2 dp, token counts with thousands separators, retention 4 dp.

### T1 — Budget realisation (main body, before any outcome)

The fairness precondition is what failed twice in the pilot, so it is reported before the
results it licenses rather than in an appendix.

```latex
\begin{tabular}{lrrrrc}
\toprule
Policy & Chains & Human tokens & \% of ceiling & Total tokens & Matched \\
\midrule
No rescue (control) & \Res & \Res & \Res & \Res & --- \\
Fresh random        & \Res & \Res & \Res & \Res & \Res \\
Schedule-only       & \Res & \Res & \Res & \Res & \Res \\
Selection-only      & \Res & \Res & \Res & \Res & \Res \\
Joint time-and-mode & \Res & \Res & \Res & \Res & \Res \\
\midrule
Spread across spending arms & & \Res\% & & \Res\% & \\
\bottomrule
\end{tabular}
```

`Matched` is a two-axis verdict, not a number: it passes only if the arm sits within the
2% practical threshold on human tokens *and* on total optimizer tokens. The control has no
entry because it spends nothing by construction and is budget-matched to nothing. The
spread row is the quantity `--check-only` asserts; it is what F-021 showed nobody had ever
printed.

### T2 — Per-arm outcomes (main body, the headline table)

```latex
\begin{tabular}{lrrrrrr}
\toprule
& & \multicolumn{3}{c}{NLL-regret AUC} & \multicolumn{2}{c}{Tail retention} \\
\cmidrule(lr){3-5}\cmidrule(lr){6-7}
Policy & Chains & Mean & SD & CV (\%) & Final & SD \\
\midrule
... one row per arm, frozen order ...
\bottomrule
\end{tabular}
```

Primary outcome and confirmatory outcome side by side, both per arm, both with
between-chain spread. CV is kept because it is the quantity the powered-design sizing is
stated in (`docs/decisions/powered_design_sizing_2026-08-19.md`).

### T3 — Paired contrasts (main body, the table the paper is about)

```latex
\begin{tabular}{lrrrrc}
\toprule
Contrast & $\Delta$ AUC & 95\% CI & Relative (\%) & Paired SD & Verdict \\
\midrule
\textbf{Joint $-$ selected baseline} & \Res & \Res & \Res & \Res & \Res \\
\midrule
Joint $-$ schedule-only    & \Res & \Res & \Res & \Res & \Res \\
Joint $-$ selection-only   & \Res & \Res & \Res & \Res & \Res \\
Schedule-only $-$ random   & \Res & \Res & \Res & \Res & \Res \\
Selection-only $-$ random  & \Res & \Res & \Res & \Res & \Res \\
Random $-$ no rescue       & \Res & \Res & \Res & \Res & \Res \\
\bottomrule
\end{tabular}
```

Three constraints on this table, all of them preregistered rather than stylistic:

1. **The top row is the only confirmatory row.** The rest are secondary and the caption
   must say so; `PREREGISTRATION.md` §Multiplicity forbids promoting any of them if the
   top row fails.
2. **`Verdict` takes one of four frozen labels** — Beneficial, Harmful, Negligible,
   Uncertain — decided by the rule in `PREREGISTRATION.md` §Meaningful-effect
   interpretation, not by a p-value and not by the sign of the mean.
3. **Every row is gated on T1**, at the project's own permitted spread rather than at the
   effect threshold. `runner/budget_matching.SPREAD_MARGIN_BELOW_THRESHOLD` (P-008) puts
   the gate an order of magnitude below the 2% practical threshold, so the bar is 0.2% on
   each axis. The generator imports that constant rather than restating it. If either
   axis fails for either arm in a contrast, the row's numeric cells render
   `NOT ESTABLISHED` instead of the numbers. This is not defensive styling: the pilot's numbers existed and were still
   uninterpretable (F-020, F-021), and a table that prints them anyway invites exactly the
   reading the run cannot support.

The baseline named in row 1 is selected by the frozen rule (lower mean AUC on
validation-only screening chains, ties to selection-only) and the generator records
*which* it selected and on what evidence, in the table's comment header. **On this run
that evidence is not the preregistered kind:** no validation-only screening chains exist,
so the two eligible arms are compared on their primary outcomes. The generator says so in
the header rather than letting the table imply a screening step that did not happen, and
the paper should say so too. The preregistered tie-break names the same arm the outcome
comparison does, which limits but does not erase the deviation.

### Figure 1 — Trajectories (main body)

Two panels sharing a generation axis: held-out human NLL on the left, tail retention on
the right, one line per policy, a ±1 SD band across the frozen seeds, and the no-rescue
control dashed. The conventions are taken from the papers this one sits beside:

- **Small multiples, one metric per panel, legend above, generations 0–9 on x** — Drayson
  et al. Figure 1 and Figure 3, Gerstgrasser et al. Figure 2 (Replace vs Accumulate).
- **A shaded band for spread across runs** — Shumailov et al. Figure 1, which plots
  perplexity as $\mu \pm \sigma$ over five runs.
- **A dashed horizontal reference the other lines are read against** — Drayson et al.
  Figure 3's `Oracle` line. Our control plays that role: it spends nothing by
  construction and is the reference point, not a competitor.

What we do *not* copy: Drayson's panels have no uncertainty band at all, and at five
seeds with CVs under 1.1% ours can afford one. Where a convention and the budget rules
conflict, the budget rules win.

### T4 — Per-generation trajectory table (appendix)

Rows are generations 0–9, one column pair per arm (mean, SD) or a single column per arm
with the SD in a companion figure. `results/figures/pilot_nll_by_generation.png` already
carries this as a plot; the table earns its place only if the paper needs exact values at
specific generations. Recommendation: keep the figure, put the table in the appendix.

### T5 — Per-chain appendix table (25 rows)

```latex
Policy & Seed & Human tokens & Total tokens & Gens & AUC regret & Tail retention & Status
```

One row per chain, status from certification (`valid`, `valid_with_limitation`,
`invalid` + code). This is the table that makes the submission checklist's "headline table
reproduced by someone who did not write the analysis" a five-minute job rather than a
re-run, and it is the only place limitation codes belong.

### T6 — Certification summary (appendix)

Counts by status and by limitation code across the grid. Two columns, six-ish rows.
Cheap, and it is the honest version of a sentence like "all chains completed".

### T7 — Allocation profile: *when* the tokens went (appendix, needs checkpoints)

Rows are arms, columns are generations 0–9, cells are mean human tokens spent at that
generation. This is the paper's time axis made visible — it shows schedule-only's frozen
`[0,0,0,0,0,20,20,20,20,20]` shape against joint's reactive one — and no current table or
figure shows it.

### T8 — Mode targeting: *which* modes the tokens went to (appendix, needs checkpoints)

Rows `common` / `mid` / `tail`, columns are the four spending arms, cells are the share of
rescued human tokens landing in that mode. This is the paper's second axis, and without it
"mode-targeted allocation" is a claim with no table behind it.

T7 and T8 are the two tables that distinguish this paper from a schedule-versus-selection
horse race, which is why the checkpoint-retention decision above matters.

## Algoverse checklist §7 compliance

The submission checklist requires of every table and figure: a caption readable on its
own, stated units, a marked best result with the direction of "better" made explicit,
a caption that states the takeaway rather than describing the visual, and an explicit
reference in the text. What that costs each table here:

- **Units and direction go in the header**, not the caption: `NLL-regret AUC ↓`,
  `Tail retention ↑`, tokens labelled as optimizer tokens, AUC in nats × generations.
- **The best result is bolded only inside the comparable set** — the arms whose realised
  spend sits within the permitted spread of one another. Bolding the lowest number in a
  column that mixes arms which received different amounts of data is precisely the
  overclaim the budget apparatus exists to prevent, and on the pilot artifacts it would
  hand the win to an arm the run cannot rank. The caption names the comparable set.
- **Captions state the takeaway**, which for a gated table is the gate: what was not
  established and why. Draft captions are generated into `final_tables/PREVIEW.md`;
  they are drafts for `@Ronit`, not final prose.
- **Every table gets referenced or moved to the appendix.** T4–T8 are appendix tables by
  default; if a section does not reference one, it stays there.

The checklist's other sections bear on tables indirectly. §3 (numbers consistent
everywhere) is what the macro discipline already enforces. §6 (baselines fair) is T1's
entire purpose.

## Generation and enforcement

- `scripts/generate_final_tables.py` emits T1–T5, the figure, `table_data.json` and a
  reviewable markdown preview from any run directory. It imports the outcome computation
  from `generate_pilot_outputs.py` rather than restating it, so the two cannot drift into
  disagreeing about what AUC regret means. T7 and T8 are not implemented: the checkpoints
  they need are not in the tracked artifact set.
- Run it with
  `--run-dir results/runs/primary_pilot_v2_2026-08-20 --config configs/experiment/primary_pilot_v2.json`.
  A later grid changes those two arguments and nothing else.
- Its output reproduces every value published for both grids independently: the pilot's
  AUC means and SDs in `paper/tables/primary_results.tex` and its intervals and budget
  spreads in `paper/tables/pilot_macros.tex`, and the corrected grid's per-arm means, CVs,
  contrasts, intervals and ±0.0507 equivalence region in
  `docs/runs/primary_pilot_v2_2026-08-20_results.md`.
- Prose cites macros. A bare decimal in `paper/sections/` is a test failure today
  (`tests/analysis/test_generated_outputs.py`) and must stay one.
- Fixture tables stay in `results/tables/`; the manuscript's copies stay in
  `paper/tables/`. `tests/scripts/test_artifact_generation.py` already fails if fixture
  generation writes into the manuscript copy.
- Add a test that T3's gate fires: feed the generator a synthetic arm that violates one
  axis and assert the row renders `NOT ESTABLISHED`. A guard never observed to bind is a
  guard whose binding is unverified — three of the pilot's seven defects had that shape.

## One inconsistency this plan surfaces

`paper/tables/method_hyperparameters.tex` is generated from `configs/policy/joint.json`
and prints `Lifetime human tokens 100` — the Week-2 fixture value. §6 of the manuscript
describes the executed grid as running at 750,000
(`paper/sections/06_experiments.tex:87`). Both are generated, both are correct about their
own source, and side by side in one paper they read as a contradiction. Resolving it is
`@Ronit`'s call and belongs in `paper/`; it is recorded here because it is a table defect
and this is the table plan.

## Not verified

Table conventions in the related literature (Drayson et al. EMNLP 2025, Shumailov et al.
Nature 2024) could not be checked in this session: the network egress proxy blocks
`aclanthology.org` and `www.nature.com`. Nothing above is attributed to those papers'
layouts. The conventions used here come from the frozen fixture tables in this repository
and from `PREREGISTRATION.md`, plus the Algoverse submission checklist §7, which the
project owner supplied as a PDF in the session that produced this plan. If the team wants
the final tables to mirror a specific published layout, someone with access should supply
the layout and this plan can be revised against it.
