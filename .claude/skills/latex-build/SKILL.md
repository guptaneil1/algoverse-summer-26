---
name: latex-build
description: Build paper/main.tex, parse the log for real errors, and report page count against the target limit. Use before claiming the paper is finished, after any section edit, or when asked how long the paper is. Requires a local TeX toolchain.
---

# Build the paper and read what the build says

The manuscript has been written for months without ever being compiled. Everything below
exists because a paper nobody has built is a paper whose length, layout and cross-references
are unknown.

## Prerequisite

```bash
winget install MiKTeX.MiKTeX
```

Then confirm: `pdflatex --version`. If it is absent, **say so and stop** — do not estimate
page count from word count and present it as a measurement. A words-per-page estimate is a
planning figure with an error bar of several pages, and this project's rule against invented
numbers applies to the paper's own metadata as much as to its results.

## Build

Two `pdflatex` passes around `bibtex`, so `\cite` and `\ref` resolve. Mirrors
`.github/workflows/paper.yml`.

```bash
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## What to report, in this order

### 1. Did it build

Exit status, and if not, the actual error with its file and line. LaTeX errors cascade —
report the **first** one, fix it, rebuild. Reporting the twelfth error wastes everyone's time.

### 2. Undefined references and citations

```bash
grep -E "Warning.*(undefined|Citation)" paper/main.log
```

Every one is a `??` or `[?]` in the PDF. There is no acceptable count other than zero.

### 3. Page count against the limit

```bash
pdfinfo paper/main.pdf | grep Pages
```

Report **body pages** (through the bibliography) separately from the appendix, because venue
limits count them differently. NeurIPS has used a 9-page main-text limit; `DECISIONS.md`
D-002 targets NeurIPS 2027, whose rules were unpublished as of 2026-08 — so state the limit
you are measuring against and where it came from rather than assuming.

**`main.tex` currently uses `\documentclass{article}` with 1-inch margins and no venue style
file.** Page count in that format is not the page count at submission. Say so every time you
report it, until a style file exists.

### 4. Overfull boxes

```bash
grep -c "Overfull" paper/main.log
```

Report the count and the worst offender. Overfull `\hbox` over ~10pt is visible as text
running into the margin. Under that, ignore it — chasing every overfull box is how a polish
pass turns into a rewrite.

### 5. Float placement

Read the PDF. A table or figure that landed pages away from its reference is a real defect a
reviewer will notice, and it is invisible in the source.

## After a successful build

The `pdf` skill can read the output — use it to check the rendered table, the figure, and
that the abstract fits where it should.

Do not commit `main.pdf`. Build artifacts stay out of the repository; CI produces the
authoritative one.

## Failure to avoid

Do not "fix" a LaTeX error by deleting the content that triggered it. An unescaped `%` that
swallows a line looks like a build fix and is a content deletion. Escape it.
