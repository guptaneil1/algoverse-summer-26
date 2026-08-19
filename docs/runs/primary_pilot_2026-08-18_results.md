# Primary pilot — execution record and variance estimate

**Run id:** `primary_pilot_2026-08-18`
**Config:** `configs/experiment/primary_pilot.json` (`FROZEN`)
**Executed:** launched 2026-08-18 21:40 UTC on 4× RTX 4090, RunPod. Longest shard
**6.75 h** (the other three 5.80–5.81 h), from the shard summaries. Observed complete at
05:24, so roughly an hour of pod time was idle after the run finished.
**Code:** `499ebbc` (the F-020 fix below post-dates the run and was not in it)
**Chains:** 25 of 25 complete, 0 failed
**Certification:** every chain `valid_with_limitation` (`validate_run.py` exit 2)

## Status of the primary contrast: NOT ESTABLISHED

`--check-only` exits 1. Realised lifetime human spend is not matched:

```
spending arms: 674,193 to 749,995 against a 750,000 ceiling
10.1070% spread, 0.2000% permitted
joint consumed 674,193 at every seed — 75,807 short
```

`PROTOCOL.md` §4 makes equal spend the fairness condition, and it does not hold.
`joint` received **10.1% less human data** than the arm it is contrasted against.
`CLAIMS.md` C-002's contract is therefore unmet by this run, and no statement about
the joint-versus-baseline comparison follows from it. Cause and fix: `FAILURE_LOG.md`
F-020.

This is not a null result and must not be reported as one. It is an invalid contrast.

## What the run does establish: between-chain variance

This was the pilot's stated purpose — `COMPUTE.md`'s compute gate blocks the powered
experiment until pilot variance is known — and it is unaffected by the spend gap,
because it is measured *within* arms.

Primary outcome: area under the generation-wise held-out human NLL regret curve,
regret defined against each chain's own generation-0 value, integrated by trapezoid
over ten generations.

| arm | AUC regret (mean) | between-chain SD | CV | realised spend |
|---|---|---|---|---|
| `no_rescue` | 2.63738 | 0.01760 | 0.67% | 0 |
| `random` | 2.52454 | 0.02055 | 0.81% | 749,869 |
| `schedule_only` | 2.54581 | 0.02757 | 1.08% | 749,878 |
| `selection_only` | 2.31320 | 0.01126 | 0.49% | 749,827 |
| `joint` | 2.32163 | 0.00949 | 0.41% | **674,193** |

Between-chain variation is **far smaller than anticipated**: coefficients of variation
between 0.41% and 1.08%, against a practical effect threshold of 2%. The paired
`joint`-minus-`selection_only` difference has an SD of 0.00880 across five seeds,
against a 2% threshold of 0.04626 in the same units.

**Implication for sizing.** At this variance, five paired chains already give roughly
80% power to detect a 2% relative effect; detecting 0.5% would take about five. The
constraint on a powered study is therefore *not* chain count. `COMPUTE.md`'s gate can
be released on this evidence, with the caveat below.

**Caveat.** `joint`'s variance is measured on chains that spent 10% less than
intended. The four other arms spent as designed and their variance is clean. Whether
a correctly-spending `joint` has comparable variance is not established here.

## Secondary outcome

Final-generation `tail_retention`, mean across five seeds:

| arm | tail_retention | SD |
|---|---|---|
| `no_rescue` | 0.8686 | 0.0021 |
| `random` | 0.8765 | 0.0015 |
| `schedule_only` | 0.8829 | 0.0017 |
| `selection_only` | 0.9015 | 0.0021 |
| `joint` | 0.8916 | 0.0015 |

## Secondary analysis: the twenty budget-matched chains

`joint` is the only arm that failed budget matching. Excluding it, the remaining 20
chains satisfy the constraint:

```
spending arms: 749,709 to 749,995 against a 750,000 ceiling
0.0381% spread, 0.2000% permitted -> budget matching: HOLDS
```

So contrasts among `random`, `schedule_only`, `selection_only` and the `no_rescue`
control are budget-matched and interpretable. Paired by seed, 5 seeds, 95% CI from a
paired *t* with 4 degrees of freedom. Lower AUC regret means less degradation. The 2%
practical threshold is 0.05049 in these units.

| contrast | difference | 95% CI | relative | distinguishable from zero |
|---|---|---|---|---|
| `selection_only` − `random` | −0.21133 | [−0.23472, −0.18794] | −8.37% | yes |
| `schedule_only` − `random` | +0.02127 | [−0.01563, +0.05818] | +0.84% | **no** |
| `random` − `no_rescue` | −0.11284 | [−0.12925, −0.09643] | −4.28% | yes |
| `selection_only` − `schedule_only` | −0.23261 | [−0.26330, −0.20191] | −9.14% | yes |

Read together: at this budget and horizon, *which* examples are selected moves the
outcome substantially, and *when* the budget is spent does not — the timing contrast's
interval contains zero and lies entirely inside the practical equivalence region.
Spending the budget at all beats spending none.

### These are secondary results and cannot carry the paper

`PREREGISTRATION.md` is explicit:

> There is one central budget, horizon, primary outcome, and primary contrast. Other
> budgets, horizons, outcomes, and comparisons are secondary or exploratory. They
> cannot replace a failed primary analysis.

The primary contrast requires `joint` and is not established. Promoting any row above
into the confirmatory result would be exactly the substitution the preregistration was
written to prevent. They may be reported as secondary, alongside the primary reported
as not established.

### Further limits on the secondary rows

- One budget (750,000), one horizon (10), one corpus and one model. Nothing here
  speaks to other operating points.
- Five seeds. Adequate given the measured variance, but the seeds were frozen for a
  different contrast.
- The `selection_only` advantage is measured against `random` selection, not against a
  strong alternative selection rule.
- No oracle upper bound exists (`PROTOCOL.md` names six treatment families; the sixth
  is deliberately unimplemented), so the size of the remaining headroom is unknown.

## Observations that are not claims

Recorded because they are in the artifacts and someone will compute them anyway. None
of these are results; the contrast that would make them results is invalid.

- Every spending arm ends below the control on both outcomes. Degradation under
  recursive training reproduces at all five seeds — generation-0 NLL 3.178–3.180
  rising to 3.642–3.659 with no rescue.
- `selection_only` has the lowest AUC regret of any arm. It spent its budget as
  designed.
- `joint` sits within 0.36% of `selection_only` on AUC regret while having spent 10.1%
  less. That is a difference in *both* strategy and data quantity, and the two cannot
  be separated from this run. It is a reason to re-run, not a finding.

## Reproduction

Artifacts: `results/runs/primary_pilot_2026-08-18/`, 25 `chain_result.json` and 25
`run_manifest.json`, plus four shard summaries and the aggregate. Checkpoints were
pruned on the pod after each chain completed; they are regenerable from the frozen
config and seeds.

To repeat the analysis in this document, read the chain results directly — the AUC
figures above are computed from `metrics[].human_nll` and nothing else.

## What must happen before the contrast can be claimed

1. F-020's fix (`policies/terminal.py`, committed after this run) must be in the code.
2. The grid must be re-run. 6.75 hours on 4× RTX 4090, the longest shard's measured
   wall time.
3. `--check-only` must exit 0 before any comparison is read.

Re-running was not possible in this session: the measured cost of the grid exceeded
the remaining budget.
