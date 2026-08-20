---
name: paper-polish
description: Minimal-edit correctness and prose pass over the manuscript. Use when the paper is substantively finished and needs to be made correct, consistent and well-written without being rewritten. Biased hard against rewriting; every change must be defensible as a fix.
---

# Paper polish — a minimal-edit pass

Load `paper-house-rules` first. This skill assumes the paper is **at a level you are trying
to preserve**, not a draft to be improved by force. The failure mode is not missing an
improvement; it is churning good prose and introducing an error into a document that
currently says only true things.

## The governing rule

> **Every edit must be defensible as a fix.** If the best justification you can give is "this
> reads better", it is not a fix and you do not make it.

An edit is a fix if it corrects a falsehood, resolves an inconsistency between two places,
removes an unlicensed claim, repairs something that would break the build, or removes an
ambiguity a reviewer could exploit. Nothing else qualifies.

**Do not restructure.** No reordering sections, no merging or splitting paragraphs, no
changing the argument. If the structure is wrong, say so and stop — that is a separate
decision with a separate cost.

## Pass order

Run these in order and do not skip ahead. Earlier passes find errors that make later
judgements moot.

### Pass 1 — Correctness against the artifacts

The only pass that can find a *wrong* paper. Everything else is cosmetic by comparison.

- Every numeric claim traces to a macro; every macro is defined and generated from the run
  named in `paper/tables/generated_provenance.json`.
- Every sentence describing the run matches `docs/runs/<run>_results.md`. Chain counts,
  certification split, spreads, intervals, wall time.
- Every claim is licensed by `docs/evidence/claim_evidence_matrix.md`. **Check the
  retirements as well as the additions** — a retired sentence that survives is the exact
  failure S20 was.
- Both mandatory pairings hold everywhere the claim appears, not just in the results section.
- Cross-references between sections agree: what §7 reports, §8 limits and §9 concludes must
  be the same result.

### Pass 2 — Internal consistency

Two places saying different things about one fact. Grep for the fact, do not read for it.

- Numbers repeated in prose and in a table or caption.
- Terminology: one name per concept throughout. `joint` vs "joint policy" vs "joint
  time-and-mode" is fine if consistent per context; drifting between them mid-paragraph is
  not.
- Tense: the run happened. Sections written before execution may still use future tense
  ("the pilot will compare"). Fix those; they read as unexecuted work.
- Hedging calibration: the null is precise and should be stated precisely. Hedged language
  around a tight interval understates the result as badly as overclaiming overstates it.

### Pass 3 — Build safety

Cannot be fully checked without a LaTeX toolchain. Check what is checkable statically:

- Every `\ref`/`\label` pairs. Every `\cite` key exists in `references.bib`.
- Math mode balanced. `%` at line end where a space would be wrong.
- Special characters escaped: `%`, `&`, `_`, `#` outside math and outside `\texttt`.
- Quotes are LaTeX quotes (`` `` `` and `''`), not `"`.
- Dashes: `---` for em, `--` for numeric ranges.

If MiKTeX is installed, build and read the log instead of guessing:

```bash
cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

### Pass 4 — Prose, minimally

Only now, and only these:

- **Sentences that could be misread.** Ambiguity is a correctness problem wearing a style
  costume. Fix.
- **Sentences that bury the finding.** A null stated in a subordinate clause is a null the
  reviewer will miss and then accuse you of hiding. Fix.
- **Dead weight**: "it is important to note that", "in order to", "the fact that". Cut, do
  not rephrase around.
- **Paragraph openings.** A reader skimming reads first sentences. If the first sentence of
  a paragraph does not carry its claim, fix that sentence and leave the rest alone.

Leave alone: word choice you would have made differently, sentence rhythm, anything whose
only defect is that you would have written it another way.

## Reporting

Do not present a diff and call it done. For every change, state: **file, what was wrong,
what it now says, and which pass caught it.** Group by pass, most severe first. If Pass 1
found nothing, say so plainly — that is the most valuable finding in the report and it
should not be buried under twelve comma fixes.

Then state explicitly what you **chose not to change and why**. That list is evidence the
pass was minimal rather than merely small.

## Stop conditions

Stop and ask rather than proceeding if:

- A correctness fix requires a number that does not exist as a macro. Adding it means
  changing the generator, which is a code change with its own review.
- The fix is to a claim's substance rather than its wording. That is `CLAIMS.md` territory
  and an owner decision.
- The structure is wrong. Say so; do not fix it silently.

## Verify before finishing

```bash
.venv/Scripts/python.exe -m pytest tests/analysis -q
.venv/Scripts/python.exe -m ruff check .
```
