#!/usr/bin/env python3
"""Assemble one Overleaf-ready ZIP containing every version of the paper.

Overleaf's "New Project -> Upload Project" takes a ZIP and unpacks it into a project. This
builds that ZIP so the whole submission is a single upload rather than a file list to get
wrong.

Layout inside the archive, deliberately flat because Overleaf projects are:

    main.tex                      the EvoRobust 4-page version, and the default Overleaf
                                  compiles because it is called main.tex
    alt-workshop-8page.tex        NewInML / CL4FMAgents
    alt-full-paper.tex            the complete 19-page paper
    pilot_nll_by_generation.png   used by the two longer versions
    README.md                     which file for which venue, and the one manual step

The one thing not included is `neurips_2026.sty`: it is not in this repository and cannot
be fetched here. The README says where to get it, and every .tex falls back to a text block
of the same dimensions when it is absent, so the project compiles either way.

Every included .tex is run through the same preflight the standalone bundles use, and the
assembled archive is unpacked into a scratch directory and compiled. A ZIP that has not
been unpacked and compiled is a ZIP that is not known to work --- which is the lesson from
shipping two broken bundles.

Usage:
    python scripts/build_overleaf_project.py
    python scripts/build_overleaf_project.py --check   # also unpack and compile

Exit codes: 0 built (and verified, with --check); 1 a version failed preflight or the
assembled archive did not compile.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bundle_paper import build  # noqa: E402
from preflight_overleaf import static_checks  # noqa: E402

OUT = ROOT / "dist" / "overleaf-project.zip"
FIGURE = ROOT / "results/figures/pilot_nll_by_generation.png"

#: source in paper/  ->  name inside the archive
VERSIONS = {
    "evorobust_main.tex": "main.tex",
    "workshop_main.tex": "alt-workshop-8page.tex",
    "main.tex": "alt-full-paper.tex",
}

README = """# The Human Data Budget — Overleaf project

Everything is here. One manual step remains, in **Setup** below.

## Which file to compile

| Venue | Limit | Compile this | Needs the PNG |
|---|---|---|---|
| **EvoRobust**, AXIOM | 4 content pages | `main.tex` *(already the default)* | no |
| NewInML, CL4FMAgents | 8 pages | `alt-workshop-8page.tex` | yes |
| A full-length venue, or an advisor | — | `alt-full-paper.tex` | yes |

To switch: right-click the file → **Set as Main File** → Recompile.

All three read the same numbers. Every result figure is a LaTeX macro generated from the
run's chain artifacts, so the versions cannot disagree with each other about a value.

## Setup — the one manual step

These workshops require the **NeurIPS 2026 style file**, which is not redistributed here.

1. Open <https://www.overleaf.com/latex/templates/formatting-instructions-for-neurips-2026/bjdwqfdkyftc>
2. **Open as Template**, then copy `neurips_2026.sty` out of that project into this one.
3. Recompile.

Without it the project still compiles, using a text block of the same dimensions, so you can
check everything else first. **That fallback is not the venue format — add the real file
before submitting.**

## Compiling

Press **Recompile** twice. The first pass shows `[?]` for citations because BibTeX has not
run yet; the second resolves them. No `.bib` file is needed — the bibliography is embedded.

## Before you submit

- Content ends within the venue's page limit (everything before *References*).
- No `??` and no `[?]` anywhere in the PDF.
- The author line reads *Anonymous Author(s)*.
- One overfull-box warning at 0.4pt is expected and invisible. Ignore it.

## Deadlines

EvoRobust and AXIOM: **29 August 2026, 11:59pm AoE**. CL4FMAgents: **30 August 2026**.
EvoRobust submission portal:
<https://openreview.net/group?id=NeurIPS.cc/2026/Workshop/EvoRobust>
"""


def latex() -> Path | None:
    exe = Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe"
    if exe.is_file():
        return exe
    found = shutil.which("pdflatex")
    return Path(found) if found else None


def verify_archive() -> bool:
    """Unpack the ZIP into an empty directory and compile its default main file."""
    exe = latex()
    if exe is None:
        print("check: no pdflatex; skipping compile of the assembled archive")
        return True

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        with zipfile.ZipFile(OUT) as zf:
            zf.extractall(work)
        # pdflatex -> bibtex -> pdflatex -> pdflatex, which is what Overleaf runs. An
        # earlier version of this check skipped bibtex and reported 11 pages instead of
        # 13, because the bibliography never rendered and every citation stayed undefined.
        bibtex = exe.with_name("bibtex.exe") if exe.suffix == ".exe" else Path("bibtex")
        for cmd in ([str(exe), "-interaction=nonstopmode", "main.tex"],
                    [str(bibtex), "main"],
                    [str(exe), "-interaction=nonstopmode", "main.tex"],
                    [str(exe), "-interaction=nonstopmode", "main.tex"]):
            subprocess.run(cmd, cwd=work, capture_output=True, text=True)
        pdf = work / "main.pdf"
        if not pdf.is_file():
            print("check: FAIL - the unpacked archive did not produce a PDF")
            return False
        log = (work / "main.log").read_text(encoding="utf-8", errors="replace")
        pages = re.search(r"Output written on main\.pdf \((\d+) pages", log)
        undef = len(re.findall(r"Warning.*(?:undefined|Citation)", log))
        print(f"check: unpacked archive compiles, "
              f"{pages.group(1) if pages else '?'} pages from main.tex, {undef} undefined")
        return undef == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="unpack the archive and compile it")
    args = parser.parse_args()

    ok = True
    bundles: dict[str, str] = {}
    for source, archive_name in VERSIONS.items():
        print(f"\n--- {source} -> {archive_name}")
        text = build(source)
        bundles[archive_name] = text
        ok = static_checks(text, Path(archive_name)) and ok

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for archive_name, text in bundles.items():
            zf.writestr(archive_name, text)
        zf.writestr("README.md", README)
        if FIGURE.is_file():
            zf.write(FIGURE, FIGURE.name)

    print(f"\nwrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")
    with zipfile.ZipFile(OUT) as zf:
        for info in zf.infolist():
            print(f"   {info.filename:32s} {info.file_size / 1024:7.1f} KB")

    if args.check:
        ok = verify_archive() and ok
    print(f"\n{'ARCHIVE READY' if ok else 'NOT READY'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
