# Message to mentors — copy from the line below

---

Hi Laryn, Charlotte,

The pilot grid finished and I'd like your sign-off before we submit to a NeurIPS workshop.
**Deadline is 29 August**, so I'm asking early rather than politely.

**Short version: the experiment worked and the hypothesis did not.** That's the result, and
I'd rather you hear it from me than find it in the paper.

## What we ran

25 recursive chains — 5 allocation policies × 5 frozen seeds, horizon 10, GPT-2 on
WikiText-103. Every chain completed; none certifies invalid. Roughly $18 of GPU time.

The design gives each chain a fixed lifetime budget of human-origin training tokens and
asks **when** in the chain to spend it and **which** under-covered parts of the
distribution to target. Four policies vary those axes; one control spends nothing.

The thing that makes it a fair test: every policy consumes the **same total optimizer
tokens** (identical to the token, by construction) and the same lifetime human budget
(0.038% spread). Human examples *displace* synthetic ones rather than being added, so no
arm trains on more data than another.

## What we found

**The preregistered primary contrast is a null.** Combining time-and-mode adaptation does
not beat mode-targeting alone: +0.0103, 95% CI [−0.0092, +0.0297]. The interval sits
*entirely inside* the ±2% practical-equivalence region we froze before opening outcomes —
so this is equivalence, not "we couldn't tell". The design is powered to that threshold at
three chains per arm and we ran five.

The secondary contrasts say where the effect actually is:

- spending human data at all: **−4.04%** vs a control on identical data volume
- targeting under-covered modes: a further **−9.59%**
- scheduling when to spend: **−0.41%**, interval containing zero

So: *which* data you buy matters, *when* you buy it doesn't, and doing both is the same as
doing the second. One wrinkle we report rather than hide — the confirmatory tail-retention
metric *does* detect a small timing effect, so the timing claim is always stated as
"on the primary outcome".

## What I need from you

**1. Is a null the right thing to lead with?** We think yes, and the paper leads with it
before the secondary effects, which are larger and more tempting. Tell us if that's wrong.

**2. A statistics read — this is the big one.** The headline is an *equivalence*, and
equivalences lean on the practical-effect threshold much harder than a positive result
would. Our 2% bar was frozen before outcomes and checked against measured anchors, but
**nobody outside the project has ever reviewed it.** If a reviewer attacks one thing, it's
this. The verdict is unchanged under the alternative denominator, and both are in the
paper.

**3. Decisions P-001 through P-012.** All accepted by me as owner, none team-ratified.
Three sit in others' CODEOWNERS areas. `DECISIONS.md` says exactly that rather than
implying agreement, but they should have real eyes on them — P-011 especially, which
changed what the experiment measures.

**4. Venue.** We're targeting EvoRobust (4 pages, 29 Aug). I'll flag honestly that our own
assessment says **AXIOM is the better topical fit** — it's explicitly about efficiency
under constraints, same deadline, same page limit. EvoRobust is about diversity-driven
search for robustness, which is adjacent but not the same question. Happy to be overruled
either way, but you should know we didn't pick it because it fits best.

**5. Someone to sign the validity certificate**, who didn't run the experiment. All the
mechanical evidence is pre-gathered at `results/certificates/`; what's left is judgement
and a signature.

## Where to look

Repo: https://github.com/guptaneil1/algoverse-summer-26 — branch `stage-a/env-freeze`,
tagged `results-freeze-2026-08-20`.

| If you have | Read |
|---|---|
| 5 minutes | `docs/HANDOVER_2026-08-20.md` |
| 20 minutes | the paper PDF, plus `docs/runs/primary_pilot_v2_2026-08-20_results.md` |
| you want to attack it | `FAILURE_LOG.md` F-020 → F-028 |

Everything reproduces from a clone. `python scripts/reproduce_pilot_table.py` recomputes
every published number from the raw chain files using arithmetic written separately from
the code that generated them — one command, no GPU, about a second. **If you run only one
thing, run that**; it also closes a checklist item that needs a non-author.

## Things I'd rather you hear from me

- **An earlier run of this grid was invalid and we threw it out.** It failed its own
  fairness check on both axes. Both failures are written up (F-020, F-021) and its
  artifacts are still in the repo rather than deleted.
- **20 of 31 citations are individually verified** against primary sources. One was wrong —
  a workshop misnamed — and is fixed. Eleven are canonical and not yet opened.
- **Three of seven predeclared comparators were never implemented**, including an oracle
  upper bound. That means our equivalence says nothing about how far either policy is from
  what's achievable, and the paper says so wherever the null appears.
- **We can't tell whether the joint policy actually behaved differently** from the
  targeting-only one, because the per-generation allocation records weren't archived before
  the compute was released (F-028). It's a real gap and it's in the limitations.

Thanks both — happy to walk through any of it live.

Ronit
