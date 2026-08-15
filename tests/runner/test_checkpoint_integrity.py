"""Corrupt-checkpoint detection.

Covers the corrupt-hash clause of the `docs/weekly/WEEK_3.md` Neil task "Test
padding, repetition, incomplete batches, gradient accumulation, resume, corrupt
hashes, and incomplete provenance." The other clauses are covered by
`tests/data/test_token_accounting.py`, `tests/data/test_training_provenance.py`,
and `tests/runner/test_checkpoint_resume.py`.

The failure this guards against is specific: a checkpoint that is corrupt but
still parses as JSON. Such a file resumes without error and yields a chain that
looks complete, is silently wrong, and cannot be reproduced.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.runner.checkpoint import (
    CheckpointIntegrityError,
    checkpoint_digest,
    checkpoint_path,
    digest_path,
    latest_checkpoint,
    load_checkpoint,
    save_checkpoint,
    verify_checkpoint,
)


def state(generation: int = 0) -> dict:
    return {
        "generation": generation,
        "remaining_human_tokens": 40,
        "consumed_human_tokens": 20,
        "mode_statistics": {"common": 0.1, "tail": 0.3},
        "allocations": [],
        "metrics": [],
    }


def test_saving_writes_a_digest_sidecar(tmp_path: Path) -> None:
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(), path)
    assert digest_path(path).exists()
    assert digest_path(path).read_text(encoding="utf-8").strip() == checkpoint_digest(path)


def test_intact_checkpoint_verifies(tmp_path: Path) -> None:
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(), path)
    verify_checkpoint(path)  # must not raise


def test_silent_corruption_is_detected(tmp_path: Path) -> None:
    """The core case: still valid JSON, different content, wrong digest."""
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(), path)

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["consumed_human_tokens"] = 999
    path.write_text(json.dumps(tampered, indent=2) + "\n", encoding="utf-8")

    assert load_checkpoint(path) is not None, "the corrupt file still parses as JSON"
    with pytest.raises(CheckpointIntegrityError, match="corrupt"):
        verify_checkpoint(path)


def test_truncated_checkpoint_is_detected(tmp_path: Path) -> None:
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(), path)
    content = path.read_text(encoding="utf-8")
    path.write_text(content[: len(content) // 2], encoding="utf-8")

    with pytest.raises(CheckpointIntegrityError, match="corrupt"):
        verify_checkpoint(path)


def test_whitespace_only_change_is_detected(tmp_path: Path) -> None:
    """Byte-level hashing, not semantic comparison: any edit is a mismatch."""
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(), path)
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(CheckpointIntegrityError, match="corrupt"):
        verify_checkpoint(path)


def test_missing_digest_is_distinguished_from_corruption(tmp_path: Path) -> None:
    """An unverifiable checkpoint and a corrupt one need different responses."""
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(), path)
    digest_path(path).unlink()

    with pytest.raises(CheckpointIntegrityError, match="no digest recorded"):
        verify_checkpoint(path)


def test_missing_checkpoint_is_reported(tmp_path: Path) -> None:
    with pytest.raises(CheckpointIntegrityError, match="missing"):
        verify_checkpoint(checkpoint_path(tmp_path, 7))


def test_digest_sidecar_is_not_mistaken_for_a_checkpoint(tmp_path: Path) -> None:
    """`latest_checkpoint` globs generation_*.json; sidecars must not match."""
    for generation in range(3):
        save_checkpoint(state(generation), checkpoint_path(tmp_path, generation))

    found = latest_checkpoint(tmp_path)
    assert found is not None
    assert found.name == "generation_0002.json"
    assert found.suffix == ".json"


def test_rewriting_a_checkpoint_updates_its_digest(tmp_path: Path) -> None:
    """A legitimate overwrite must stay verifiable, not become a false positive."""
    path = checkpoint_path(tmp_path, 0)
    save_checkpoint(state(0), path)
    first = digest_path(path).read_text(encoding="utf-8").strip()

    save_checkpoint(state(1), path)
    second = digest_path(path).read_text(encoding="utf-8").strip()

    assert first != second
    verify_checkpoint(path)


def test_no_temporary_files_survive(tmp_path: Path) -> None:
    """Atomic writes must not leave .tmp debris that a later glob could pick up."""
    save_checkpoint(state(), checkpoint_path(tmp_path, 0))
    leftovers = list((tmp_path / "checkpoints").glob("*.tmp"))
    assert leftovers == []
