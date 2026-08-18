"""`scripts/run_chain.sh` refuses to launch an unfrozen or underspecified config.

`docs/audits/week3_execution_required.md` §1.1 calls this one of "two guards" that
make it safe to ship primary configs whose scientific values are still `null`, and
quotes the exact refusal text. The guard existed, was deleted by commit `243f58b`
("Remaining session changes"), and its absence went unnoticed because nothing
tested it — the script silently regained a hidden `configs/experiment/toy_cpu.json`
default and, given an unfrozen config, died on an uncaught `TypeError` deep inside
`run_directory` rather than refusing.

These tests exist so the same deletion fails visibly next time.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_chain.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None, reason="bash is required to run the launcher script"
)


def run_chain(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def _write(path: Path, payload: dict) -> Path:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")
    return path


# --- no hidden scientific defaults ------------------------------------------


def test_refuses_to_run_without_a_config() -> None:
    """The packet's "no hidden scientific defaults" rule."""
    result = run_chain()

    assert result.returncode != 0
    assert "refusing to guess a config" in result.stderr


def test_no_argument_does_not_silently_launch_the_toy_chain() -> None:
    """The deleted version defaulted to configs/experiment/toy_cpu.json."""
    result = run_chain()

    assert "completed toy chain" not in result.stdout


def test_refuses_a_config_that_does_not_exist(tmp_path: Path) -> None:
    result = run_chain(str(tmp_path / "absent.json"))

    assert result.returncode != 0
    assert "config not found" in result.stderr


# --- the freeze guard -------------------------------------------------------


@pytest.mark.parametrize(
    "config_name",
    # primary_pilot.json was frozen 2026-08-18 (DECISIONS.md P-003..P-007), so it
    # is no longer expected to refuse. The two reference conditions remain
    # unfrozen and must still be refused.
    ["primary_no_rescue.json", "primary_fresh_random.json"],
)
def test_refuses_every_shipped_config_still_awaiting_the_freeze(config_name: str) -> None:
    """The three primary configs must remain unlaunchable until they are frozen."""
    config = ROOT / "configs" / "experiment" / config_name
    payload = json.loads(config.read_text(encoding="utf-8"))
    assert payload["_freeze_status"] == "AWAITING_JULY_31_FREEZE", (
        f"{config_name} is no longer awaiting the freeze; this test needs updating"
    )

    result = run_chain(str(config))

    assert result.returncode != 0
    assert "refusing to launch" in result.stderr
    assert "AWAITING_JULY_31_FREEZE" in result.stderr
    assert "not 'FROZEN'" in result.stderr


def test_refusal_is_a_controlled_message_not_a_crash() -> None:
    """Dying on a TypeError from a null field is not a guard.

    After the guard was deleted the only thing stopping an unfrozen run was an
    accidental `TypeError: unsupported operand type(s) for /: 'WindowsPath' and
    'NoneType'` raised while building the output directory.
    """
    result = run_chain(
        str(ROOT / "configs" / "experiment" / "primary_no_rescue.json"))

    assert "Traceback" not in result.stderr
    assert "TypeError" not in result.stderr


def test_refuses_a_config_whose_scientific_values_are_still_null(tmp_path: Path) -> None:
    """A config marked FROZEN but still holding nulls must not launch either."""
    config = _write(
        tmp_path / "half_filled.json",
        {"_freeze_status": "FROZEN", "run_id": None, "horizon": 3},
    )

    result = run_chain(str(config))

    assert result.returncode != 0
    assert "unset values" in result.stderr
    assert "run_id" in result.stderr


def test_refuses_a_config_that_is_not_valid_json(tmp_path: Path) -> None:
    config = tmp_path / "broken.json"
    config.write_text("{not json\n", encoding="utf-8")

    result = run_chain(str(config))

    assert result.returncode != 0
    assert "not valid JSON" in result.stderr


# --- the frozen path still works --------------------------------------------


def test_a_config_with_no_freeze_status_still_launches() -> None:
    """The toy fixture config carries no `_freeze_status` and must keep working."""
    config = ROOT / "configs" / "experiment" / "toy_cpu.json"
    assert "_freeze_status" not in json.loads(config.read_text(encoding="utf-8"))

    result = run_chain(str(config))

    assert result.returncode == 0, result.stdout + result.stderr
    assert "completed toy chain" in result.stdout
