# Contributions - Shreyan Ronit Mazumdar

Updated 2026-08-20, after the corrected grid completed. Supersedes the version written while
the pilot was still invalid.

**Counts are checkable.** Commits: `git shortlog -sne HEAD`. 179 of the 259 commits on
`stage-a/env-freeze` are mine - `BigRonit` (raghavram317, 101), `Ronit Mazumdar`
(childrensbusinessfair, 27), the unconfigured `Stage A <stage-a@local>` identity the run pod
committed under (40), and 11 more committed by tooling running under my direction. That is
69% of the branch. PRs: 15 opened, 15 merged, all under `BigRonit`.

---

**Led the project and built the experiment.** The chain runner, the validator, and the only
real experimental data we have are all mine - 179 commits and 15 PRs, about 69% of the
branch and the biggest share in the repo, and I paid for the compute.

### Ideas / research question
*shaped the direction, proposed the hypothesis*

Helped frame the project around a fixed lifetime human data budget, with the full recursive
chain as the thing we measure instead of individual generations. Pushed for doing the
positive control first so we weren't building on unverified numbers. Also set the rule that
budgets have to match on both axes (human tokens and total optimizer tokens). That rule is
the only reason we caught that our first pilot result was confounded instead of just
believing it - and after the fix, it's what lets us say the final result is fair rather than
hope so: human spend now matches to 0.038% across arms and total optimizer tokens are
identical to the token.

### Literature
*papers found and summarized that made it into Related Works*

Pinned the upstream model-collapse repo we build on (Drayson et al.) and audited it for
setup and domain match before we committed to it, it's the baseline everything gets measured
against. Built the source list and closest-work table that Related Works pulls from. Also
went through the NeurIPS workshops and landed on EvoRobust, which is what our timeline works
back from now. 20 of our 31 citations are individually verified against primary sources; one
was wrong (a misnamed workshop) and is fixed.

### Code
*what you wrote or fixed (name the component)*

Wrote the real recursive chain runner. Before that, train and generate were placeholder
functions with zero model calls, so we didn't actually have an experiment. Every result we
have now goes through it. Also wrote the pilot driver, the held-out evaluator, and the
three-state validator that certifies every run. Unified budget matching across the three
implementations after they drifted apart, then specified and implemented the displacement
rule that makes the control arm train on exactly the volume every spending arm does - that
change is what converts "spending helps" from a confounded observation into a claim about
where the data came from rather than how much of it there was. Own the repo infrastructure
too (CI, lint, artifact hashing, branch/PR workflow), plus the submission tooling: one
command builds the Overleaf archive for whichever venue we target and verifies it by
unpacking it into an empty directory and compiling it there, because compiling inside our
repo proves nothing about a fresh Overleaf project. 179 commits and 15 PRs, about 69% of the
branch.

### Experiments
*which runs you set up and executed*

Ran the primary grid twice. The first execution (25 chains, 4x RTX 4090) failed its own
fairness check on both axes and I discarded it rather than report it. The corrected grid ran
25 chains on 2x RTX 4090 in four seed-block phases: 5.96 hrs across launches where every
chain finished, 9.56 hrs counting two attempts that infrastructure bugs killed, about $18.
All 25 chains completed, zero failed, zero certify invalid. That's the only real
experimental data the project has, and the results section only exists because of it. Nobody
else has run Stage B at all. Also re-ran Stage A (the execution whose artifacts we kept,
matched the published table within 5%). Started on free Kaggle T4s, kept timing out, moved
everything to RunPod and got it running unattended. Paid for it myself.

### Analysis
*what you computed or interpreted from the results*

Got the between-chain variance number the whole compute gate was blocked on, and it changed
our plan - turns out five paired chains already gives ~80% power, so chain count was never
the real constraint. Then found our first pilot's primary contrast was invalid rather than
null: joint got ~10% less human data than the arm it's compared to, identically at every
seed, and the second budget axis had never been checked once in the entire project. Without
that we'd have written up a confounded result as a finding. Diagnosed both mechanisms, fixed
them, re-ran, and produced the result we actually have: a valid preregistered null, +0.0103
with a 95% interval of [-0.0092, +0.0297], sitting entirely inside the equivalence region we
froze before opening outcomes. Also located the effect in the three secondary contrasts -
spending helps 4.04%, targeting modes helps a further 9.59%, timing 0.41% with an interval
covering zero - and flagged the one disagreement between our two preregistered outcomes so
the timing claim always travels with its qualifier.

### Figures / tables
*which ones*

Built the pipeline that generates results tables straight from run data, so nothing in the
paper is typed by hand and every number traces to a real run - a bare decimal in a section
fails a test, deliberately. Made the pilot tables and the variance/power figures. The re-run
is done, so the paper figures are final rather than pending.

### Writing
*which sections you drafted*

Drafted method, experiments, results, conclusion, and abstract, basically the sections that
depend on knowing what actually ran. Three versions of the paper build from one shared set
of generated numbers, so they can't disagree with each other. Also wrote the whole evidence
trail: failure log (25 entries, 33 counting follow-ups), decision and claims ledgers, compute
ledger, status doc, runbooks, handovers. That's the stuff that makes any of this defensible
to a reviewer.

### Editing / review
*sections you substantively revised, code you reviewed*

Caught a revert that had quietly wiped 26 files of other people's work and restored all of
it. Then showed our headline finding at the time ("joint policy is degenerate") was just an
artifact of that revert, and fixed every doc repeating it as fact - we'd have submitted a
false claim otherwise. Found ten more defects in Stage B, every single one after a dry run
had already passed clean. After the run, caught that the paper defined the primary outcome
as a different quantity from the one the code actually computes, by checking the mathematics
against the function rather than trusting the prose. No reported number changed; the sentence
describing them was wrong, and a reviewer implementing our stated definition couldn't have
reproduced a single figure.

### Data / annotation
*labeling, cleaning, validation*

Built the frozen partition manifests and the hash-checked corpus assembly, which is what
stops the data drifting between arms - the comparison only means anything because of it.
Added near-duplicate overlap detection and the token ledger recompute. Every artifact from
the final grid is checksummed against a published SHA-256 ledger. The run archives are
published on the repo's releases and I verified all 101 files in the final one against that
ledger, so the data can be checked rather than taken on trust, and it no longer exists only
on my laptop.

### Coordination
*task tracking, running meetings, unblocking people*

Led the project and set the order of work. Ran the weekly audits of where we actually were
vs. the plan, sent out tasks name by name each week, and reviewed everyone's work as it came
in (plus reconciled it into main when branches conflicted). Took the entire experimentation
load myself so nobody was sitting blocked on compute. Also handled the mentor check-ins and
the workshop check-in.

### Background research
*general literature review, reading, exploration, scoping, ramp-up*

Got deep enough into the upstream codebase to work around its failure modes instead of
hand-patching them every run, that's what made unattended multi-hour runs possible at all.
Also priced out GPU providers to find one that fit the budget and still finished the grid.

### Other

Set the no-fabrication rules the repo runs on: don't write a number you didn't read off a
real command, use TODOs instead of placeholder values, log failures instead of hiding them,
failure log stays append-only. Reported the first pilot honestly as invalid and confounded
rather than dressing it up as a win - then fixed the cause and re-ran it, instead of shipping
the confounded version or quietly dropping the axis that failed. Documented the limitations
we can't fix, including one descriptive question about policy behaviour we can no longer
answer because the records that would settle it weren't archived before the compute was
released.
