"""Every result number in the paper must trace to a generated macro, and every macro to a run.

`docs/SUBMISSION_CHECKLIST.md` asks that every headline value trace to a frozen artifact.
Three checks already cover parts of that chain and none covers the join:

* `test_committed_paper_sections_contain_no_hardcoded_result_numbers` forbids bare decimals
  in prose, so a number must arrive through a macro.
* `test_generated_provenance.py` pins the digests of the generated files, so the macros file
  is the one the generator produced.
* `scripts/reproduce_pilot_table.py` recomputes the published values independently.

The gap: a section could cite `\\PilotSomethingUndefined`, which is not a bare decimal and
so passes the first check, is absent from the macros file and so is untouched by the second,
and never reaches the third. LaTeX would fail at build time on a machine with a toolchain —
there is none here, so nothing catches it in CI. It would surface as a missing number in a
submitted PDF.

These tests close that join without needing LaTeX.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = ROOT / "paper" / "sections"
MACROS = ROOT / "paper" / "tables" / "pilot_macros.tex"
PROVENANCE = ROOT / "paper" / "tables" / "generated_provenance.json"

#: Macros defined elsewhere in the manuscript preamble rather than by the pilot generator.
#: Empty today, and named explicitly so that adding one is a deliberate act.
EXTERNALLY_DEFINED: frozenset[str] = frozenset()


def _defined() -> set[str]:
    return set(re.findall(r"newcommand\{\\(\w+)\}", MACROS.read_text(encoding="utf-8")))


def _referenced() -> dict[str, list[str]]:
    """Every \\Pilot... macro cited in section prose, mapped to the files citing it."""
    used: dict[str, list[str]] = {}
    for section in sorted(SECTIONS.glob("*.tex")):
        for line in section.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("%"):
                continue
            for name in re.findall(r"\\(Pilot\w+)", line):
                used.setdefault(name, []).append(section.name)
    return used


def test_every_macro_the_paper_cites_is_defined() -> None:
    missing = {
        name: files for name, files in _referenced().items()
        if name not in _defined() and name not in EXTERNALLY_DEFINED
    }
    assert not missing, (
        "paper sections cite macros that pilot_macros.tex does not define. LaTeX would "
        "render these as errors or silently drop them:\n"
        + "\n".join(f"  \\{n} cited in {', '.join(sorted(set(f)))}" for n, f in missing.items())
    )


def test_the_macros_file_names_the_run_it_came_from() -> None:
    """A macro set that does not say which run produced it traces to nothing."""
    header = MACROS.read_text(encoding="utf-8")[:600]
    assert "run:" in header, "pilot_macros.tex does not record its source run"
    recorded = json.loads(PROVENANCE.read_text(encoding="utf-8"))["run_dir"]
    run_name = Path(recorded).name
    assert run_name in header, (
        f"pilot_macros.tex names a different run than the provenance record ({run_name})"
    )


def test_the_named_run_exists_and_holds_chain_artifacts() -> None:
    """The end of the chain: the run the macros name is on disk with results in it."""
    recorded = json.loads(PROVENANCE.read_text(encoding="utf-8"))["run_dir"]
    run_dir = ROOT / recorded
    assert run_dir.is_dir(), f"macros trace to {recorded}, which does not exist"
    chains = list(run_dir.rglob("chain_result.json"))
    assert len(chains) == 25, f"expected 25 chain results under {recorded}, found {len(chains)}"


def test_the_paper_cites_the_primary_contrast_macros() -> None:
    """A results section that never cites the primary contrast is not reporting it."""
    referenced = _referenced()
    for required in ("PilotPrimaryMean", "PilotPrimaryLow", "PilotPrimaryHigh"):
        assert required in referenced, f"the paper never cites \\{required}"
