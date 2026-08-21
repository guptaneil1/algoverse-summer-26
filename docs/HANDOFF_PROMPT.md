# Handoff prompt — paste this into a new chat

Copy everything below the line.

---

I'm continuing the Human Data Budget research project at
`C:\Users\sanji\Downloads\algoverse-summer-26`, branch `stage-a/env-freeze`.
**Read `docs/HANDOVER_2026-08-20.md` and `FAILURE_LOG.md` entries F-020 through F-028
first** — they carry the full state and I don't want it re-derived.

**Verify the repo state yourself before trusting anything below**, since I can't:

```
git status -sb ; git status --short ; git log --oneline origin/stage-a/env-freeze..HEAD
```

As of the last session: working tree clean, nothing unpushed, HEAD `5523afe`, tags
`results-freeze-2026-08-20` and `pilot-2026-08-18` on the remote
(`github.com/guptaneil1/algoverse-summer-26`). The branch is ~66 commits ahead of `main`
with **no PR open**; `docs/PR_DESCRIPTION_stage-a-env-freeze.md` is written if I want one.

## What the project is

Recursive-training / model-collapse study. Under a *fixed lifetime budget* of human-origin
optimizer tokens, does it matter **when** you spend them and **which** under-covered modes
you target? Five budget-matched arms — `no_rescue` (control), `random`, `schedule_only`,
`selection_only`, `joint` — crossed with 5 frozen seeds, horizon 10, GPT-2 on WikiText-103.
Complete recursive chains are the experimental unit.

## The result — the experiment is finished

The corrected grid completed 2026-08-20: **25 of 25 chains, zero failures, 25
`valid_with_limitation`, 0 `invalid`.** Both axes of `PROTOCOL.md` §4 hold — human spread
**0.0381%** against 0.2000% permitted, and total optimizer tokens **identical at 16,678,912
in every chain of every arm** — because rescued human examples displace synthetic records
rather than being appended (`DECISIONS.md` P-011). Artifacts:
`results/runs/primary_pilot_v2_2026-08-20/`.

**The preregistered primary contrast is a null.** joint − `selection_only` = **+0.0103,
95% CI [−0.0092, +0.0297]**, +0.45% relative, against an equivalence region of ±0.0507. The
interval lies *wholly inside* that region — equivalence at the preregistered threshold, not
insufficient power. `CLAIMS.md` C-002 is **tested and not supported**. It is *not* evidence
joint is worse: the interval covers zero.

**Secondary contrasts, all admissible:** spending at all −4.04%; targeting under-covered
modes a further −9.59%; scheduling −0.41% with an interval containing zero. Which modes you
target matters, when you spend does not — **on the primary outcome**. The confirmatory
tail-retention outcome detects a small timing effect, and
`docs/evidence/claim_evidence_matrix.md` makes reporting that alongside any timing claim a
mandatory pairing.

Record: `docs/runs/primary_pilot_v2_2026-08-20_results.md`.

## Papers — three versions, one archive

All three read the same generated macros, so they cannot disagree about a number.

| Source | Content pages | Venue |
|---|---|---|
| `paper/evorobust_main.tex` | 4 | EvoRobust, AXIOM |
| `paper/workshop_main.tex` | 6 | NewInML, CL4FMAgents (8pp limit) |
| `paper/main.tex` | ~12.5 | full version, 19pp total |

`python scripts/build_overleaf_project.py --check` builds `dist/overleaf-project.zip` —
one Overleaf "Upload Project" containing all three plus the figure and a README — and
verifies it by unpacking into an empty directory and compiling. `scripts/preflight_overleaf.py`
checks a single bundle against Overleaf conditions (three compile scenarios, static checks).
`tests/analysis/test_overleaf_bundles.py` gates all of it.

**MiKTeX is installed**, so the papers can be compiled locally. `neurips_2026.sty` is *not*
in the repo; every version falls back to a same-dimension text block without it.

## Target venues and deadlines

| Workshop | Pages | Deadline | Fit |
|---|---|---|---|
| **EvoRobust** (my choice) | 4 incl. figures | **29 Aug 2026 AoE** | weak — I was told, I chose it anyway |
| AXIOM | 4 | 29 Aug 2026 | strong |
| CL4FMAgents | 8 / 4 | 30 Aug 2026 | moderate |
| NewInML | 2–8, non-archival | see CFP | strong by eligibility |

Assessment and evidence: `docs/WORKSHOP_SUBMISSION_GUIDE.md`. Upload steps:
`docs/OVERLEAF_TUTORIAL_EVOROBUST.md`.

## What is left

Nothing blocks on code. Everything remaining needs a person:

- **Mentor approval.** `docs/MENTOR_REVIEW_REQUEST.md` is a ready-to-send message to Laryn
  and Charlotte naming five decisions that need someone other than me.
- **Statistics review** of the 2% practical-effect threshold. The headline is an
  equivalence, which leans on that threshold far harder than a positive result would, and
  it has never been reviewed outside the project. **This is the paper's main attack
  surface.**
- **11 of 31 citations** not yet individually verified (20 are, all exact; one defect found
  and fixed). Remaining: Kang, Ye, RegMix, DSIR, and seven long-established ML papers.
- **Validity certificate** — evidence pre-gathered at `results/certificates/`, deliberately
  unsigned because it was assembled by the run operator.
- **Independent reproduction** — I ran `scripts/reproduce_pilot_table.py` myself
  (logged in `results/certificates/reproduction_log.md`); it wants someone with no stake.
- External novelty review, uninvolved-reader review, mock-review scores.

## Constraints

- Budget is gone. The grid cost ~$18 of ~$25. **The pod is terminated; there is no GPU
  access.** Say so if a suggestion costs money, and ask before spending any.
- **No invented numbers.** Every result figure comes from `paper/tables/pilot_macros.tex`,
  generated by `scripts/generate_pilot_outputs.py`. A bare decimal in a paper section is a
  test failure, deliberately.
- `FAILURE_LOG.md` is **append-only**.
- Banned words: "first", "optimal", "prevents collapse", "solves", "state of the art",
  unqualified "novel".
- `primary_no_rescue.json` and `primary_fresh_random.json` stay `AWAITING_JULY_31_FREEZE`.
- **Never push to `main`.** Branch and PR.
- **Heredocs eat backslash escapes here.** Use Write/Edit for anything containing them —
  this has now broken a shim, a LaTeX file, a regex, and four edit scripts.
- **`git add -A` has swept in unwanted directories.** Stage explicitly.
- Validator exit codes are **0 valid / 1 limited / 2 invalid / 3 usage** (F-024, F-024a).
  `run_pilot --check-only` is a *different* tool with only 0 and 1.
- **Wall time for a phased grid is the sum of per-launch maxima**, not the max over shard
  summaries (F-026a).
- **`dist/` is gitignored and transient.** Do not write tests that read from it — one did,
  and failed the moment it was cleaned.
- Run tests with the venv active: several shell out to bare `python` and pick up the
  system interpreter otherwise, producing a failure and 58 collection errors that say
  nothing about the repo.

## Project skills

`.claude/skills/` has five I built for this: `paper-house-rules`, `paper-polish`,
`latex-build`, `claim-licence`, `cite-check`. `.claude/agents/` has `evidence-auditor`,
`novelty-adversary` and `stats-referee`, which are unused because of the standing
instruction below.

## Standing instruction

Make the decisions yourself rather than asking me — the team is not supplying reviews and I
am not technical enough to arbitrate. Judge every call by what makes the paper strongest,
keep it consistent with the repo, and make sure each decision has supporting evidence.
Record provenance honestly, including when a decision is yours, unvalidated, or in another
owner's CODEOWNERS area. The only thing to ask me about is spending money on compute. If
something needs a person to run a command or push, say so and I'll do it.

## Open judgement calls the last session made

- **The 2% threshold's denominator** had three conventions in the repo; the code now uses
  the one both U-006 documents use (the fresh-random mean). That is a threshold definition
  touched *after* outcomes opened, which U-006 exists to constrain. The verdict is identical
  under either convention and both are emitted as macros. F-026a has the note.
- **P-012's phase ordering** was the assistant's, not mine — scheduling only, no scientific
  content, and the run reached the last phase so it left no trace in the design.

## State

**849 tests pass, 0 fail.** Ruff and repository audit clean. Papers build with 0 undefined
references and 0 errors. Decisions P-001–P-012 accepted by me as owner, not team-ratified;
all six U-items closed.
