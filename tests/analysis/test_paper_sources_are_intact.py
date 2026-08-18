"""Catch maimed LaTeX sources before the TeX build job does.

A backslash-escape eaten in transit turns a LaTeX command into a control
character plus a word fragment: ``\\alpha`` becomes BEL + ``lpha``, ``\\begin``
becomes BS + ``egin``, ``\\ref`` becomes CR + ``ef``. The result is still valid
UTF-8 and still passes a structural ``\\input``-target check, so the first thing
that notices is ``pdflatex -halt-on-error`` -- after a TeX Live install, minutes
into CI, with a log nobody reads until the job goes red.

This ran red on PR #30 for exactly that reason. These tests move the failure into
the unit-test job, where it costs seconds.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCES = sorted((ROOT / "paper").rglob("*.tex"))

# Fragments a LaTeX command decays into when its leading backslash is consumed
# as a C escape. Keyed by the escape that ate it.
DECAYED_COMMANDS = (
    "ef{", "egin{", "end{", "ext{", "extbf{", "extit{", "exttt{",
    "rac{", "ewline", "imes", "lpha", "au", "op{",
)


def test_paper_sources_exist() -> None:
    assert SOURCES, "no .tex sources found under paper/"


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.name)
def test_no_control_characters(source: Path) -> None:
    """Only newline is legal. BEL, BS, CR and friends mean an eaten backslash."""
    text = source.read_text(encoding="utf-8")
    offenders = {
        f"0x{ord(ch):02x}" for ch in text if ord(ch) < 32 and ch != "\n"
    }
    assert not offenders, (
        f"{source.name} contains control characters {sorted(offenders)}. "
        "A LaTeX command lost its backslash in transit -- see this module's docstring."
    )


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.name)
def test_no_line_starts_with_a_decayed_command(source: Path) -> None:
    """A line opening with `ef{` or `egin{` is a beheaded command, not prose."""
    offenders = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        for fragment in DECAYED_COMMANDS:
            if stripped.startswith(fragment):
                offenders.append(f"{source.name}:{number}: {stripped[:60]}")
    assert not offenders, "beheaded LaTeX commands:\n" + "\n".join(offenders)


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.name)
def test_braces_balance(source: Path) -> None:
    """An unbalanced brace halts pdflatex too, and is equally invisible upstream."""
    depth, previous = 0, ""
    for character in source.read_text(encoding="utf-8"):
        if previous != "\\":
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
        assert depth >= 0, f"{source.name} closes a brace that was never opened"
        previous = character
    assert depth == 0, f"{source.name} leaves {depth} brace(s) open"
