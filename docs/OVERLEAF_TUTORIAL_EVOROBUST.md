# Filling an empty Overleaf project — EvoRobust submission

Start to finish, from a blank project to a submittable PDF. Roughly fifteen minutes.

**Target:** EvoRobust @ NeurIPS 2026 · **4 content pages** including figures and tables ·
references and supplementary unlimited · **deadline 29 Aug 2026, 11:59pm AoE** · NeurIPS 2026
style file required · anonymised.

---

## What you are uploading

| File | Where it comes from | Goes where |
|---|---|---|
| `evorobust-submission.tex` | `dist/evorobust-submission.tex` | project root |
| `pilot_nll_by_generation.png` | `results/figures/` | **project root**, not a folder |
| `neurips_2026.sty` | the EvoRobust CFP page | project root |

Three files. No `.bib` — the bibliography is embedded in the `.tex`.

---

## Step 1 — Create the project

Overleaf → **New Project** → **Blank Project**. Name it something that does not identify you;
reviewers will not see the name, but shared links do.

Overleaf creates a `main.tex` with placeholder content.

## Step 2 — Delete the placeholder

In the file tree, right-click Overleaf's `main.tex` → **Delete**.

Do this **before** uploading. If two `.tex` files both look like main documents, Overleaf
compiles the wrong one and you get a one-page "Hello World".

## Step 3 — Upload the submission and the figure

Click the **upload icon** (a page with an up-arrow, top-left above the file tree) → **Select
from your computer** → choose both:

- `evorobust-submission.tex`
- `pilot_nll_by_generation.png`

**The PNG must sit at the top level of the file tree**, at the same indentation as the
`.tex`. Do not create a `figures/` folder. The document calls
`\includegraphics{pilot_nll_by_generation}` with no path, and a folder makes the figure
vanish with only a warning.

> Note: the EvoRobust version does not currently place that figure in the main text — it is
> referenced from the supplementary. Upload it anyway; without it the compile emits a
> missing-file warning.

## Step 4 — Get the venue style file

Open the EvoRobust CFP page and download the **NeurIPS 2026 style file**
(`neurips_2026.sty`). Upload it to the project root the same way.

**You do not edit anything to activate it.** The document opens with:

```latex
\IfFileExists{neurips_2026.sty}{\usepackage[final]{neurips_2026}}{ ...fallback... }
```

so the real style is used the moment the file exists. Without it you get a text block of the
same dimensions — which is why the page counts quoted here are meaningful — but **the
fallback is not the venue format and must not be submitted.**

If the CFP offers an Overleaf template link instead of a file, open that template, copy
`neurips_2026.sty` out of it, and upload it here.

## Step 5 — Set the main document

Right-click `evorobust-submission.tex` → **Set as Main File**. With Overleaf's `main.tex`
deleted this is usually automatic; do it explicitly anyway.

## Step 6 — Compile twice

Press **Recompile**.

The first pass shows `[?]` where every citation should be. **This is expected** — BibTeX has
not run yet. Press **Recompile** a second time and they resolve to `[1]`, `[2]`, and so on.

If they are still `[?]` after the second pass, open the **Logs** panel (next to the
Recompile button) and look for a BibTeX error. The usual cause is Overleaf being set to
`pdfLaTeX` without automatic BibTeX; switch **Menu → Compiler** to `pdfLaTeX` and
**Menu → Advanced → Bibliography** to automatic.

## Step 7 — Check before submitting

Work through these in the compiled PDF, not in the editor.

1. **Content page count.** Everything from the title to the line *References* is content.
   EvoRobust allows **4**. It should end partway down page 4.
2. **Search the PDF for `??`.** Zero. Anything else is a broken cross-reference.
3. **Search for `[?]`.** Zero.
4. **Search for `TODO`, `PENDING`, `PLACEHOLDER`.** Zero.
5. **Table 1 renders** with bold values and the ↓/↑ direction markers in the header.
6. **Figure 1** (the pipeline diagram) renders as boxes and arrows, not a grey rectangle.
7. **No author name anywhere**, including the PDF properties (Overleaf takes them from
   `\author`, which reads `Anonymous Submission`).

## Step 8 — Submit

EvoRobust uses OpenReview. Download the PDF (**Menu → Download → PDF**) and upload it there.
Keep the Overleaf project — camera-ready may extend to 5 pages and you will want the source.

---

## If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| "File `figures/pipeline.tex' not found" | You uploaded a non-bundled `.tex` | Use `dist/evorobust-submission.tex`; it has everything inlined |
| Compile produces no PDF, "Emergency stop" | A missing input file | Read the first `!` line in the Logs. Only the first matters; the rest cascade |
| Figure is a grey box | PNG is in a folder, or missing | Move it to the project root |
| Citations stay `[?]` | BibTeX did not run | Recompile again; check Menu → Compiler settings |
| Page count too high | Style file missing, so the fallback geometry is in use | Upload `neurips_2026.sty` |
| Overleaf compiles "Hello World" | Placeholder `main.tex` still present | Delete it, then Set as Main File |

---

## If you need to cut further

The submission ends partway down page 4, so there is a little slack but not much. If the
real NeurIPS style runs longer than the fallback, cut in this order:

1. The **Contributions** paragraph in Section 1 — condense to one sentence.
2. The **variance sentence** at the end of Section 3.
3. The **"Both budgets are matched"** paragraph in Section 2 — reduce to two sentences and
   move the rest to supplementary.

**Do not cut**, in any circumstances: the equivalence-region statement, the sentence saying
joint is *not* shown to be worse, the missing-comparators limitation, or the
confirmatory-outcome disagreement. Each is there because removing it lets a true sentence
imply something false, and a reviewer who spots that will not believe the rest.

---

## One thing to weigh before you submit here

EvoRobust's scope is *"Self-Evolving Diversity-Driven Search for Robust AI Systems"* —
novelty search, quality-diversity algorithms, failure discovery, agentic safety. This paper
frames recursive training as a self-evolving system whose failure mode is diversity loss,
and asks which intervention bounds it under a fixed budget. That connection is real and the
submission makes it explicitly.

It is still a narrower fit than **AXIOM** ("Foundations of Efficient Deep Learning", which
explicitly covers compute-optimal training under constraints — the same 4-page limit and
deadline), and than **NewInML** (8 pages, non-archival, aimed at first-time authors). The
assessment and evidence are in `docs/WORKSHOP_SUBMISSION_GUIDE.md`.

Submitting to more than one is allowed: these are non-archival workshops. The 8-page version
for NewInML/CL4FMAgents is already built at
`dist/human-data-budget-workshop-bundled.tex`, and needs the same three-file upload.
