---
name: cite-check
description: Verify every citation resolves, every bibliography entry is used, and entries are the best available version. Use before a submission, after adding related work, or when the build reports undefined citations.
---

# Citation and bibliography check

Cheap to run, and reviewers notice every one of these. `paper/references.bib` is the single
bibliography; `main.tex` uses `\bibliographystyle{plain}`.

## 1. Every `\cite` resolves

```bash
cd /c/Users/sanji/Downloads/algoverse-summer-26 && .venv/Scripts/python.exe -c "
import re
from pathlib import Path
bib = Path('paper/references.bib').read_text(encoding='utf-8')
keys = set(re.findall(r'@\w+\{([^,]+),', bib))
cited = set()
for f in list(Path('paper/sections').glob('*.tex')) + [Path('paper/main.tex')]:
    for line in f.read_text(encoding='utf-8').splitlines():
        if line.strip().startswith('%'):
            continue
        for group in re.findall(r'\\\\cite[tp]?\*?(?:\[[^]]*\])*\{([^}]*)\}', line):
            cited.update(k.strip() for k in group.split(','))
print('bib entries :', len(keys))
print('cited keys  :', len(cited))
missing = sorted(cited - keys)
unused  = sorted(keys - cited)
print('MISSING from bib (renders as [?]):', missing or 'none')
print('in bib, never cited:', unused or 'none')
"
```

Missing keys render as `[?]` in the PDF and are unambiguous defects. Unused entries are not
errors — `plain` omits them — but an entry nobody cites is usually a related-work claim that
got cut, and worth a look.

## 2. Entry quality

For each entry, in descending order of how much a reviewer cares:

- **arXiv preprint that has since been published.** Cite the published version. This is the
  most common and most noticed defect in a related-work section, and the fix is mechanical.
- **Missing year, venue, or author list.** `plain` will render whatever is there, including
  nothing.
- **Inconsistent author formatting** across entries — `Last, First` mixed with `First Last`.
- **Duplicate entries under different keys.** Same paper cited twice looks careless and
  inflates the reference count.

## 3. The claims the citations support

A citation check is not only a formatting check. For every entry cited in
`03_related_work.tex`, confirm the sentence citing it says something the cited work actually
supports. This project has a `novelty-adversary` agent for the hostile version of that
question; this skill covers the mechanical half.

**C-004's search has a date horizon.** `docs/evidence/c004_novelty_audit_2026-08-19.md`
records it, and the repository states that a later submission must refresh it. If the
submission date has moved materially past that horizon, say so — a stale novelty search is a
finding, not a background condition.

## 4. Anonymity

`main.tex` currently carries `\author{Anonymous August 2026 Project Draft}`. For a
double-blind venue, check that no citation phrasing de-anonymises: "in our previous work
\cite{...}" identifies the authors as reliably as a name would. Use third person.

## Report

Group as: **breaks the build** (missing keys), **wrong version** (preprint over published),
**cosmetic** (formatting), **content** (citation does not support its sentence). State counts
per group. Zero missing keys is the only acceptable result for the first group.
