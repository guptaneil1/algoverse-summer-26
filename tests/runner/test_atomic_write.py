"""Prove save_checkpoint's atomicity: a crash before the final os.replace can
never leave a half-written file at the destination path.
"""

import json
from pathlib import Path

import pytest

from human_data_budget.runner.checkpoint import (
    checkpoint_path,
    load_checkpoint,
    save_checkpoint,
)


def test_crash_after_write_before_fsync_leaves_prior_checkpoint_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = checkpoint_path(tmp_path, 0)
    valid_state = {"generation": 0, "consumed_human_tokens": 10}
    save_checkpoint(valid_state, path)

    def crashing_fsync(_fd: int) -> None:
        raise OSError("simulated crash: killed before fsync completes")

    monkeypatch.setattr("human_data_budget.runner.checkpoint.os.fsync", crashing_fsync)

    with pytest.raises(OSError, match="simulated crash"):
        save_checkpoint({"generation": 0, "consumed_human_tokens": 999}, path)

    # The destination was never replaced -- the last valid checkpoint survives,
    # never a half-written mix of the old and new state.
    assert load_checkpoint(path) == valid_state
    assert json.loads(path.read_text(encoding="utf-8")) == valid_state


def test_crash_before_fsync_creates_no_destination_when_none_existed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = checkpoint_path(tmp_path, 0)

    def crashing_fsync(_fd: int) -> None:
        raise OSError("simulated crash: killed before fsync completes")

    monkeypatch.setattr("human_data_budget.runner.checkpoint.os.fsync", crashing_fsync)

    with pytest.raises(OSError, match="simulated crash"):
        save_checkpoint({"generation": 0}, path)

    assert not path.exists()
    assert load_checkpoint(path) is None


def test_crash_during_replace_leaves_prior_checkpoint_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = checkpoint_path(tmp_path, 0)
    valid_state = {"generation": 0, "consumed_human_tokens": 10}
    save_checkpoint(valid_state, path)

    def crashing_replace(_src: str, _dst: str) -> None:
        raise OSError("simulated crash: killed during rename")

    monkeypatch.setattr("human_data_budget.runner.checkpoint.os.replace", crashing_replace)

    with pytest.raises(OSError, match="simulated crash"):
        save_checkpoint({"generation": 0, "consumed_human_tokens": 999}, path)

    # The rename never happened -- the destination still holds the last
    # fully-written checkpoint, never a half-applied update.
    assert load_checkpoint(path) == valid_state


def test_destination_path_is_never_opened_directly_for_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The destination is only ever reached via os.replace, never via open()."""

    import builtins

    path = checkpoint_path(tmp_path, 0)
    real_open = builtins.open

    def guarded_open(file, mode="r", *args, **kwargs):
        if str(file) == str(path) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError("save_checkpoint must never open the destination for writing")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("human_data_budget.runner.checkpoint.open", guarded_open, raising=False)

    new_state = {"generation": 0, "consumed_human_tokens": 5}
    save_checkpoint(new_state, path)

    assert load_checkpoint(path) == new_state
