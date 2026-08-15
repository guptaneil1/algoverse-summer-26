#!/usr/bin/env python3
"""One reproducible command producing every fixture artifact plus a hash manifest.

Implements the `docs/weekly/WEEK_4.md` Aarav clause "Generate LaTeX/CSV/figures
and hashes through one reproducible command", at the fixture level.

Runs, in order:

1. ``generate_figures.py``        -> results/figures/*.png + figure_provenance.json
2. ``generate_fixture_tables.py`` -> results/tables/*.tex + results/aggregates/fixture_primary.json
3. ``export_csv.py``              -> results/csv/*.csv
4. ``policy_behavior_report.py``  -> results/policy_behavior_report.md

then writes ``results/ARTIFACT_MANIFEST.json``: every produced file with its
SHA-256, so a reviewer can verify that what they are reading is what the
pipeline emitted. `PROTOCOL.md` §3 requires generated tables and figures to
carry content hashes; this is where they are collected in one place.

**Everything produced here is fixture output.** No language model is trained.
The manifest records that fact in a machine-readable field so a downstream
consumer cannot mistake these artifacts for results.

The equivalent command for real runs is `make reproduce-headline`, which stays
guarded until a results freeze exists.

Usage
-----
    python scripts/build_fixture_artifacts.py --seeds 5
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _load(name: str):
    """Import a sibling script as a module without requiring it be installed."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # required before exec for @dataclass resolution
    spec.loader.exec_module(module)
    return module


def _hash_tree(paths: list[Path]) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seeds", type=int, default=5)
    args = parser.parse_args(argv)

    seeds = [str(args.seeds)]

    print("[1/4] figures")
    generate_figures = _load("generate_figures")
    if generate_figures.main(["--seeds", *seeds]) != 0:
        return 1

    print("[2/4] tables")
    generate_fixture_tables = _load("generate_fixture_tables")
    if generate_fixture_tables.main(["--seeds", *seeds]) != 0:
        return 1

    print("[3/4] csv")
    from human_data_budget.analysis.simulator import simulate_all_policies

    export_csv = _load("export_csv")
    with tempfile.TemporaryDirectory() as scratch:
        chain_paths = []
        for seed in range(1, args.seeds + 1):
            for policy, run in simulate_all_policies(chain_seed=seed).items():
                path = Path(scratch) / f"{policy}_seed{seed}.json"
                path.write_text(
                    json.dumps(run["chain_result"], indent=2) + "\n", encoding="utf-8"
                )
                chain_paths.append(str(path))
        if export_csv.main([*chain_paths, "--output-dir", str(RESULTS / "csv")]) != 0:
            return 1

    print("[4/4] policy behaviour report")
    policy_behavior_report = _load("policy_behavior_report")
    if policy_behavior_report.main(["--seeds", *seeds]) != 0:
        return 1

    produced = [
        *sorted((RESULTS / "figures").glob("*.png")),
        RESULTS / "figures" / "figure_provenance.json",
        *sorted((RESULTS / "tables").glob("*.tex")),
        RESULTS / "tables" / "table_provenance.json",
        RESULTS / "aggregates" / "fixture_primary.json",
        *sorted((RESULTS / "csv").glob("*.csv")),
        RESULTS / "policy_behavior_report.md",
    ]

    manifest = {
        "schema_version": "1.0",
        "fixture_only": True,
        "scientific_evidence": False,
        "warning": (
            "Fixture artifacts produced by scripts/build_fixture_artifacts.py from "
            "analysis.simulator. No language model was trained. These files must be "
            "regenerated from immutable chain artifacts before any value enters the "
            "manuscript as a result."
        ),
        "generator": "scripts/build_fixture_artifacts.py",
        "chain_seeds": list(range(1, args.seeds + 1)),
        "artifacts": _hash_tree(produced),
    }

    manifest_path = RESULTS / "ARTIFACT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    print()
    print(f"{len(manifest['artifacts'])} artifacts hashed into {manifest_path.name}")
    for name, digest in manifest["artifacts"].items():
        print(f"  {digest[:16]}...  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
