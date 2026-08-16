"""End-to-end: the toy smoke chain must produce a certifiable run package.

Before `data.partitions` was emitted, this chain ran cleanly and then classified
`invalid` with `SEPARATION_MISSING_PROVENANCE` — 14 checks passing and the run still
uncertifiable. Nothing in the suite caught it, because every other test stops at the
manifest or at the validator, never joining the two. This test joins them.

A real chain fails the same way for the same reason, so this guards expensive runs:
provenance cannot be back-filled after a chain completes.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOY_CONFIG = ROOT / "configs/experiment/toy_cpu.json"


@pytest.fixture(scope="module")
def completed_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run the toy chain into a temporary output directory."""

    output_dir = tmp_path_factory.mktemp("toy_chain") / "run"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "human_data_budget.runner.chain",
            "--config",
            str(TOY_CONFIG),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return output_dir


def test_toy_chain_classifies_valid_with_documented_limitations(
    completed_run: Path,
) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_run.py", str(completed_run)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)

    # Was `valid` / no reason codes. The auditor has since gained two checks that
    # correctly report "cannot check" on this run rather than passing it silently:
    #   LIMIT_NEAR_DUPLICATE_NOT_CHECKED  - the manifest carries the four required
    #     provenance fields and no example text, so surface overlap is uncomparable.
    #   LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE - nothing in the repository emits
    #     batch_records.jsonl, so the declared ledger cannot be recomputed.
    # Both are honest limitations of the toy chain, not defects in it. The run is
    # still certifiable; it is simply not certifiable as unqualified `valid`.
    assert report["classification"] == "valid_with_limitation", report["checks_failed"]
    assert set(report["reason_codes"]) == {
        "LIMIT_NEAR_DUPLICATE_NOT_CHECKED",
        "LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE",
    }
    assert not report["schema_failures"]
    assert result.returncode == 1


def test_toy_chain_manifest_records_every_partition(completed_run: Path) -> None:
    manifest = json.loads((completed_run / "run_manifest.json").read_text(encoding="utf-8"))
    partitions = manifest["data"]["partitions"]

    assert set(partitions) == {
        "base_human_train",
        "rescue_candidates",
        "generation_prompts",
        "validation",
        "final_human_test",
    }
    for records in partitions.values():
        assert records
        for record in records:
            assert record["stable_id"]
            assert record["content_hash"]
            assert record["source_dataset"]
            assert record["origin"]
