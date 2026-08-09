"""Tables are generated from an aggregate and contain no hand-typed value."""

import importlib.util
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AGGREGATE_CLI = ROOT / "scripts" / "aggregate_chain_results.py"
TABLES_CLI = ROOT / "scripts" / "generate_tables.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "aggregate_chain_results", AGGREGATE_CLI
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agg = _load_module()

ChainFactory = Callable[..., dict[str, Any]]
WriteChain = Callable[..., Path]


def test_aggregate_cli_writes_a_labelled_file(
    chain_payload: ChainFactory, write_chain: WriteChain, tmp_path: Path
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1)),
        write_chain(chain_payload("joint-2", "joint", 2)),
    ]
    output = tmp_path / "aggregates" / "provisional.json"

    completed = subprocess.run(
        [sys.executable, str(AGGREGATE_CLI), *map(str, paths), "--output", str(output)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["label"] == "provisional"
    assert payload["policies"]["joint"]["chain_count"] == 2


def test_aggregate_cli_rejects_duplicates_with_exit_two(
    chain_payload: ChainFactory, write_chain: WriteChain, tmp_path: Path
) -> None:
    paths = [
        write_chain(chain_payload("joint-1", "joint", 1), "a.json"),
        write_chain(chain_payload("joint-1", "joint", 2), "b.json"),
    ]
    completed = subprocess.run(
        [
            sys.executable,
            str(AGGREGATE_CLI),
            *map(str, paths),
            "--output",
            str(tmp_path / "out.json"),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 2
    assert "REJECTED" in completed.stdout


def test_table_is_generated_from_the_aggregate(
    chain_payload: ChainFactory, write_chain: WriteChain, tmp_path: Path
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1, nlls=(2.0, 4.0)))
    aggregate_path = tmp_path / "aggregate.json"
    aggregate_path.write_text(json.dumps(agg.aggregate([path])), encoding="utf-8")

    table = tmp_path / "table.tex"
    completed = subprocess.run(
        [sys.executable, str(TABLES_CLI), str(aggregate_path), "--output", str(table)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    text = table.read_text(encoding="utf-8")
    assert "AUTO-GENERATED" in text
    assert "3.0000" in text


def test_empty_aggregate_renders_result_pending(tmp_path: Path) -> None:
    aggregate_path = tmp_path / "aggregate.json"
    aggregate_path.write_text(json.dumps({"policies": {}}), encoding="utf-8")

    table = tmp_path / "table.tex"
    subprocess.run(
        [sys.executable, str(TABLES_CLI), str(aggregate_path), "--output", str(table)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert "RESULT\\_PENDING" in table.read_text(encoding="utf-8")


def test_generated_table_carries_the_do_not_edit_banner(
    chain_payload: ChainFactory, write_chain: WriteChain, tmp_path: Path
) -> None:
    path = write_chain(chain_payload("joint-1", "joint", 1))
    aggregate_path = tmp_path / "aggregate.json"
    aggregate_path.write_text(json.dumps(agg.aggregate([path])), encoding="utf-8")

    table = tmp_path / "table.tex"
    subprocess.run(
        [sys.executable, str(TABLES_CLI), str(aggregate_path), "--output", str(table)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    first_line = table.read_text(encoding="utf-8").splitlines()[0]
    assert "DO NOT EDIT" in first_line


def test_committed_paper_sections_contain_no_hardcoded_result_numbers() -> None:
    """Result-bearing prose must stay generated or explicitly pending."""
    sections = sorted((ROOT / "paper" / "sections").glob("*.tex"))
    assert sections, "no paper sections found"

    # A bare decimal in prose is the shape of a hand-entered experimental value.
    decimal = re.compile(r"(?<![\w.\\])\d+\.\d+(?![\w.])")
    offenders = []
    for section in sections:
        for number, line in enumerate(section.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("%"):
                continue
            if decimal.search(stripped):
                offenders.append(f"{section.name}:{number}: {stripped}")

    assert not offenders, "hand-entered numeric values in paper prose:\n" + "\n".join(offenders)
