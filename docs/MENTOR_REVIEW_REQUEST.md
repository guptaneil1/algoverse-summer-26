# Message to mentors - copy from the line below

Plain ASCII on purpose. Typographic characters (em dash, U+2212 minus, multiplication sign)
do not survive a paste into most mail clients intact, and nobody types them by hand.

---

Hi Laryn, Charlotte,

The pilot grid is done and I need your sign-off before we submit. Deadline is 29 August, so
I'm asking now rather than in a week.

The experiment worked. The hypothesis didn't. I'd rather tell you that than have you find it
in the paper.

## What we ran

25 recursive chains: 5 allocation policies across 5 frozen seeds, horizon 10, GPT-2 on
WikiText-103. All 25 completed and none certifies invalid. About $18 of GPU time.

Each chain gets a fixed lifetime budget of human-origin tokens. The question is when to
spend it, and which under-covered parts of the distribution to aim at. Four policies vary
those two axes; one control spends nothing.

What makes it a fair test: every policy burns the same total optimizer tokens, identical to
the token, and the same human budget to within 0.038%. Rescued human examples displace
synthetic ones instead of being added on top, so no arm sees more data than another.

## What we found

The preregistered primary contrast came out null. Combining time and mode adaptation does
not beat mode-targeting on its own: +0.0103, 95% CI [-0.0092, +0.0297]. That interval sits
entirely inside the 2% practical-equivalence region we froze before opening outcomes, so
this is equivalence, not "we couldn't tell". We powered the design for three chains per arm
and ran five.

The secondary contrasts show where the effect actually lives:

- spending human data at all: -4.04% against a control on identical data volume
- targeting under-covered modes: another -9.59%
- choosing when to spend: -0.41%, interval covering zero

Which data you buy matters. When you buy it doesn't. Doing both comes out the same as doing
the first. One caveat we print rather than bury: the confirmatory tail-retention metric does
pick up a small timing effect, so we qualify every timing claim as "on the primary outcome".

## What I need from you

**1. Is leading with a null right?** We think so, and the paper puts it ahead of the
secondary effects, which are bigger and more tempting. Say so if that's wrong.

**2. A statistics read. This is the big one.** An equivalence result leans on the
practical-effect threshold much harder than a positive result would. Our 2% bar was frozen
before outcomes and checked against measured anchors, but nobody outside the project has
looked at it. If a reviewer goes after one thing, it's this. The verdict holds under the
alternative denominator and both are in the paper.

**3. Decisions P-001 through P-012.** I accepted all of them as owner and none is
team-ratified. Three fall in other people's CODEOWNERS areas. `DECISIONS.md` says so plainly
rather than implying agreement, but they need real eyes, P-011 most of all, since it changed
what the experiment measures.

**4. Venue.** We're aimed at EvoRobust, 4 pages, 29 August. Our own read is that AXIOM fits
better: it's explicitly about efficiency under constraints, same deadline, same page limit,
while EvoRobust is diversity-driven search for robustness, which is adjacent but not our
question. Overrule me if you like, but you should know we didn't pick on fit.

**5. Someone to sign the validity certificate** who didn't run the experiment. The
mechanical evidence is already gathered in `results/certificates/`. What's missing is
judgement and a signature.

## Where to look

Use these links rather than the repo front page. The work is on branch `stage-a/env-freeze`,
tagged `results-freeze-2026-08-20`. The default branch is 42 commits behind and still says
there's no result. It predates the run and I haven't merged it.

Branch: https://github.com/guptaneil1/algoverse-summer-26/tree/stage-a/env-freeze

- 5 minutes: `docs/HANDOVER_2026-08-20.md`
- 20 minutes: the attached PDF, plus `docs/runs/primary_pilot_v2_2026-08-20_results.md`
- if you want to attack it: `FAILURE_LOG.md`, entries F-020 through F-028

The PDF is attached because it's a build artifact we don't commit, so a clone won't have
one. The raw run artifacts are too big for the repo and hang off the release:
https://github.com/guptaneil1/algoverse-summer-26/releases/tag/results-freeze-2026-08-20 -
that's `v2_results.tar.gz`, 101 files, each matching the SHA-256 ledger in
`ARTIFACT_HASHES.json`, if you'd rather verify than trust.

Everything reproduces from a clone. `python scripts/reproduce_pilot_table.py` recomputes
every published number from the raw chain files, using arithmetic written separately from
the code that generated them. One command, no GPU, about a second. If you run one thing, run
that. It also closes a checklist item that needs someone who isn't the analysis author.

## Things you should hear from me first

- An earlier version of this grid was invalid and we threw it out. It failed its own
  fairness check on both axes. Both failures are written up as F-020 and F-021, and its
  artifacts are still in the repo rather than deleted.
- 20 of our 31 citations are individually verified against primary sources. One was wrong, a
  misnamed workshop, now fixed. The remaining eleven are canonical and I haven't opened them.
- Three of seven predeclared comparators were never implemented, including an oracle upper
  bound. So our equivalence says nothing about how far either policy sits from what's
  achievable, and the paper says that wherever the null appears.
- We can't tell whether the joint policy actually behaved differently from the
  targeting-only one. The per-generation allocation records weren't archived before we
  released the compute (F-028). That's a real gap and it's in the limitations.

Happy to walk through any of it live.

Ronit
