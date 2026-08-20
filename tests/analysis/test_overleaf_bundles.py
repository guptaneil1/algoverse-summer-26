"""The shipped bundles must stay uploadable.

Three bundles get handed to people who paste them into an empty Overleaf project. Two have
already shipped broken --- once with four unresolved `\\input` directives that killed the
compile, once telling the reader to upload a figure the document never references.

**These tests build each bundle from `paper/` rather than reading `dist/`.** An earlier
version read the committed artifact, and failed the moment `dist/` was cleaned, because
`dist/` is a gitignored build directory whose contents are not guaranteed to exist. A test
that depends on a transient artifact reports the artifact's absence as a defect in the
paper. Building from source tests the thing that actually has to keep working: the
derivation.

The static half runs everywhere, including CI with no TeX, because every defect that
actually shipped was textual. The compile half skips cleanly without pdflatex.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from bundle_paper import build  # noqa: E402
from preflight_overleaf import compile_scenario  # noqa: E402

SOURCES = ("evorobust_main.tex", "workshop_main.tex", "main.tex")

_cache: dict[str, str] = {}


def bundle_for(source: str) -> str:
    if source not in _cache:
        _cache[source] = build(source)
    return _cache[source]


def has_latex() -> bool:
    return (Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe").is_file()


@pytest.mark.parametrize("source", SOURCES)
def test_no_unresolved_input(source: str) -> None:
    """The defect that shipped twice: a nested \\input the bundler's regex missed."""
    leftover = re.findall(r"\\input\{[^}]*\}", bundle_for(source))
    assert not leftover, f"{source} would fail on Overleaf: {leftover}"


@pytest.mark.parametrize("source", SOURCES)
def test_no_path_escapes_the_project(source: str) -> None:
    """An Overleaf project is flat: `../` and absolute paths resolve here and nowhere else."""
    text = bundle_for(source)
    assert not re.findall(r"\{\.\./[^}]*\}|\{\{\.\./[^}]*\}", text), f"{source} has ../ paths"
    assert not re.findall(r"\{[A-Za-z]:[\\/][^}]*\}", text), f"{source} has absolute paths"


@pytest.mark.parametrize("source", SOURCES)
def test_bibliography_is_embedded(source: str) -> None:
    """No .bib ships alongside, so an unembedded bibliography renders every cite as [?]."""
    assert "filecontents" in bundle_for(source)


@pytest.mark.parametrize("source", SOURCES)
def test_style_is_not_loaded_final(source: str) -> None:
    """[final] is the camera-ready option and prints author names on a blind submission."""
    assert "\\usepackage[final]{neurips_2026}" not in bundle_for(source)


@pytest.mark.parametrize("source", SOURCES)
def test_figures_use_bare_filenames(source: str) -> None:
    """Uploaded assets sit beside the .tex, so any directory component fails to resolve."""
    for target in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}",
                             bundle_for(source)):
        assert "/" not in target, f"{source} references {target} by path, not bare filename"


@pytest.mark.parametrize("source", SOURCES)
def test_compiles_without_the_venue_style(source: str) -> None:
    """The common case: the reader has not added neurips_2026.sty yet."""
    if not has_latex():
        pytest.skip("no local pdflatex; static checks above still ran")
    assert compile_scenario(bundle_for(source), source, with_figure=True, with_style=False)


@pytest.mark.parametrize("source", SOURCES)
def test_compiles_with_the_venue_style(source: str) -> None:
    """The \\IfFileExists true branch, which nothing else exercises."""
    if not has_latex():
        pytest.skip("no local pdflatex; static checks above still ran")
    assert compile_scenario(bundle_for(source), source, with_figure=True, with_style=True)


@pytest.mark.parametrize("source", SOURCES)
def test_compiles_without_the_figure(source: str) -> None:
    """The figure is a separate upload and gets forgotten; that must not kill the compile."""
    if not has_latex():
        pytest.skip("no local pdflatex; static checks above still ran")
    assert compile_scenario(bundle_for(source), source, with_figure=False, with_style=False)


# --- the single-upload archive ------------------------------------------------
#
# The deliverable is one ZIP, so the ZIP is what has to be known good: unpacked into an
# empty directory and compiled, not merely assembled. The first version of its check
# skipped bibtex and reported 11 pages where the real answer is 13, because the
# bibliography never rendered and every citation stayed undefined.

from build_overleaf_project import VERSIONS  # noqa: E402


def test_archive_covers_every_version() -> None:
    """A ZIP that quietly omits a version is worse than one that fails to build."""
    assert set(VERSIONS) == set(SOURCES)
    assert VERSIONS["evorobust_main.tex"] == "main.tex", (
        "the EvoRobust version must be main.tex so Overleaf compiles it by default"
    )


def test_archive_unpacks_and_compiles() -> None:
    """Build the ZIP, unpack it somewhere empty, compile it, require zero undefined."""
    if not has_latex():
        pytest.skip("no local pdflatex; static checks above still ran")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_overleaf_project.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ARCHIVE READY" in result.stdout
