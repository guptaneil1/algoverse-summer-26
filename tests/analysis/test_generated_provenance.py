"""The committed tables and figure must be what the generator produces.

`docs/SUBMISSION_CHECKLIST.md` asks for tables regenerated from immutable artifacts *and*
their digests recorded. The digest is what turns "generated, not hand-written" from a
statement into a check: `test_committed_paper_sections_contain_no_hardcoded_result_numbers`
guards prose, and until now nothing guarded the generated files themselves. A number
corrected by hand in `pilot_macros.tex` would have propagated into every section that cites
the macro, silently, and the no-hand-editing rule would have been intact on paper only.

This runs `record_paper_provenance.py --check` rather than reimplementing the comparison,
because a test that recomputes the digest its own way can agree with itself while
disagreeing with the tool an operator runs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "paper" / "tables" / "generated_provenance.json"


def test_the_provenance_record_exists_and_names_a_run() -> None:
    assert RECORD.is_file(), "no digest record for the generated tables and figure"
    payload = json.loads(RECORD.read_text(encoding="utf-8"))
    assert payload["run_dir"], "provenance record does not say which run it came from"
    assert payload["_scientific_evidence"] is True
    assert payload["files"], "provenance record covers no files"


def test_every_generated_file_matches_its_recorded_digest() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "record_paper_provenance.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 0, (
        "a generated paper table or figure does not match its recorded digest.\n"
        "Regenerate with scripts/generate_pilot_outputs.py, then re-record with\n"
        "scripts/record_paper_provenance.py.\n\n" + result.stdout + result.stderr
    )


def test_the_record_covers_the_macros_the_paper_actually_cites() -> None:
    """A record that omitted pilot_macros.tex would guard nothing that matters."""
    payload = json.loads(RECORD.read_text(encoding="utf-8"))
    covered = set(payload["files"])
    assert "paper/tables/pilot_macros.tex" in covered
    assert "paper/tables/primary_results.tex" in covered
    assert "results/figures/pilot_nll_by_generation.png" in covered
