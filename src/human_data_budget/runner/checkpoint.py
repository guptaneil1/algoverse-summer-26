"""Atomic per-generation checkpoints for resuming a recursive chain.

This module is a generic, chain-shape-agnostic atomic JSON store; the caller
decides what belongs in ``state`` (docs/RUNBOOK.md: "Save atomic generation
checkpoints").
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def checkpoint_path(run_dir: Path, generation: int) -> Path:
    """Return the conventional checkpoint file path for one generation."""

    return run_dir / "checkpoints" / f"generation_{generation:04d}.json"


def save_checkpoint(state: dict[str, Any], path: Path) -> None:
    """Atomically write ``state`` as the checkpoint at ``path``.

    Writes to a temp file in the same directory, flushes and fsyncs it, then
    ``os.replace``s it onto ``path``. The destination is never opened for
    writing directly, so a crash at any point before the replace leaves
    whatever was previously at ``path`` (a prior valid checkpoint, or
    nothing) untouched — never a half-written file.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state, indent=2) + "\n"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)


def load_checkpoint(path: Path) -> dict[str, Any] | None:
    """Return the checkpoint at ``path``, or ``None`` if it does not exist."""

    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def latest_checkpoint(run_dir: Path) -> Path | None:
    """Return the highest-generation checkpoint path under ``run_dir``, or None."""

    checkpoints_dir = run_dir / "checkpoints"
    if not checkpoints_dir.is_dir():
        return None
    candidates = sorted(checkpoints_dir.glob("generation_*.json"))
    return candidates[-1] if candidates else None
