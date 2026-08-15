# Presentation Outlines

**Deliverable:** `docs/weekly/WEEK_2.md`, Ronit — five- and ten-minute presentation outlines.

**Constraint:** both outlines are result-free. Every slot that would carry a number is marked
`RESULT_PENDING` and is filled only from generated artifacts, never typed by hand
(`CLAUDE.md` rule 3).

**Honesty note for the current state:** if either talk is delivered before Stage A completes, the
status slide is not optional and must not be softened. A mentor audience will discover the absence
of results in the first question if it is not stated in the talk.

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

**4. Status — 60s**
State plainly: pipeline, policies, evaluation, and analysis are built and unit-tested; the published
positive control has not been reproduced; no experimental results exist. Name the critical path —
GPU access → positive control → pilot.
*Visual:* the critical-path chain from `docs/STATUS.md`.

**5. What we would conclude — 45s**
The design permits a null or harmful answer, and we have precommitted to reporting it. If a fixed
schedule matches joint allocation at equal cost, the adaptivity is not justified — and that is a
useful finding.
*Visual:* the four outcome templates as four boxes.

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

**8. Status and critical path — 90s**
As slide 4 of the short talk, expanded. Show the week-by-week reality: Week 1 complete, Week 2 the
live frontier, Weeks 3–4 gated rather than late. One workstream is compute-blocked; three have
available work.

**9. Outcome commitments — 60s**
Walk the four templates. Emphasize that a tight interval around zero and a wide interval are
different results and will be reported differently.

**10. Asks — 60s**
Specific, not vague: GPU allocation for Stage A; a decision on training regime, domain, and
budgets; an external reviewer for the novelty claim; and a revised timeline.
*Visual:* the four blockers mapped to the four members.

## Slide-count discipline

Five minutes is five slides. Ten minutes is ten. If a slide needs more than 90 seconds it is two
slides or it is cut. The status slide is never the one cut.

## Filling result slots

When results exist, `RESULT_PENDING` markers are replaced by values read from
`results/aggregates/`, and each results slide carries the generating command in its speaker notes.
No number is typed by hand into a slide, for the same reason no number is typed by hand into the
paper.
