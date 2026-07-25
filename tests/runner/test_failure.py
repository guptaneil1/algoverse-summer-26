import json
from pathlib import Path

import pytest

from human_data_budget.runner.failure import FailureState, write_failure


def test_write_failure_round_trips(tmp_path: Path) -> None:
    failure = FailureState(
        run_id="fixture_run",
        category="implementation_defect",
        message="allocation exceeded budget",
        generation=1,
        evidence={"traceback": "ValueError: allocation exceeds remaining budget"},
        rerun_allowed=True,
    )
    path = tmp_path / "failure.json"
    write_failure(failure, path)
    assert json.loads(path.read_text(encoding="utf-8")) == failure.as_dict()


def test_rejects_unknown_category() -> None:
    with pytest.raises(ValueError):
        FailureState(run_id="r", category="mystery", message="x", generation=None)


def test_rejects_negative_generation() -> None:
    with pytest.raises(ValueError):
        FailureState(run_id="r", category="infrastructure_failure", message="x", generation=-1)


def test_atomic_write_leaves_no_tmp_file(tmp_path: Path) -> None:
    failure = FailureState(
        run_id="r", category="infrastructure_failure", message="oom", generation=0
    )
    path = tmp_path / "nested" / "failure.json"
    write_failure(failure, path)
    assert path.exists()
    assert not (path.parent / "failure.json.tmp").exists()
