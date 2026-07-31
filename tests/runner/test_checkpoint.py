from pathlib import Path

from human_data_budget.runner.checkpoint import (
    checkpoint_path,
    latest_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


def test_checkpoint_path_zero_pads_generation(tmp_path: Path) -> None:
    path = checkpoint_path(tmp_path, 3)
    assert path == tmp_path / "checkpoints" / "generation_0003.json"


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    state = {"generation": 1, "consumed_human_tokens": 20, "mode_statistics": {"tail": 0.4}}
    path = checkpoint_path(tmp_path, 1)
    save_checkpoint(state, path)
    assert load_checkpoint(path) == state


def test_load_missing_checkpoint_returns_none(tmp_path: Path) -> None:
    assert load_checkpoint(checkpoint_path(tmp_path, 0)) is None


def test_atomic_write_leaves_no_tmp_file(tmp_path: Path) -> None:
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint({"generation": 0}, path)
    assert path.exists()
    assert not (path.parent / "generation_0000.json.tmp").exists()


def test_latest_checkpoint_returns_highest_generation(tmp_path: Path) -> None:
    for generation in (0, 1, 2):
        save_checkpoint({"generation": generation}, checkpoint_path(tmp_path, generation))
    assert latest_checkpoint(tmp_path) == checkpoint_path(tmp_path, 2)


def test_latest_checkpoint_none_when_absent(tmp_path: Path) -> None:
    assert latest_checkpoint(tmp_path) is None
    (tmp_path / "checkpoints").mkdir()
    assert latest_checkpoint(tmp_path) is None
