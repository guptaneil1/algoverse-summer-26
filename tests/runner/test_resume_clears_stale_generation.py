"""A resumed generation must own its output directory.

FAILURE_LOG.md F-026. The checkpoint is written at the *end* of a generation, so
resume restarts at the generation after the last completed one -- exactly the
generation an interruption was in the middle of. That generation's ``model/``
directory is already populated by the attempt that died, and upstream
``train.py`` raises rather than writing into a non-empty ``--output_dir``. Every
interrupted chain therefore failed instantly on relaunch.

These tests run under ``dry_run``, which is why the defect survived: dry run
spawns no subprocess and so never creates ``model/`` itself. The stale directory
is planted here explicitly. That is the fifth boundary of the same kind recorded
in F-017, F-020, F-022 and F-025 -- a property the simulation simulates away.
"""

from __future__ import annotations

from pathlib import Path

from human_data_budget.runner.real_chain import run_real_chain
from tests.runner.test_real_chain import _config


def _plant_stale_model_dir(output_dir: Path, generation: int) -> Path:
    """Reproduce what an interrupted attempt leaves behind."""

    model_dir = output_dir / "upstream" / str(generation) / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "pytorch_model.bin").write_bytes(b"partial weights")
    return model_dir


def test_resume_clears_the_directory_of_the_generation_it_retries(tmp_path: Path) -> None:
    out = tmp_path / "out"
    run_real_chain(_config(tmp_path, horizon=2), output_dir=out, dry_run=True)

    # The chain died partway through generation 2, after its checkpoint for 1.
    stale = _plant_stale_model_dir(out, 2)
    assert (stale / "pytorch_model.bin").is_file()

    _, resumed = run_real_chain(
        _config(tmp_path, horizon=3), output_dir=out, resume=True, dry_run=True)

    assert resumed.generations_completed == 3
    assert not (stale / "pytorch_model.bin").exists(), (
        "generation 2 resumed onto the weights of the attempt that failed"
    )


def test_a_chain_with_no_checkpoint_still_clears_generation_zero(tmp_path: Path) -> None:
    """An interruption before the first checkpoint leaves no checkpoints directory.

    ``run_pilot`` then starts the chain from scratch, and generation 0's stale
    ``model/`` blocks it just the same.
    """

    out = tmp_path / "out"
    stale = _plant_stale_model_dir(out, 0)

    _, result = run_real_chain(
        _config(tmp_path, horizon=2), output_dir=out, dry_run=True)

    assert result.generations_completed == 2
    assert not (stale / "pytorch_model.bin").exists()


def test_every_generation_of_a_clean_chain_starts_from_an_absent_directory(
    tmp_path: Path,
) -> None:
    """The clearing is unconditional, so it must not disturb a normal run."""

    out = tmp_path / "out"
    _, result = run_real_chain(_config(tmp_path, horizon=3), output_dir=out, dry_run=True)
    assert result.generations_completed == 3
    assert [m.generation for m in result.metrics] == [0, 1, 2]
