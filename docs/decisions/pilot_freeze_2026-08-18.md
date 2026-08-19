# Pilot freeze — U-001 through U-006

**Date:** 2026-08-18
**Made by:** this working session, at the project owner's direction, after confirming no
decision had been recorded on `origin/main`.
**Status: ACCEPTED BY THE PROJECT OWNER 2026-08-19, NOT TEAM-RATIFIED.** `DECISIONS.md` assigns no owner to U-001
through U-007; `docs/SUBMISSION_CHECKLIST.md` Gate C infers owners from directory ownership
and says to confirm each with the person named. That confirmation has not happened. Every
decision below records the evidence it rests on and what would reverse it.

Nothing here is a scientific result. These are design choices that had to be made before any
primary chain could run at all.

## U-001 — training regime: continued fine-tuning or from base?

**Decision: retrain from the pretrained base at every generation, matching upstream.**

**Evidence.** All 11 generations of both Stage A arms invoke
`--model_name_or_path openai-community/gpt2`. The previous checkpoint appears only as
`generate.py --model_path`, producing that generation's corpus. No generation resumes
optimization from the previous generation's weights. Recorded in `COMPUTE.md` and
`docs/evidence/stage_b_freeze_evidence.md`.

**Why this way.** The positive control validated a pipeline in this regime. Choosing
continued fine-tuning would mean the reproduction no longer covers the pilot's training path,
and the pilot would carry an unvalidated component into its primary claim. It also keeps
`--prune-models` sound, since a checkpoint is spent once the next generation's data exists.

**Reverses if** the team decides the research question is specifically about weight-space
drift rather than distribution drift, in which case the positive control must be re-run in
the new regime before it covers the pilot.

## U-002 — domain and corpus scale

**Decision: WikiText-103, subsampled to the first 400 `base_train` articles in frozen
manifest order (~3,004 blocks of 512 tokens).**

**Evidence.** `docs/evidence/domain_audit.md` already recommends WikiText-103; the frozen
manifests are built from it at pinned revision `b08601e04326c79dfdd32d625aee71d232d685c3`.
The subsample size is derived from two measurements, not chosen:

- The screening run resolved 200 articles into 1,502 blocks — 7.51 blocks per article.
- Stage A on one RTX 4090 cost ~247 s per generation-step at 4,669 blocks.

| Articles | Blocks | s/step | Chain-hours | Cost at \$0.74/h |
|---:|---:|---:|---:|---:|
| 300 | 2,253 | 119 | 9.9 | \$7.35 |
| **400** | **3,004** | **159** | **13.2** | **\$9.80** |
| 600 | 4,506 | 238 | 19.9 | \$14.70 |
| 622 | 4,671 | 247 | 20.6 | \$15.24 |

for 6 policies × 5 paired seeds × 10 generations = 300 generation-steps.

**Why 400, against a \$20 ceiling.** \$9.80 leaves room for one complete second attempt.
The screening run surfaced eight defects before completing; a design that assumes zero
reruns would be the wrong lesson to draw from it. 600 articles would match WikiText-2's
4,669 blocks — the scale the pipeline was validated at — but at \$14.70 a single failed
attempt exceeds the budget, and that scale-matching is a nicety rather than a requirement:
the screening run executed correctly at 1,502 blocks.

**Why the corpus is the right thing to shrink.** The alternatives are worse. Cutting seeds
from five weakens uncertainty estimates, which are computed across chains and are the
statistical basis of the whole comparison. Cutting policies drops treatment families
`PROTOCOL.md` §4 names. Shrinking the corpus costs signal strength, which is a limitation
that can be stated plainly in the paper without invalidating the design.

**Why not the full corpus.** `COMPUTE.md` assumption A7 warns that a full-corpus pilot is
"low by more than an order of magnitude". At the measured rate that is roughly \$675 —
about 29× the entire remaining budget. Subsampling is not a preference here; it is the only
option that exists.

**Reverses if** funding changes, or if the team judges a 600-article corpus too small to
carry the claim — in which case the claim must narrow rather than the corpus grow.

## U-003 — lifetime and total token budgets

**Decision, all in optimizer tokens under the frozen GPT-2 tokenizer (P-002):**

| Quantity | Value | Derivation |
|---|---:|---|
| One epoch of the base corpus | 1,538,048 | 3,004 blocks × 512 |
| `per_generation_human_budget` | 75,000 | ~5% of one epoch |
| `lifetime_human_budget` | 750,000 | 10 × base, mirroring the frozen 100/10 ratio |
| Maximum generation spend | 150,000 | 2 × base, mirroring the frozen 20/10 ratio |
| `total_optimizer_tokens` | 16,100,000 | 10 epochs + lifetime human budget |

**Evidence.** The ratios are not invented: `docs/method/week2_method_freeze.md` fixes
lifetime 100, base spend 10, maximum spend 20 over horizon 10. Those are fixture units; the
structure (base = 1/10 of lifetime, max = 2× base) is preserved and rescaled to real tokens.

**Feasibility, checked.** The rescue partition holds 17,289,136 optimizer tokens across
4,235 candidates, averaging 4,082 each. A lifetime budget of 750,000 is 4.3% of what is
available, and 75,000 per generation buys roughly 18 examples — enough granularity for a
selection policy to differ from a random one, though thinner than the ~28 a larger corpus
would have afforded.

**Reverses if** the pilot shows the budget is too small for any policy to separate from
another, which would be a power problem rather than an allocation finding and must be
reported as such.

## U-005 — final contribution type

**Decision: a design-and-validation contribution. No primary empirical claim.**

**Evidence.** `docs/SUBMISSION_CHECKLIST.md`, under "If the deadline arrives before Gate D":
"Ship the honest paper. A manuscript that presents a well-specified question, a validated
pipeline, a pinned positive control, and a truthful account of what was not reached is a real
contribution and is defensible."

All four of those now exist. What does not exist is a completed primary chain, and the
paper says so using template 9 verbatim.

**Reverses if** the pilot completes and validates before submission, at which point the
contribution becomes empirical and the results sections are regenerated from artifacts.

## U-006 — smallest scientifically meaningful effect

**Decision: 2% relative, the practical effect threshold already frozen in
`docs/method/week2_method_freeze.md`.**

**Evidence.** That threshold was fixed during the Week 2 method freeze, before any primary
outcome existed, and is listed among the frozen hyperparameters. U-006 asks for a quantity
that has, in effect, already been frozen under a different name.

**This is the weakest decision here, and it is flagged rather than smoothed over.**
`DECISIONS.md` names "mentor/statistics review" as the required evidence, and no such review
has occurred. Adopting the existing 2% threshold at least avoids inventing a *new* number
after seeing pipeline behaviour, which is the failure the preregistration exists to prevent.
It does not substitute for the review.

**Reverses if** a statistics review sets a different threshold. It should be obtained before
any power claim is made, and a pilot run under this threshold remains interpretable if the
threshold later moves, provided the move is recorded.

## What is still not decided

U-004b's numeric `nll_threshold_candidate`. Its input now exists — the generation-0 per-mode
validation NLL distribution from the screening run — but it should be re-derived from the
frozen pilot baseline rather than from a screening run at a different corpus scale. It is
not needed to launch; it is needed before primary outcomes are opened.
