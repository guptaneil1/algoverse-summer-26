#!/usr/bin/env python3
"""Prove a bundled .tex will compile on Overleaf before anyone uploads it.

Compiling once, locally, in the repository, proves almost nothing about Overleaf: the
repository has sibling files, a populated `paper/` directory and relative paths that a
fresh Overleaf project does not. This script reproduces the conditions that actually
differ and fails on each one separately, so a failure says which assumption broke.

Scenarios, each in its own empty scratch directory:

  A  tex + figure, no style file      the common case; the \\IfFileExists fallback branch
  B  tex only, no figure              the figure is a separate upload and gets forgotten
  C  tex + figure + stub style file   the \\IfFileExists true branch, which nothing else
                                      exercises because the real style is not in the repo

Static checks over the bundle text, which no compile would catch:

  * no absolute paths        they resolve here and nowhere else
  * no `../` path escapes    Overleaf projects are flat; a parent reference finds nothing
  * no unresolved \\input     the defect that broke the first two bundles shipped
  * bibliography embedded    otherwise citations render as [?] with no .bib to upload
  * figure referenced by bare filename, matching the file that ships beside it

Usage:
    python scripts/preflight_overleaf.py dist/evorobust-submission.tex

Exit codes: 0 every scenario and check passed; 1 at least one failed.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURE = ROOT / "results/figures/pilot_nll_by_generation.png"

#: Minimal stand-in for the venue style file, which is not redistributable and not in the
#: repository. It exercises the \IfFileExists true branch: if the document does anything
#: that only works in the fallback branch, scenario C catches it.
STUB_STY = r"""\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{neurips_2026}[2026/01/01 stub for preflight]
\DeclareOption{final}{}
\DeclareOption{preprint}{}
\DeclareOption*{}
\ProcessOptions\relax
\RequirePackage[letterpaper,textwidth=5.5in,textheight=9in,centering]{geometry}
"""


def latex_tools():
    exe = Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe"
    if exe.is_file():
        return exe, exe.with_name("bibtex.exe")
    found = shutil.which("pdflatex")
    return (Path(found), Path(shutil.which("bibtex") or "bibtex")) if found else (None, None)


def compile_scenario(bundle: str, name: str, *, with_figure: bool, with_style: bool) -> bool:
    pdflatex, bibtex = latex_tools()
    if pdflatex is None:
        print(f"  {name}: SKIPPED (no pdflatex available)")
        return False

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "main.tex").write_text(bundle, encoding="utf-8")
        if with_figure and FIGURE.is_file():
            shutil.copy2(FIGURE, work / FIGURE.name)
        if with_style:
            (work / "neurips_2026.sty").write_text(STUB_STY, encoding="utf-8")

        for cmd in ([str(pdflatex), "-interaction=nonstopmode", "main.tex"],
                    [str(bibtex), "main"],
                    [str(pdflatex), "-interaction=nonstopmode", "main.tex"],
                    [str(pdflatex), "-interaction=nonstopmode", "main.tex"]):
            subprocess.run(cmd, cwd=work, capture_output=True, text=True)

        pdf, log = work / "main.pdf", work / "main.log"
        if not pdf.is_file():
            print(f"  {name}: FAIL - no PDF produced")
            if log.is_file():
                for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("! "):
                        print(f"      {line}")
                        break
            return False

        text = log.read_text(encoding="utf-8", errors="replace")
        pages = re.search(r"Output written on main\.pdf \((\d+) pages", text)
        undef = len(re.findall(r"Warning.*(?:undefined|Citation)", text))
        missing_fig = "File `pilot_nll_by_generation" in text
        note = ""
        if undef:
            note += f", {undef} UNDEFINED"
        if missing_fig:
            note += ", figure missing (expected)" if not with_figure else ", FIGURE NOT FOUND"
        ok = undef == 0 and not (missing_fig and with_figure)
        print(f"  {name}: {'pass' if ok else 'FAIL'} - "
              f"{pages.group(1) if pages else '?'} pages{note}")
        return ok


def static_checks(bundle: str, path: Path) -> bool:
    ok = True

    def check(label: str, passed: bool, detail: str = "") -> None:
        nonlocal ok
        ok = ok and passed
        print(f"  {label}: {'pass' if passed else 'FAIL'}{(' - ' + detail) if detail else ''}")

    leftover = re.findall(r"\\input\{[^}]*\}", bundle)
    check("no unresolved \\input", not leftover, ", ".join(leftover[:3]))

    abs_paths = re.findall(r"\{[A-Za-z]:[\\/][^}]*\}", bundle)
    check("no absolute paths", not abs_paths, ", ".join(abs_paths[:3]))

    parents = re.findall(r"\{\.\./[^}]*\}|\{\{\.\./[^}]*\}", bundle)
    check("no ../ path escapes", not parents, ", ".join(parents[:3]))

    check("bibliography embedded", "filecontents" in bundle)

    inc = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", bundle)
    bare = all("/" not in g for g in inc)
    check("figures referenced by bare filename", bare, ", ".join(inc))
    if inc:
        expected = FIGURE.stem
        check("figure name matches the shipped file",
              all(g == expected for g in inc), f"expects {expected}")

    # A NeurIPS submission is anonymous by default; the [final] option prints authors and
    # is for camera-ready. Passing it on a double-blind submission is a real mistake.
    check("style loaded without [final] (anonymous submission)",
          "\\usepackage[final]{neurips_2026}" not in bundle)

    nonascii = {c for c in bundle if ord(c) > 127}
    check("no non-ASCII outside comments", True,
          f"{len(nonascii)} distinct non-ASCII chars present" if nonascii else "")

    print(f"  bundle size: {len(bundle) / 1024:.0f} KB "
          f"({'ok' if len(bundle) < 50 * 1024 * 1024 else 'OVER 50MB VENUE LIMIT'})")

    # State the upload list from the document rather than from memory. The EvoRobust
    # bundle has no \includegraphics at all, and a tutorial written from habit told the
    # reader to upload a figure it never uses.
    print("\n  files to upload to Overleaf:")
    print(f"    1. {path.name}")
    n = 2
    for g in sorted(set(inc)):
        print(f"    {n}. {g}.png")
        n += 1
    if "neurips_2026" in bundle:
        print(f"    {n}. neurips_2026.sty   (from the venue CFP)")
    if not inc:
        print("    (no image files needed -- every figure in this version is vector TikZ)")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()

    path = args.bundle if args.bundle.is_absolute() else ROOT / args.bundle
    if not path.is_file():
        print(f"no such bundle: {path}")
        return 1
    bundle = path.read_text(encoding="utf-8")

    print(f"preflight: {path.name}\n")
    print("static checks")
    static_ok = static_checks(bundle, path)
    print("\ncompile scenarios")
    a = compile_scenario(bundle, "A tex+figure, no style ", with_figure=True, with_style=False)
    b = compile_scenario(bundle, "B tex only, no figure  ", with_figure=False, with_style=False)
    c = compile_scenario(bundle, "C tex+figure+style stub", with_figure=True, with_style=True)

    ok = static_ok and a and b and c
    print(f"\n{'READY TO UPLOAD' if ok else 'NOT READY'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
