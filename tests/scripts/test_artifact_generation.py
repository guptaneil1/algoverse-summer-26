"""Tests for the fixture artifact-generation scripts.

Covers `scripts/export_csv.py`, `scripts/generate_fixture_tables.py`,
`scripts/policy_behavior_report.py`, `scripts/build_fixture_artifacts.py`, and
`scripts/generate_figures.py`.

These scripts produce the *format* that real results will later occupy, so two
classes of defect matter more than usual:

1. **A fixture value reaching the manuscript.** `PROTOCOL.md` §5 forbids any
   experimental value entering the paper before its artifact validates. Fixture
   output is not experimental at all, so it must stay out of `paper/` entirely.
2. **Silent format drift.** If a column disappears or a watermark is dropped, the
   error surfaces only when someone reads a published table.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest

from human_data_budget.analysis.simulator import POLICY_NAMES, simulate_all_policies

ROOT = Path(__file__).resolve().parents[2]

# Defined at module top because skipif decorators are evaluated at import time,
# in definition order.
matplotlib_available = importlib.util.find_spec("matplotlib") is not None


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


export_csv = load_script("export_csv")
generate_fixture_tables = load_script("generate_fixture_tables")
policy_behavior_report = load_script("policy_behavior_report")


def chain_results(seeds: range = range(1, 4)) -> list[dict]:
    documents = []
    for seed in seeds:
        for run in simulate_all_policies(chain_seed=seed).values():
            documents.append(run["chain_result"])
    return documents


def write_results(tmp_path: Path, documents: list[dict]) -> list[Path]:
    paths = []
    for index, document in enumerate(documents):
        path = tmp_path / f"chain_{index}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        paths.append(path)
    return paths


# --------------------------------------------------------------------------
# export_csv
# --------------------------------------------------------------------------


def test_long_csv_has_one_row_per_chain_generation(tmp_path: Path) -> None:
    documents = chain_results()
    out = tmp_path / "out"
    export_csv.write_long(documents, out / "long.csv")

    rows = list(csv.DictReader((out / "long.csv").open(encoding="utf-8")))
    expected = sum(len(document["metrics"]) for document in documents)
    assert len(rows) == expected


def test_long_csv_preserves_the_generation_column(tmp_path: Path) -> None:
    """Averaging generations away is the repeated-observations mistake."""
    out = tmp_path / "long.csv"
    export_csv.write_long(chain_results(), out)
    header = csv.DictReader(out.open(encoding="utf-8")).fieldnames
    assert "generation" in header
    assert "chain_seed" in header


def test_long_csv_column_set_is_stable(tmp_path: Path) -> None:
    out = tmp_path / "long.csv"
    export_csv.write_long(chain_results(), out)
    header = csv.DictReader(out.open(encoding="utf-8")).fieldnames
    assert header == export_csv.LONG_COLUMNS


def test_summary_excludes_invalid_chains(tmp_path: Path) -> None:
    """An excluded chain must not contribute to a policy mean."""
    documents = chain_results(range(1, 3))
    for document in documents:
        if document["policy"] == "joint":
            document["valid"] = False
            document["exclusion_reason"] = "fixture exclusion"

    out = tmp_path / "summary.csv"
    export_csv.write_summary(documents, out)
    rows = {row["policy"]: row for row in csv.DictReader(out.open(encoding="utf-8"))}
    assert "joint" not in rows
    assert "random" in rows


def test_invalid_chain_still_appears_in_the_long_file(tmp_path: Path) -> None:
    """Excluded chains are retained in the raw export, never silently dropped."""
    documents = chain_results(range(1, 2))
    documents[0]["valid"] = False
    documents[0]["exclusion_reason"] = "evaluator crash"

    out = tmp_path / "long.csv"
    export_csv.write_long(documents, out)
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert any(row["exclusion_reason"] == "evaluator crash" for row in rows)


def test_schema_invalid_input_is_refused(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"run_id": "x"}), encoding="utf-8")
    with pytest.raises(jsonschema.ValidationError):
        export_csv.load_results([bad])


def test_export_is_deterministic(tmp_path: Path) -> None:
    documents = chain_results()
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    export_csv.write_long(documents, first)
    export_csv.write_long(list(reversed(documents)), second)
    assert first.read_bytes() == second.read_bytes(), "row order must not depend on input order"


# --------------------------------------------------------------------------
# generate_fixture_tables
# --------------------------------------------------------------------------


def test_fixture_tables_never_write_into_paper(tmp_path: Path) -> None:
    """The invariant that keeps a simulated number out of the manuscript."""
    before = (ROOT / "paper" / "tables" / "primary_results.tex").read_bytes()
    generate_fixture_tables.main(
        [
            "--seeds",
            "2",
            "--table-dir",
            str(tmp_path / "tables"),
            "--aggregate-out",
            str(tmp_path / "aggregate.json"),
        ]
    )
    after = (ROOT / "paper" / "tables" / "primary_results.tex").read_bytes()
    assert before == after, "fixture generation modified the manuscript's result table"


def test_paper_result_table_is_still_pending() -> None:
    """`paper/tables/primary_results.tex` must not contain fixture numbers."""
    text = (ROOT / "paper" / "tables" / "primary_results.tex").read_text(encoding="utf-8")
    assert "RESULT\\_PENDING" in text or "RESULT_PENDING" in text


def test_no_fixture_figures_live_in_the_manuscript_directory() -> None:
    """`paper/figures/` must hold only result-independent sources.

    Fixture PNGs sitting here are one stray `\\includegraphics` away from putting
    a simulated figure in the PDF. They are watermarked, but a watermark is a
    last line of defence, not a reason to store them in the manuscript tree.
    Generated figures live in `results/figures/`; `paper/figures/` receives them
    only when the inputs are real chain artifacts.
    """
    stray = sorted(path.name for path in (ROOT / "paper" / "figures").glob("*.png"))
    assert stray == [], (
        f"fixture figures found in paper/figures/: {stray}. "
        "generate_figures.py must not mirror there while inputs are simulated."
    )


@pytest.mark.skipif(not matplotlib_available, reason="matplotlib is an optional extra")
def test_generate_figures_writes_nowhere_but_output_dir_by_default(tmp_path: Path) -> None:
    """With no --mirror-dir, exactly one directory receives files.

    Asserted behaviourally rather than by inspecting argparse defaults: running
    the script and checking where files landed is what actually matters.
    """
    generate_figures = load_script("generate_figures")
    output = tmp_path / "out"
    sentinel = tmp_path / "should-stay-empty"
    sentinel.mkdir()

    generate_figures.main(["--seeds", "2", "--output-dir", str(output)])

    assert sorted(path.name for path in output.glob("*.png"))
    assert list(sentinel.iterdir()) == []


def test_generated_tables_carry_the_fixture_banner(tmp_path: Path) -> None:
    generate_fixture_tables.main(
        [
            "--seeds",
            "2",
            "--table-dir",
            str(tmp_path / "tables"),
            "--aggregate-out",
            str(tmp_path / "aggregate.json"),
        ]
    )
    for name in ("fixture_primary_results.tex", "fixture_paired_contrasts.tex"):
        text = (tmp_path / "tables" / name).read_text(encoding="utf-8")
        assert "FIXTURE DATA" in text
        assert "Not scientific evidence" in text
        assert "never be \\input by paper" in text


def test_every_emitted_chain_result_is_schema_valid(tmp_path: Path) -> None:
    """The task says "from fake schema-valid results" — enforce, don't assume."""
    paths = generate_fixture_tables.write_chain_results([1, 2], tmp_path)
    assert len(paths) == 2 * len(POLICY_NAMES)


def test_fixture_aggregate_is_marked_non_evidence(tmp_path: Path) -> None:
    aggregate_path = tmp_path / "aggregate.json"
    generate_fixture_tables.main(
        ["--seeds", "2", "--table-dir", str(tmp_path / "t"), "--aggregate-out", str(aggregate_path)]
    )
    document = json.loads(aggregate_path.read_text(encoding="utf-8"))
    assert document["fixture_only"] is True
    assert document["scientific_evidence"] is False


def test_table_generation_is_deterministic(tmp_path: Path) -> None:
    digests = []
    for run in ("a", "b"):
        table_dir = tmp_path / run
        generate_fixture_tables.main(
            [
                "--seeds",
                "3",
                "--table-dir",
                str(table_dir),
                "--aggregate-out",
                str(tmp_path / f"{run}.json"),
            ]
        )
        digests.append(
            hashlib.sha256((table_dir / "fixture_primary_results.tex").read_bytes()).hexdigest()
        )
    assert digests[0] == digests[1]


# --------------------------------------------------------------------------
# policy_behavior_report
# --------------------------------------------------------------------------


def test_report_finds_no_degenerate_pairs() -> None:
    """The report must reflect the frozen implementation, not the reverted scaffold.

    This asserted `Degenerate pairs found: 2` and the presence of `F-001`. Both
    described `policies/joint.py` as commit `243f58b` left it — reverted to the
    Week-1 scaffold. With the frozen implementation restored the four families
    separate, so the report correctly finds none. See `FAILURE_LOG.md` F-005.
    """
    report = policy_behavior_report.build_report([1, 2, 3])
    assert "Degenerate pairs found: 0" in report


def test_report_carries_the_non_evidence_warning() -> None:
    report = policy_behavior_report.build_report([1])
    assert "FIXTURE DATA" in report
    assert "No language model was trained" in report


def test_report_confirms_budget_equality() -> None:
    report = policy_behavior_report.build_report([1, 2])
    assert "Budget equality: HOLDS" in report


def test_report_records_monitoring_sensitivity() -> None:
    report = policy_behavior_report.build_report([1, 2])
    assert "Monitoring-omission sensitivity" in report


def test_report_is_deterministic() -> None:
    assert policy_behavior_report.build_report([1, 2]) == policy_behavior_report.build_report(
        [1, 2]
    )


# --------------------------------------------------------------------------
# Committed artifact manifest
# --------------------------------------------------------------------------

MANIFEST = ROOT / "results" / "ARTIFACT_MANIFEST.json"


@pytest.mark.skipif(not MANIFEST.exists(), reason="fixture artifacts not built")
def test_committed_manifest_hashes_match_the_files_on_disk() -> None:
    """A manifest that disagrees with its artifacts is worse than no manifest."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, recorded in manifest["artifacts"].items():
        path = ROOT / relative
        if not path.exists():
            mismatches.append(f"{relative}: missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != recorded:
            mismatches.append(f"{relative}: recorded {recorded[:12]}, actual {actual[:12]}")
    assert not mismatches, "regenerate with `make fixture-artifacts`:\n" + "\n".join(mismatches)


@pytest.mark.skipif(not MANIFEST.exists(), reason="fixture artifacts not built")
def test_committed_manifest_is_marked_non_evidence() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["fixture_only"] is True
    assert manifest["scientific_evidence"] is False


# --------------------------------------------------------------------------
# generate_figures (optional dependency)
# --------------------------------------------------------------------------


@pytest.mark.skipif(not matplotlib_available, reason="matplotlib is an optional extra")
def test_figures_are_deterministic(tmp_path: Path) -> None:
    generate_figures = load_script("generate_figures")
    digests = []
    for run in ("a", "b"):
        output = tmp_path / run
        generate_figures.main(
            ["--seeds", "3", "--output-dir", str(output), "--mirror-dir", str(tmp_path / f"m{run}")]
        )
        digests.append(
            hashlib.sha256((output / "nll_by_generation.png").read_bytes()).hexdigest()
        )
    assert digests[0] == digests[1]


@pytest.mark.skipif(not matplotlib_available, reason="matplotlib is an optional extra")
def test_figure_provenance_records_matplotlib_version(tmp_path: Path) -> None:
    """PNG bytes are version-dependent, so the version must travel with the hashes."""
    generate_figures = load_script("generate_figures")
    generate_figures.main(
        ["--seeds", "2", "--output-dir", str(tmp_path), "--mirror-dir", str(tmp_path / "mirror")]
    )
    provenance = json.loads((tmp_path / "figure_provenance.json").read_text(encoding="utf-8"))
    assert provenance["matplotlib_version"]
    assert provenance["fixture_only"] is True
    assert set(provenance["figure_sha256"]) == {
        "nll_by_generation.png",
        "tail_retention_by_generation.png",
        "allocation_by_generation.png",
        "paired_difference.png",
    }
