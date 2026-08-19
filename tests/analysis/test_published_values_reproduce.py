"""The headline numbers must reproduce from the artifacts, by independent arithmetic.

`scripts/reproduce_pilot_table.py` recomputes every published quantity from
`chain_result.json` alone, deliberately sharing no code with the generator that produced
the paper's table -- an independent check that calls the thing it is checking is not
independent.

This runs it in CI so the published values cannot drift away from the artifacts silently.
It is the automatable half of the submission checklist's "headline table reproduced by
someone who did not write the analysis"; the human half still stands.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results" / "runs" / "primary_pilot_2026-08-18"


@pytest.mark.skipif(not RUN.is_dir(), reason="pilot artifacts not present")
def test_every_published_value_reproduces() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/reproduce_pilot_table.py", "--run-dir", str(RUN)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        "published values no longer reproduce from the chain artifacts:\n"
        + result.stdout + result.stderr
    )
    assert "every published value reproduced" in result.stdout
