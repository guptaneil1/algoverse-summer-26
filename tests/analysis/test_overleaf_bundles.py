"""The shipped bundles must stay uploadable.

Three bundles get handed to people who will paste them into an empty Overleaf project.
Two of them have already shipped broken --- once with four unresolved `\\input` directives
that killed the compile, once telling the reader to upload a figure the document never
references. Both were caught by a check, and both would have been caught earlier by this
one.

The static half runs everywhere, including CI with no TeX installed, because the defects
that actually shipped were textual: an unresolved input, a path that only resolves inside
the repository, an option that prints author names on an anonymous submission. The compile
half needs pdflatex and skips cleanly without it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLES = (
    "dist/evorobust-submission.tex",
    "dist/human-data-budget-workshop-bundled.tex",
    "dist/human-data-budget-paper-bundled.tex",
)


def _bundle(name: str) -> str:
    path = ROOT / name
    if not path.is_file():
        pytest.skip(f"{name} not built; run scripts/bundle_paper.py")
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", BUNDLES)
def test_no_unresolved_input(name: str) -> None:
    """The defect that shipped twice: a nested \\input the bundler's regex missed."""
    leftover = re.findall(r"\\input\{[^}]*\}", _bundle(name))
    assert not leftover, f"{name} would fail on Overleaf: {leftover}"


@pytest.mark.parametrize("name", BUNDLES)
def test_no_path_escapes_the_project(name: str) -> None:
    """An Overleaf project is flat. `../` and absolute paths resolve here and nowhere else."""
    text = _bundle(name)
    assert not re.findall(r"\{\.\./[^}]*\}|\{\{\.\./[^}]*\}", text), f"{name} has ../ paths"
    assert not re.findall(r"\{[A-Za-z]:[\\/][^}]*\}", text), f"{name} has absolute paths"


@pytest.mark.parametrize("name", BUNDLES)
def test_bibliography_is_embedded(name: str) -> None:
    """No .bib ships alongside, so an unembedded bibliography renders every cite as [?]."""
    assert "filecontents" in _bundle(name)


@pytest.mark.parametrize("name", BUNDLES)
def test_style_is_not_loaded_final(name: str) -> None:
    """[final] is the camera-ready option and prints author names on a blind submission."""
    assert "\\usepackage[final]{neurips_2026}" not in _bundle(name)


@pytest.mark.parametrize("name", BUNDLES)
def test_figures_use_bare_filenames(name: str) -> None:
    """Uploaded assets sit beside the .tex, so any directory component fails to resolve."""
    for target in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", _bundle(name)):
        assert "/" not in target, f"{name} references {target} by path, not bare filename"


@pytest.mark.parametrize("name", BUNDLES)
def test_preflight_passes(name: str) -> None:
    """Full preflight, including the three compile scenarios. Skips without a TeX toolchain."""
    if not (Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe").is_file():
        pytest.skip("no local pdflatex; static checks above still ran")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "preflight_overleaf.py"), name],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
