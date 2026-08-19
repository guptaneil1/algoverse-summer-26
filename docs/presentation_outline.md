# Presentation Outlines

**Deliverable:** `docs/weekly/WEEK_2.md`, Ronit — five- and ten-minute presentation outlines.

**Constraint:** both outlines are result-free. Every slot that would carry a number is marked
`RESULT_PENDING` and is filled only from generated artifacts, never typed by hand
(`CLAUDE.md` rule 3).

**Honesty note, updated 2026-08-19.** Stage A is reproduced and the pilot has executed. The
status slide is still not optional and still must not be softened, but what it must say has
changed: the run happened, the preregistered fairness check rejected it on both axes, and the
primary contrast is **not established**. A mentor audience will find that in the artifacts
within one question if the talk does not lead with it. Leading with it is also the strongest
move available -- see the revised slides below.

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
The pilot ran: 25 chains, 5 policies x 5 frozen seeds, horizon 10, 6.75 h on 4x RTX 4090. Every
chain completed. **The preregistered fairness check then rejected the run on both of its axes** --
one policy under-spent its human budget by 10.1%, and realised total tokens span 2.26% across arms.
The primary contrast is reported as invalid, not null. Say this in the first sentence of the slide.
*Visual:* the two-axis budget table, both rows failing.
*Speaker note:* the numbers come from `pilot_macros.tex`, generated from chain artifacts.

**5. What survives, and why it matters — 45s**
Three things. Between-chain variance is small enough that five seeds is already powered at the
preregistered threshold -- so chain count is not the constraint, which is the opposite of what the
pilot was commissioned to find out. One comparison is matched on both axes and is a null: **when**
the budget is spent does not detectably change the outcome. And the check that killed our headline
did so before anyone read the result -- we declined the secondary comparison that would have looked
better. That last point is the contribution a methods audience will actually respect.
*Visual:* three boxes -- variance, the surviving null, the declined comparison.

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
Seven defects, F-015 through F-021a, every one found *after* a passing dry run and every one
invisible to a 740-test suite. Three share a shape: a check whose intent was documented and whose
implementation did not achieve it, with no test asserting the intent. **A guard never observed to
bind is a guard whose binding is unverified.** Two limits on dry runs are now written down: they
cannot see the subprocess environment, and they cannot test budget matching for score-dependent
policies at all.
*Visual:* the seven defects, with the three sharing a shape grouped.

**9. The design change the run forced — 60s**
Adding human data to a fixed synthetic corpus makes training volume depend on how much a policy
spent -- so strategy and quantity cannot be separated, including against a control that spends
nothing. We now specify that human examples **displace** synthetic records rather than being
appended. That makes the total-token condition hold by construction. It is untested; no chain has
run under it.
*Visual:* two corpora side by side, additive vs displacement.

**10. Asks — 60s**
Specific, not vague. (1) Ratify P-001 through P-011 -- accepted by the owner, never team-reviewed,
three in others' CODEOWNERS areas. (2) An external novelty reviewer; the stop rule has been applied
internally and is not triggered, but internal is not the same as external. (3) A statistics review
of the 2% threshold, which every interval in the paper is read against. (4) Roughly $20 and one
validation chain to re-run the grid under the corrected design -- the variance data says five seeds
is already enough, so this is the cheapest empirical result available to the project.
*Visual:* four asks mapped to owners.

## Slide-count discipline

Five minutes is five slides. Ten minutes is ten. If a slide needs more than 90 seconds it is two
slides or it is cut. The status slide is never the one cut.

## Filling result slots

Results now exist. Every number on a slide is read from
`results/runs/primary_pilot_2026-08-18/` or from `paper/tables/pilot_macros.tex`, which is
generated from those artifacts by `scripts/generate_pilot_outputs.py`. Each results slide carries
the generating command in its speaker notes. No number is typed by hand into a slide, for the same
reason no number is typed by hand into the paper.

**The figure to use** is `results/figures/pilot_nll_by_generation.png`, also generated. Its caption
must carry the same qualification the paper's does: two of the five trajectories are not
budget-matched.
