# Overleaf → EvoRobust, in six steps

**Deadline: 29 August 2026, 11:59pm AoE.**
Submit at: <https://openreview.net/group?id=NeurIPS.cc/2026/Workshop/EvoRobust>

You need one file from me: **`evorobust-submission.tex`**. No `.bib`, no images.

---

### 1. Open the NeurIPS template

<https://www.overleaf.com/latex/templates/formatting-instructions-for-neurips-2026/bjdwqfdkyftc>

Click **Open as Template**. This creates a project in your account that already contains
`neurips_2026.sty` — which is why we start here rather than from a blank project. EvoRobust
requires that style file and does not host it itself.

### 2. Delete everything except `neurips_2026.sty`

In the file tree, delete `neurips_2026.tex`, `checklist.tex`, and anything else.

**Keep `neurips_2026.sty`.** That is the only thing you came for.

### 3. Upload `evorobust-submission.tex`

Upload icon (top-left, above the file tree) → **Select from your computer**.

### 4. Set it as the main file

Right-click `evorobust-submission.tex` → **Set as Main File**.

### 5. Recompile twice

The first pass shows `[?]` where citations go. That is BibTeX not having run yet, not an
error. Hit **Recompile** again and they become `[1]`, `[2]`, …

### 6. Check four things, then submit

- Content ends **by page 4** — everything before the word *References*.
- No `??` anywhere in the PDF.
- No `[?]` anywhere.
- No author name; it should read *Anonymous Author(s)*.

**Menu → Download → PDF**, then upload that at the OpenReview link above.

---

## If something breaks

| What you see | Fix |
|---|---|
| "Hello World", or the NeurIPS instructions paper | Step 2 or 4 not done. Delete the leftover `.tex`, set ours as main |
| `File 'figures/pipeline.tex' not found` | Wrong file. Use `evorobust-submission.tex` from `dist/` |
| Citations stay `[?]` after two compiles | Menu → Compiler: **pdfLaTeX**; Menu → Advanced → Bibliography: **automatic** |
| Content runs past page 4 | See below |
| Overfull hbox warnings | Ignore. There is one, at 0.4pt — invisible |

## If it is too long

I tested against a text block matching the NeurIPS dimensions, not the real style file, so
the true page count could differ slightly. If content runs past page 4, cut in this order:

1. The **Contributions** paragraph in Section 1 → one sentence.
2. The **variance sentence** at the end of Section 3.
3. The **"Both budgets are matched"** paragraph in Section 2 → two sentences.

**Never cut these**, whatever the page count says:

- the sentence saying the interval lies inside the equivalence region
- the sentence saying joint is *not* shown to be worse
- the missing-comparators limitation
- the confirmatory-outcome disagreement

Each one stops a true sentence from implying something false. A reviewer who catches that
will not trust the rest of the paper.

---

## Other versions, if you submit elsewhere too

These are non-archival workshops, so the same work may go to more than one.

| Venue | File | Also upload | Limit |
|---|---|---|---|
| EvoRobust, AXIOM | `evorobust-submission.tex` | — | 4 pages |
| NewInML, CL4FMAgents | `human-data-budget-workshop-bundled.tex` | `pilot_nll_by_generation.png` | 8 pages |

The 8-page version **does** use an image. Put the PNG in the project root, not in a folder.

`python scripts/preflight_overleaf.py <file>` prints the exact upload list for any of them,
read from the document rather than from memory.
