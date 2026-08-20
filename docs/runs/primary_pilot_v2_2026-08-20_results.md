# Corrected grid (v2) — execution record and primary result

**Run id:** `primary_pilot_v2_2026-08-19` (config), executed to completion 2026-08-20
**Config:** `configs/experiment/primary_pilot_v2.json` (`FROZEN`)
**Artifacts:** `results/runs/primary_pilot_v2_2026-08-20/`
**Hardware:** 2× RTX 4090, RunPod, at an observed $3/hour
**Chains:** 25 of 25 complete, 0 failed
**Certification:** **25 `valid_with_limitation`, 0 `invalid`.** `validate_run.py` exits 1,
which is the *limited* code (`0 valid / 1 limited / 2 invalid / 3 usage`, F-024)
**Every number below is generated** by `scripts/generate_pilot_outputs.py` into
`paper/tables/pilot_macros.tex`. None is typed by hand.

## Status of the primary contrast: VALID, AND C-002 IS NOT SUPPORTED

`run_pilot --check-only` exits 0. Both axes `PROTOCOL.md` §4 requires hold:

```
spending arms:           749,709 to 749,995 against a 750,000 ceiling
                         0.0381% spread, 0.2000% permitted
total optimizer tokens:  16,678,912 to 16,678,912
                         0.0000% spread, 0.2000% permitted
control arms held to an exact zero: 1 arm, 5 chains
```

This is the condition the previous grid failed on both counts — 10.1070% on the human
axis (F-020) and 2.2564% on the total axis (F-021). The comparison is therefore
admissible, and what follows is a result rather than a precondition failure.

**Primary estimand** (`PREREGISTRATION.md`): paired chain-level difference in held-out
human NLL-regret AUC, joint minus the strongest eligible non-joint baseline. Lower
favours joint.

**Strongest eligible non-joint baseline: `selection_only`** (lowest mean AUC regret of
the four non-joint arms). The *rule* is preregistered; which arm satisfies it is read
from the outcome, and this line is the record of that.

```
joint - selection_only = +0.01026   95% CI [-0.00916, +0.02968]   +0.45% relative
practical-equivalence region        ±0.05073   (2% of the fresh-random mean)
interval lies entirely inside it    yes
```

**C-002 is not supported.** Its falsification clause voids the claim if the interval
includes the practically equivalent or harmful region, and this interval lies *wholly*
within it. That is the strong form of the negative: not "we could not tell", but
"joint and selection-only are practically equivalent at this operating point, and the
data are precise enough to say so". The interval's furthest reach from zero is 0.0297,
against a 0.0507 threshold — it does not come close to clearing the bar.

The verdict does not depend on how the threshold's denominator is read. U-006 was
settled against the fresh-random mean (`effect_threshold_review_2026-08-19.md` computes
0.05049 as 2% of 2.52454, and `powered_design_sizing_2026-08-19.md` sizes against the
same figure), giving ±0.05073 here. Taken instead against the strongest baseline it is
±0.04586. The interval is inside both. The generator emits both figures so a reader can
check, because a threshold denominator touched after outcomes are open is exactly what
U-006 exists to constrain.

## Per-arm results

| Policy | Chains | Human tokens | AUC regret | SD | CV | Tail retention |
|---|---|---|---|---|---|---|
| No rescue (control) | 5 | 0 | 2.6431 | 0.0140 | 0.53% | 0.8676 |
| Fresh random | 5 | 749,869 | 2.5364 | 0.0080 | 0.32% | 0.8769 |
| Schedule-only | 5 | 749,878 | 2.5261 | 0.0194 | 0.77% | 0.8846 |
| Selection-only | 5 | 749,827 | 2.2931 | 0.0250 | 1.09% | 0.9024 |
| Joint time-and-mode | 5 | 749,827 | 2.3034 | 0.0221 | 0.96% | 0.9024 |

## Secondary contrasts

All four arms are matched on both axes, so unlike the previous grid every contrast here
is admissible. Paired by seed, 95% t interval on 4 degrees of freedom.

| Contrast | Mean | 95% CI | Relative | Reading |
|---|---|---|---|---|
| `random` − `no_rescue` | −0.10670 | [−0.12144, −0.09196] | −4.04% | spending human tokens at all helps, and clears the 2% bar |
| `selection_only` − `random` | −0.24330 | [−0.26872, −0.21787] | −9.59% | **which** examples you buy matters, and matters a lot |
| `schedule_only` − `random` | −0.01032 | [−0.03632, +0.01567] | −0.41% | **when** you spend does not detectably matter |
| `joint` − `selection_only` | +0.01026 | [−0.00916, +0.02968] | +0.45% | adding timing to selection buys nothing |
| `selection_only` − `no_rescue` | −0.34999 | [−0.37081, −0.32918] | −13.24% | full effect of well-targeted rescue |
| `joint` − `no_rescue` | −0.33973 | [−0.36106, −0.31840] | −12.85% | joint also beats the control decisively |

The `schedule_only` − `random` null replicates the previous grid's one clean contrast,
now with both budget axes holding rather than one.

**The shape of the result.** Spending helps; targeting under-covered modes helps about
2.3 times as much again; scheduling when to spend does not move the primary outcome;
and combining scheduling with targeting is indistinguishable from targeting alone. The
question this project asked was whether *when* you spend and *which* modes you target
both matter under a fixed lifetime budget. At this operating point the answer is that
the second does and the first does not.

## Confirmatory outcome

`PREREGISTRATION.md` names the frozen tail-retention metric as confirmatory. It agrees
with the primary on the primary contrast and disagrees on one secondary.

| Contrast | Mean | 95% CI |
|---|---|---|
| `joint` − `selection_only` | +0.00003 | [−0.00100, +0.00105] |
| `schedule_only` − `random` | +0.00766 | [+0.00563, +0.00968] |

The primary contrast is a tighter null on the confirmatory outcome than on the primary
one. **The timing contrast is not.** On tail retention `schedule_only` beats `random`
with an interval excluding zero — a real difference, though at 0.87% of the random mean
it is below the 2% relative bar the project uses for practical significance on the
primary outcome. Applying that bar to a different metric is an extension, not something
U-006 settled, so the honest statement is: timing shows no detectable effect on the
primary outcome and a small, statistically distinguishable, practically minor effect on
the confirmatory one. It is recorded here because it was measured, not because it helps.

## Variance

Between-chain CVs run 0.32% to 1.09%, against 0.41%–1.08% in the previous grid. The
variance estimate that released `COMPUTE.md`'s compute gate is reproduced by an
independent 25 chains under a changed corpus-assembly rule, which is the strongest
check it has had. `powered_design_sizing_2026-08-19.md`'s conclusion is unchanged: three
chains per arm suffice at the preregistered threshold, and the frozen five-seed set
exceeds it.

## Feasibility

| Figure | Hours | Meaning |
|---|---|---|
| Clean | 5.96 | Launches in which every chain finished. What a reproducer should budget |
| Productive | 8.53 | Launches that completed at least one chain, including the attempt F-026 killed after four |
| Total | 9.56 | Every launch in this directory, including one that produced nothing |

All three are read from `wall_seconds` in the shard summaries, never inferred from
timestamps — F-020a is the record of what happens otherwise. Measured throughput was
**5.07 min per generation** on 2× RTX 4090. At the observed $3/hour the clean figure is
roughly $18.

The grid was completed in four seed-block phases (`DECISIONS.md` P-012), so its wall
time is the *sum* of per-phase longest shards, not the longest shard overall. A single
maximum over the summaries returns 3.35 h, which is one phase and not the run.

## What this run does not establish

- **Three of the seven comparators C-002's contract names never ran.** Accumulation or
  fixed-fraction (5), detector/importance-resampling selection (6), and oracle mode
  information as a non-deployable upper bound (7) are not implemented. "Strongest
  eligible baseline" therefore means strongest *among the four that exist*. The absent
  oracle upper bound in particular bounds what any result here can claim.
- **One operating point.** GPT-2, WikiText-103, horizon 10, a 750,000-token lifetime
  budget, one corpus-assembly rule. The equivalence of joint and selection-only is
  measured there and nowhere else. Nothing here speaks to larger models, longer
  horizons, or different budget ratios.
- **The 2% threshold is a project decision, never externally reviewed.** U-006 is
  settled and was checked against measured anchors, but the mentor/statistics review the
  repository calls for has not happened. The equivalence verdict rests on that bar.
- **Standing certification limitations.** All 25 chains carry
  `LIMIT_NEAR_DUPLICATE_NOT_CHECKED` (28,351 examples carried no text and were not
  compared) and `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE` (no realised batch records to
  recompute the declared ledger against). Neither is new and neither is about this run;
  both are why the certification is `valid_with_limitation` rather than `valid`.
- **`joint` is not shown to be worse.** The interval covers zero. The finding is
  equivalence to selection-only, not inferiority to it.

## Provenance

- **Seed-block ordering** (P-012) determined which chains ran when, never which ran.
  All 25 completed, so the ordering leaves no trace in the design. Had it stopped early
  the retained seeds would have needed naming; it did not.
- **The eight chains that predate the final phases** were produced by the launch F-026
  killed. They are ordinary completed chains — the defect stopped chains from starting,
  never corrupted one that finished — and are skipped-and-reused by the resume path
  exactly as any completed chain is.
- **No chain was excluded.** `aggregate.json` records 25 included, 0 excluded, and
  `SUBMISSION_CHECKLIST.md`'s rule that no `invalid` chain enters an analysis is
  satisfied vacuously: there are none.
- **Code:** the F-026 fix (`e88a6b3`) and `--only-seeds` (`088b7ff`) were in the tree
  for every phase. `scripts/generate_pilot_outputs.py` was changed *after* the run, to
  gate the primary contrast on measured budget axes rather than on a hardcoded refusal
  naming F-020; that change is reported in this document rather than left implicit,
  because it is the difference between a script that refuses to compute a contrast and
  one that computes it.
