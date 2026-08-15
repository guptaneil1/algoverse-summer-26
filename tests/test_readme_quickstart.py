"""The documented quickstart must stay true.

Implements the `docs/weekly/WEEK_4.md` Khantushig clause "Verify ... exact README
commands".

A quickstart that drifts from the Makefile is worse than no quickstart: a new
contributor follows it, hits an error, and cannot tell whether they made a
mistake or the docs did. These tests fail CI when README and Makefile disagree,
and when a command references a file that no longer exists.

Commands with side effects (creating a venv, installing packages, running the
full suite) are checked structurally rather than executed — executing them from
inside the suite would recurse. `scripts/verify_clean_install.sh` executes them
for real in a throwaway environment.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MAKEFILE = ROOT / "Makefile"


def quickstart_block() -> list[str]:
    """Return the commands from README's first ```bash block."""
    text = README.read_text(encoding="utf-8")
    match = re.search(r"```bash\n(.*?)```", text, re.DOTALL)
    assert match is not None, "README.md no longer contains a ```bash quickstart block"
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def makefile_target(name: str) -> list[str]:
    """Return the recipe lines of one Makefile target."""
    lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    recipe: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith(f"{name}:"):
            collecting = True
            continue
        if collecting:
            if line.startswith("\t"):
                recipe.append(line.strip())
            elif line.strip():
                break
    return recipe


def test_quickstart_block_exists_and_is_non_trivial() -> None:
    commands = quickstart_block()
    assert len(commands) >= 4, f"quickstart shrank unexpectedly: {commands}"


def test_install_commands_match_the_setup_target() -> None:
    """README install lines must be exactly what `make setup` runs.

    If they diverge, one of the two is lying about how to install the project.
    """
    quickstart = quickstart_block()
    setup = makefile_target("setup")
    assert setup, "Makefile has no `setup` target"
    for command in setup:
        assert command in quickstart, (
            f"`make setup` runs {command!r} but the README quickstart does not. "
            "Update whichever is stale."
        )


def test_quickstart_references_existing_files() -> None:
    """Every path a quickstart command names must exist."""
    for command in quickstart_block():
        for token in command.split():
            if token.endswith((".txt", ".json", ".toml", ".cfg")):
                assert (ROOT / token).exists(), (
                    f"quickstart references {token!r}, which does not exist"
                )


def test_quickstart_smoke_config_exists() -> None:
    """The documented chain command must point at a real config."""
    commands = quickstart_block()
    chain_commands = [command for command in commands if "runner.chain" in command]
    assert chain_commands, "quickstart no longer documents the toy chain command"

    for command in chain_commands:
        match = re.search(r"--config\s+(\S+)", command)
        assert match is not None, f"chain command has no --config: {command!r}"
        assert (ROOT / match.group(1)).exists(), (
            f"quickstart chain config {match.group(1)!r} does not exist"
        )


def test_documented_python_floor_matches_pyproject() -> None:
    """README's stated Python requirement must match the packaging metadata."""
    readme = README.read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    declared = re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"', pyproject)
    assert declared is not None, "pyproject.toml no longer declares requires-python"
    version = declared.group(1)

    assert version in readme, (
        f"pyproject requires Python >={version} but README does not mention {version}"
    )


def test_every_makefile_target_is_declared_phony() -> None:
    """A target missing from .PHONY silently breaks if a same-named file appears."""
    text = MAKEFILE.read_text(encoding="utf-8")
    phony_line = next(
        (line for line in text.splitlines() if line.startswith(".PHONY:")), None
    )
    assert phony_line is not None, "Makefile has no .PHONY declaration"
    declared = set(phony_line.removeprefix(".PHONY:").split())

    targets = {
        match.group(1)
        for match in re.finditer(r"^([a-z][a-z0-9-]*):", text, re.MULTILINE)
    }
    missing = targets - declared
    assert not missing, f"Makefile targets missing from .PHONY: {sorted(missing)}"
