# Workshop submission guide

Written 2026-08-20. Covers the four NeurIPS 2026 workshops under consideration, the Overleaf
procedure, and where each Algoverse checklist item actually stands.

---

## 1. The four venues, with their real rules

Fetched from each workshop's own CFP on 2026-08-20. **Verify before submitting** — CFPs change.

| Workshop | Content pages | Deadline | Topical fit |
|---|---|---|---|
| **EvoRobust** | **4** incl. figures/tables (5 camera-ready), unlimited supp. | 29 Aug 2026, 11:59pm AoE | **Weak** |
| **CL4FMAgents** | 8 regular / 4 short, excl. references | **30 Aug 2026, 11:59 UTC** | Moderate |
| **AXIOM** | 4, excl. references and appendix | 29 Aug 2026, 11:59pm UTC | **Strong** |
| **NewInML** | 2–8, excl. references | see CFP | Strong, by eligibility |

All four require the **NeurIPS 2026 workshop style file** and anonymised submission via
OpenReview.

### On fit, since it contradicts the stated preference order

**EvoRobust is the weakest match despite being first choice.** Its scope is *"Self-Evolving
Diversity-Driven Search for Robust AI Systems"* — novelty search, quality-diversity
algorithms, failure discovery, agentic safety, dynamic evaluation benchmarks. This paper is
a budgeted-allocation study whose "diversity" is tail-mode retention. The overlap is a word,
not a research question, and a scope desk-reject is the likely outcome.

**AXIOM is the strongest topical match.** *"Foundations of Efficient Deep Learning"*,
explicitly listing compute-optimal training and capability prediction **under constraints**.
"Where should a fixed lifetime budget of human data go" is precisely a constrained-efficiency
question. Cost: 4 pages.

**NewInML is the strongest practical match.** 8 pages, non-archival — so submitting there
does not burn the work for a later venue — and explicitly scoped to authors who have not yet
published at a top ML conference.

**CL4FMAgents** takes 8 pages and recursive generational retraining is adjacent to continual
learning, but the workshop centres on foundation-model *agents*, which this is not.

**Recommendation:** build the 8-page version once, submit to NewInML and/or CL4FMAgents, and
derive the 4-page cut from it for AXIOM. The 4-page version is a strict subset, so it is one
trim rather than a second paper.

---

## 2. Which file to submit

| File | Use |
|---|---|
| `dist/human-data-budget-workshop-bundled.tex` | **Workshop submission.** 6 pages of content + references + appendix. Self-contained |
| `dist/human-data-budget-paper-bundled.tex` | Full paper, 19 pages. For the record, an advisor, or a full-length venue |
| `results/figures/pilot_nll_by_generation.png` | Required by both. Not inlinable |

Both bundles were compiled in a scratch directory containing nothing but themselves and the
PNG. That is what `scripts/bundle_paper.py --check` does, and it is the only reason either is
known to work.

---

## 3. Overleaf, start to finish

### Step 1 — create the project

Overleaf → **New Project** → **Blank Project**. Name it something neutral; the project name is
not part of the PDF, but do not put author names in it if you may share the link.

### Step 2 — upload the two files

Click the **upload icon** (page with an up-arrow, top-left of the file tree) and add:

1. `human-data-budget-workshop-bundled.tex`
2. `pilot_nll_by_generation.png`

**The PNG must land in the project root**, at the same level as the `.tex` — not inside a
folder. The document calls `\includegraphics{pilot_nll_by_generation}` with no path. If you
drop it into a `figures/` folder the figure silently disappears.

Delete the default `main.tex` that Overleaf created, or you will have two candidate main
files.

### Step 3 — set the main document

Right-click `human-data-budget-workshop-bundled.tex` → **Set as Main File**. Overleaf usually
picks it automatically once the default `main.tex` is gone.

### Step 4 — add the venue style file

Download `neurips_2026.sty` from the workshop's CFP page (all four link it) and upload it to
the project root alongside the `.tex`.

**You do not have to do anything else.** The document begins:

```latex
\IfFileExists{neurips_2026.sty}{\usepackage[final]{neurips_2026}}{...fallback...}
```

so it uses the real style the moment the file exists, and falls back to a text block of the
same dimensions when it does not. The fallback is why the local page counts in this document
are meaningful, but **the fallback is not the venue format** — add the real file before
submitting.

### Step 5 — compile

Press **Recompile**. First pass shows `[?]` for every citation: that is normal, because
BibTeX has not run yet. Press **Recompile** once more and they resolve.

You need no `.bib` file. The bibliography is embedded via `filecontents`, which writes
`references.bib` into the project at compile time. If your Overleaf compiler ever objects,
upload `paper/references.bib` separately and it works either way.

### Step 6 — check the output before you submit

- **Search the PDF for `??`** — should be zero. Broken cross-references render as `??`.
- **Search for `[?]`** — should be zero after the second compile.
- **Count content pages.** Everything from the title to the start of *References* is content.
  References and appendix do not count at any of these four venues, but confirm against the
  CFP you are submitting to.
- **Look at the figure.** If it is a grey box or missing, the PNG is not in the root.

### Step 7 — anonymise for OpenReview

The bundle already says `Anonymous Submission` and contains no affiliations,
acknowledgements or repository links. Before uploading, check that:

- you have not added your name to the Overleaf project's title block;
- the PDF metadata does not carry your name (Overleaf sets `Author` from the `\author`
  field only, which is anonymous here);
- you do not write "our prior work [X]" anywhere if you later cite yourselves.

### Step 8 — cutting to 4 pages, for AXIOM or EvoRobust

The workshop version is ~6 content pages. To reach 4, in this order:

1. **Move Section 3 (Experimental design) into the appendix** — it is already mostly
   pointers. Saves roughly half a page.
2. **Cut the Section 5 limitations paragraph to three sentences**, keeping the missing
   comparators, the unarchived allocation trace and the unreviewed threshold. Do not cut
   these; they are what makes the null defensible.
3. **Drop Figure 2** (the NLL trajectories) and keep Table 1. The table carries the result;
   the figure illustrates it.
4. **Compress the contributions list** from four items to two sentences.

Do not cut: the equivalence-region statement, the "not evidence that joint is worse"
sentence, or the confirmatory-outcome disagreement. Each exists because removing it makes a
true sentence imply something false.

---

## 4. Algoverse checklist — honest status

Verified means checked against the artifact, not assumed.

| # | Item | Status |
|---|---|---|
| 1 | Citations real | **◐** 6 of 31 verified individually against primary sources; 1 defect found and fixed (a workshop name). 25 canonical entries unverified |
| 2 | Overview diagram | **☑** Figure 1 in the introduction; caption states the mechanism and why it makes the decision joint |
| 3 | Numbers consistent | **☑** Mechanically enforced. Every figure is a macro; a bare decimal in prose fails a test; both papers share one macro file so they cannot disagree |
| 4 | AI sanity pass | **☑** Run repeatedly. F-027 (estimand mismatch) and F-028 (unarchived allocations) came out of it |
| 5 | Claims map to evidence | **☑** `docs/evidence/claim_evidence_matrix.md`; contributions list maps item-by-item to sections; conclusion adds nothing new |
| 6 | Baselines fair | **☑** Matched on both budget axes and measured; 3 of 7 predeclared comparators unimplemented and stated wherever the null appears |
| 7 | Tables/figures self-contained | **☑** Captions carry the takeaway, direction markers (↓/↑) on the table, best value bolded — and tied arms both bolded, because bolding one would assert a difference the paper reports as absent |
| 8 | Notation consistent | **☑** The estimand mismatch (F-027) is fixed; symbols defined once |
| 9 | Anonymisation | **☑** No names, affiliations, acknowledgements or repo links |
| 10 | Venue compliance | **◐** **6 content pages**, within NewInML/CL4FMAgents' 8 and over AXIOM/EvoRobust's 4. Style file must be added by you |
| 11 | Final mechanics | **☑** 0 undefined references, 0 undefined citations, 0 errors, 1 overfull box at 0.5pt (invisible). No placeholders. Limitations present |

### The two that are not ticked, and why

**Item 1.** Six citations were opened and confirmed against primary sources: `zhu2026reflow`
(CPAL 2026, PMLR v328, pp. 314–340), `wang2026tikmix` (ACL 2026), `wang2026scpl` (ACL 2026,
pp. 33862–33882), `zhao2026regmixd` (arXiv 2606.18663), `yi2026verification`, and
`briesch2023llmoutput`. One was wrong — `yi2026verification` cited a workshop that is not the
one it appeared at — and is fixed. The remaining 25 are canonical entries (Shumailov *Nature*
2024, DoReMi, BADGE, GroupDRO, coreset, logit adjustment). The checklist asks for 100%, and
100% has not been done.

**Item 10.** Page count is satisfied for two of the four venues and not the other two; the
cut for those is in §3 Step 8. The style file cannot be added from here — it has to be
downloaded from the CFP.

---

## 5. What is genuinely still open

- **Statistics review.** The headline is an equivalence, and equivalences rest on the
  practical-effect threshold more heavily than positive findings do. That threshold has been
  checked against measured anchors and never externally reviewed. This is the single
  strongest attack surface on the paper.
- **The remaining 25 citations.**
- **The venue decision**, which determines whether the 4-page cut is needed at all.
