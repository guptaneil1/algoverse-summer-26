#!/usr/bin/env python3
"""Record content digests for every generated paper table and figure.

`docs/SUBMISSION_CHECKLIST.md` requires tables and figures to be regenerated from
immutable artifacts *and* their digests recorded, so a reader can tell whether the
committed `.tex` and `.png` are the ones the generator produces from the committed
chain results, or whether something was touched by hand afterwards.

The digest is the check that the no-hand-editing rule is actually enforced rather than
merely stated. `test_committed_paper_sections_contain_no_hardcoded_result_numbers` covers
prose; nothing covered the generated files themselves.

`results/figures/figure_provenance.json` already exists and covers the *fixture* figures
from `scripts/generate_figures.py`, which are explicitly marked `scientific_evidence:
false`. It does not cover `pilot_nll_by_generation.png`, which is generated from real
chain artifacts by a different script. This file covers the real ones.

Usage:
    python scripts/record_paper_provenance.py --run-dir results/runs/primary_pilot_v2_2026-08-20
    python scripts/record_paper_provenance.py --check

Exit codes: 0 written, or verified with everything matching; 1 a digest disagrees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "paper" / "tables" / "generated_provenance.json"

#: Generated from real chain artifacts. Anything not listed here is either hand-written
#: (and must not be) or fixture output (covered by results/figures/figure_provenance.json).
GENERATED = (
    "paper/tables/primary_results.tex",
    "paper/tables/pilot_macros.tex",
    "results/figures/pilot_nll_by_generation.png",
)


def digest(path: Path) -> dict:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path,
                        default=Path("results/runs/primary_pilot_v2_2026-08-20"))
    parser.add_argument("--check", action="store_true",
                        help="verify committed digests instead of rewriting them")
    args = parser.parse_args()

    current = {}
    for relative in GENERATED:
        path = ROOT / relative
        if not path.is_file():
            print(f"missing generated file: {relative}")
            return 1
        current[relative] = digest(path)

    if args.check:
        if not OUTPUT.is_file():
            print(f"no provenance record at {OUTPUT.relative_to(ROOT)}")
            return 1
        recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))["files"]
        bad = [r for r in GENERATED
               if recorded.get(r, {}).get("sha256") != current[r]["sha256"]]
        for relative in bad:
            print(f"DIGEST MISMATCH {relative}\n"
                  f"  recorded {recorded.get(relative, {}).get('sha256')}\n"
                  f"  actual   {current[relative]['sha256']}")
        if bad:
            print("\nEither the generator was re-run against different artifacts, or a "
                  "generated file was edited by hand. Regenerate and re-record.")
            return 1
        print(f"{len(GENERATED)} generated files match their recorded digests")
        return 0

    payload = {
        "_purpose": (
            "SHA-256 of every paper table and figure generated from real chain artifacts. "
            "Regenerate with scripts/generate_pilot_outputs.py and re-record with this "
            "script; verify with --check."
        ),
        "_scientific_evidence": True,
        "_not_covered_here": (
            "Fixture figures from scripts/generate_figures.py are covered by "
            "results/figures/figure_provenance.json and are marked scientific_evidence: "
            "false. method_hyperparameters.tex and positive_control.tex come from "
            "scripts/generate_method_tables.py and the positive-control artifacts, not "
            "from the pilot run named below."
        ),
        "generator": "scripts/generate_pilot_outputs.py",
        "run_dir": str(args.run_dir).replace("\\", "/"),
        "files": current,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} covering {len(current)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
