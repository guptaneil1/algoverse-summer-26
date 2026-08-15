"""Atomic per-generation checkpoints for resuming a recursive chain.

This module is a generic, chain-shape-agnostic atomic JSON store; the caller
decides what belongs in ``state`` (docs/RUNBOOK.md: "Save atomic generation
checkpoints").
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class CheckpointIntegrityError(ValueError):
    """Raised when a checkpoint's bytes do not match its recorded digest."""


def checkpoint_path(run_dir: Path, generation: int) -> Path:
    """Return the conventional checkpoint file path for one generation."""

    return run_dir / "checkpoints" / f"generation_{generation:04d}.json"


def digest_path(path: Path) -> Path:
    """Return the sidecar digest path for a checkpoint.

    A sidecar rather than a field inside the checkpoint: embedding a digest in
    the document it describes means hashing a structure that contains its own
    hash, which requires an exclusion rule that is easy to get subtly wrong. The
    sidecar name deliberately does not match ``generation_*.json``, so
    ``latest_checkpoint`` never mistakes a digest file for a checkpoint.
    """

    return path.with_suffix(path.suffix + ".sha256")


def checkpoint_digest(path: Path) -> str:
    """Return the SHA-256 of a checkpoint file's exact bytes."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_checkpoint(path: Path) -> None:
    """Raise if a checkpoint's bytes disagree with its recorded digest.

    ``PROTOCOL.md`` §3 requires resume from a frozen checkpoint to preserve the
    predeclared conclusion. Silent corruption — a truncated write on a full disk,
    a partial network-storage copy, a hand edit — breaks that guarantee while
    still parsing as valid JSON. Resuming from a corrupted checkpoint would
    produce a chain that looks complete and is not reproducible.

    A checkpoint written before digests existed has no sidecar; that is reported
    as a missing digest rather than a corruption, because the two need different
    responses.
    """

    sidecar = digest_path(path)
    if not path.exists():
        raise CheckpointIntegrityError(f"checkpoint missing: {path}")
    if not sidecar.exists():
        raise CheckpointIntegrityError(
            f"no digest recorded for {path.name}; integrity cannot be verified"
        )

    recorded = sidecar.read_text(encoding="utf-8").strip()
    actual = checkpoint_digest(path)
    if recorded != actual:
        raise CheckpointIntegrityError(
            f"checkpoint {path.name} is corrupt: recorded {recorded[:16]}..., "
            f"computed {actual[:16]}..."
        )


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

    # Record the digest after the checkpoint is durably in place. Ordering
    # matters: a crash between the two leaves a valid checkpoint with a missing
    # digest (recoverable, reported as unverifiable), whereas the reverse would
    # leave a digest describing a file that does not exist.
    digest_tmp = digest_path(path).with_suffix(".sha256.tmp")
    digest_tmp.write_text(checkpoint_digest(path) + "\n", encoding="utf-8")
    os.replace(digest_tmp, digest_path(path))


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
