"""Shared subprocess driver for upstream recursive-training steps.

Factored out of ``scripts/run_positive_control_arm.py`` so Stage A (the published
positive control) and Stage B (the budget-matched policy pilot) drive upstream
through one code path. That path reproduced published values on 2026-08-17, so
Stage B inherits a validated invocation rather than a second implementation.

Pure standard library on purpose. ``torch`` and ``transformers`` are not declared
dependencies of this repository; they live in the upstream checkout this module
shells out to. Importing this module must never require them, so CI and the toy
path keep working on CPU with no model stack installed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class UpstreamStepError(RuntimeError):
    """An upstream subprocess exited non-zero."""


def sha256_file(path: Path) -> str:
    """Content hash of one file, streamed."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_tree(root: Path) -> str:
    """Order-stable content hash of a directory.

    Hashes each file's repository-relative POSIX path and its bytes, walking in
    sorted order, so the digest does not depend on filesystem enumeration order.
    """
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(sha256_file(path).encode("ascii"))
    return digest.hexdigest()


def step_environment(cuda_device: int, *, shim_dir: Path | None = None,
                     overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    """Environment for one upstream subprocess.

    ``CUDA_VISIBLE_DEVICES`` mirrors upstream ``main.py:33``: the child sees exactly
    one device, so the HuggingFace trainer reports ``n_gpu: 1``.

    The wandb variables alone are **not** sufficient. Upstream ``main.py:25`` guards
    ``wandb.init`` with ``bool(str(cfg.wandb_disabled))``, which is always truthy, so
    init never runs while ``train.py`` still calls ``wandb.log`` unconditionally, and
    wandb's pre-init stub raises regardless of mode. ``FAILURE_LOG.md`` F-006 records
    the resulting crash and F-007 the shim that fixes it: a ``sitecustomize.py`` on
    ``PYTHONPATH`` performing a disabled-mode init. Pass ``shim_dir`` to enable it.
    """
    environment = dict(os.environ)
    environment["CUDA_VISIBLE_DEVICES"] = str(cuda_device)
    environment["WANDB_DISABLED"] = "true"
    environment["WANDB_MODE"] = "disabled"
    environment["WANDB_SILENT"] = "true"
    if shim_dir is not None:
        environment["STAGE_A_WANDB_SHIM"] = "1"
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            f"{shim_dir}{os.pathsep}{existing}" if existing else str(shim_dir)
        )
    if overrides:
        environment.update(overrides)
    return environment


def run_upstream_step(command: Sequence[str], *, upstream_dir: Path, log_path: Path,
                      cuda_device: int = 0, shim_dir: Path | None = None,
                      env_overrides: Mapping[str, str] | None = None,
                      dry_run: bool = False) -> float:
    """Run one upstream subprocess, returning wall time in seconds.

    Raises ``UpstreamStepError`` on non-zero exit. Output is appended to
    ``log_path`` rather than captured, so a long decode is inspectable while it runs.
    """
    printable = " ".join(str(part) for part in command)
    print(f"  $ {printable}", flush=True)
    if dry_run:
        return 0.0

    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n===== {printable}\n")
        log.flush()
        result = subprocess.run(
            [str(part) for part in command],
            cwd=upstream_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=step_environment(cuda_device, shim_dir=shim_dir, overrides=env_overrides),
        )
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        raise UpstreamStepError(
            f"upstream step failed (exit {result.returncode}); full log: {log_path}"
        )
    return elapsed


def optimizer_consumed_tokens(train_results: Path, block_size: int) -> int:
    """Tokens actually consumed by the optimizer for one generation.

    ``train_samples`` is the count of tokenized blocks the trainer consumed, so the
    product with ``block_size`` is a count of tokens presented to the optimizer, not
    an estimate from characters or documents. ``PROTOCOL.md`` §3 requires the former
    and forbids the latter. This is the same derivation used for the positive
    control's token ledger in ``COMPUTE.md``.
    """
    payload: dict[str, Any] = json.loads(train_results.read_text(encoding="utf-8"))
    if "train_samples" not in payload:
        raise UpstreamStepError(
            f"{train_results} has no train_samples; cannot count consumed tokens "
            "without estimating, which PROTOCOL.md section 3 forbids"
        )
    return int(payload["train_samples"]) * int(block_size)
