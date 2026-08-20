# Presentation Outlines

**Deliverable:** `docs/weekly/WEEK_2.md`, Ronit — five- and ten-minute presentation outlines.

**Constraint:** both outlines are result-free. Every slot that would carry a number is marked
`RESULT_PENDING` and is filled only from generated artifacts, never typed by hand
(`CLAUDE.md` rule 3).

**Honesty note, updated 2026-08-20.** Stage A is reproduced, the corrected grid has executed,
and both fairness axes hold. The status slide is still not optional and still must not be
softened, but what it must say has changed again: **the primary contrast is now valid, and it
is a null.** The hypothesis the project was built to test is not supported, and the interval is
tight enough to say that rather than to plead insufficient power.

Lead with the null. Do not bury it behind the secondary effects, which are large and tempting.
A mentor audience will find it in the artifacts within one question, and a talk that leads with
a null it can defend is stronger than one that looks steered toward its secondary results.

The 2026-08-19 version of this note described a run rejected by its own fairness check. That
run is superseded; its record stays in `docs/runs/primary_pilot_2026-08-18_results.md`.

## Five-minute outline (5 slides)

**1. The loop — 45s**
Models increasingly train on text earlier models produced. Controlled studies show some versions of
this loop degrade fit, diversity, and tail coverage; others remain stable. The determining factor is
the data workflow, not synthetic data per se.
*Visual:* the four-box recursive diagram from `README.md`.

**2. The question — 60s**
Human-origin data is a finite, expensive resource. Measured in optimizer-consumed tokens, spending
it three times costs three times. Given one fixed lifetime stock: **when** in the recursive chain
should it be spent, and **which** under-covered modes should it target?
*Visual:* budget grid, generations on one axis, modes on the other, `Σ b_{g,m} = B`.

**3. The design — 90s**
Four budget-matched families: random, schedule-only, selection-only, joint. Every policy consumes
identical lifetime human tokens and identical total optimizer tokens — that matching is the
fairness constraint. The experimental unit is a complete seeded chain, not a generation.
*Visual:* the four-family decomposition table.

**4. What happened — 60s**
25 chains, 5 policies x 5 frozen seeds, horizon 10, on 2x RTX 4090. Every chain completed, none
failed, none certifies invalid. **Both axes of the fairness check hold**: human spend varies by
0.04% across arms and total optimizer tokens are identical, because rescued human examples
displace synthetic records rather than being added to them. **The primary contrast is valid and
it is a null** -- joint allocation is practically equivalent to the strongest non-joint baseline,
with the interval lying inside the equivalence region rather than merely spanning zero. Say the
null in the first sentence of the slide.
*Visual:* the two-axis budget table, both rows passing, with the primary interval beneath it.
*Speaker note:* the numbers come from `pilot_macros.tex`, generated from chain artifacts.

**5. Where the effect actually is — 45s**
The null is not "nothing works". All four comparisons are matched on both axes, so all are
admissible, and together they decompose the question. Spending a human budget at all is worth
about 4% against a control trained on **identical data volume**. Targeting under-covered modes is
worth a further 9-10%. Scheduling when to spend moves the primary outcome by under half a percent,
with an interval containing zero. Adding scheduling to targeting buys nothing.

**Which** modes you spend on matters; **when** you spend does not, on the primary outcome. Say the
qualifier out loud: the confirmatory tail-retention outcome does detect a small timing effect, and
the talk reports that rather than leaving it out.

Close on what bounds it: three of seven predeclared comparators were never implemented, including
an oracle upper bound, so how much headroom remains above any of these policies is unknown.
*Visual:* four bars -- control, random, schedule, selection/joint -- with the equivalence band drawn on.

## Ten-minute outline (10 slides)

Slides 1–3 as above, expanded ~30s each, then:

**4. Why this is not already solved — 90s**
The honest version of the novelty position. Accumulation (Gerstgrasser, Kazdan) can avoid collapse
where replacement causes it. Fresh-real schedules and biased sampling (Alemohammad) combine time
and distribution. Detector resampling (Drayson) is a strong selector. Dynamic mixture methods
(RegMix-D, TikMix) allocate across training time and domain. **Each of these is a genuine threat**,
and the residual distinction is narrow: recursion, a fixed lifetime human-token stock, and matched
non-joint baselines — all three together.
*Visual:* the `closest_work.csv` matrix, threat level column highlighted.

**5. Formalization — 60s**
Horizon `G`, monitored partition into `M` modes, lifetime budget `B`, allocation `b_{g,m}` with
`Σ b_{g,m} = B`. Primary outcomes: regret AUC over the horizon, plus a frozen tail-retention
measure evaluated on a partition never used for selection.
*Note:* the joint allocation rule itself is **not yet frozen** — say so.

**6. Verification machinery — 90s**
The part most likely to impress a methods-focused mentor. Stable content hashes, five disjoint
partitions, exact optimizer-token accounting from real batches, seed propagation, checkpoint-resume
equivalence, atomic artifact writes, script-generated tables with content hashes, and a no-result
rule that blocks any number from reaching the paper before its artifact validates.
*Visual:* the six evidence gates.

**7. Positive control — 60s**
Before any novel comparison, reproduce Drayson et al. (EMNLP 2025), upstream pinned at
`feb8511479a2e2dc868e1caf3f63cb99f1fcc746`. Note the discovered hazard: upstream installs
`transformers` unpinned from Git main, so reproducing it requires pinning that ourselves.
*Visual:* Stage A acceptance criteria.

**8. What the run cost us, and what it taught — 90s**
Twelve defects, F-015 through F-026a, every one found *after* a passing dry run and every one
invisible to an 800-test suite. Four share a shape: a check whose intent was documented and whose
implementation did not achieve it, with no test asserting the intent. **A guard never observed to
bind is a guard whose binding is unverified.**

The sharper lesson is about which failures cost anything. Two were loud -- F-025 put four
processes on one GPU, F-026 made resume die on a directory upstream refuses to overwrite -- and
between them cost about 3.6 hours of pod time and no science, because both stopped chains from
starting and neither corrupted a chain that finished. The expensive ones were silent: a guard that
checked one of the two axes it named, a reconciliation that never bound, a documented exit code
inverted against its own implementation. **Loud failures are cheap. The ones that pass are not.**

Five boundaries of what a dry run can check are now enumerated rather than rediscovered one at a
time.
*Visual:* the defects split into loud/cheap and silent/expensive, not into a single list.

**9. The design change the run forced, and what it bought — 60s**
Adding human data to a fixed synthetic corpus makes training volume depend on how much a policy
spent -- so strategy and quantity cannot be separated, including against a control that spends
nothing. Human examples now **displace** synthetic records rather than being appended, which makes
the total-token condition hold by construction.

It is no longer untested: 25 chains ran under it, and realised total optimizer tokens are identical
across all five arms to the token. That is what converts "spending helps by 4%" from a confounded
observation into a statement about the *origin* of the data rather than its quantity.
*Visual:* two corpora side by side, additive vs displacement, realised totals under each.

**10. Asks — 60s**
Specific, not vague. (1) Ratify P-001 through P-012 -- accepted by the owner, never team-reviewed,
three in others' CODEOWNERS areas. (2) An external novelty reviewer; the stop rule has been applied
internally and is not triggered, but internal is not the same as external. (3) A statistics review
of the 2% threshold, which every interval in the paper is read against. (4) A read of the null by
someone who has not seen it. The result is defensible; the thing worth pressure-testing is whether
an equivalence with three comparators missing is being presented with the right confidence.
*Visual:* four asks mapped to owners.

## Slide-count discipline

Five minutes is five slides. Ten minutes is ten. If a slide needs more than 90 seconds it is two
slides or it is cut. The status slide is never the one cut.

## Filling result slots

Results now exist. Every number on a slide is read from
`results/runs/primary_pilot_v2_2026-08-20/` or from `paper/tables/pilot_macros.tex`, which is
generated from those artifacts by `scripts/generate_pilot_outputs.py`. Each results slide carries
the generating command in its speaker notes. No number is typed by hand into a slide, for the same
reason no number is typed by hand into the paper.

**The figure to use** is `results/figures/pilot_nll_by_generation.png`, also generated. Its caption
no longer needs the budget-matching qualification the 2026-08-18 version carried: all five
trajectories are matched on both axes, and the selection-only and joint lines lying on top of each
other is the primary null shown rather than stated.
