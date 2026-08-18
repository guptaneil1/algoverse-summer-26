"""Real training step: one generation of fine-tuning through upstream's train.py.

Stands behind the same contract as ``training.toy.toy_train_step`` so the runner
can select between them by configuration rather than by import.

**Training corpus is supplied, not mixed here.** Upstream's ``train.py`` can blend
human data itself via ``--human_data_filepath`` and ``--human_data_alpha``, which is
how the positive control's arms are defined. Stage B cannot use that path: a
budget-matched policy chooses *which specific* human examples enter each generation,
and an alpha blend chooses a proportion. The caller therefore assembles
``train_file`` from the previous generation's synthetic corpus plus the policy's
selected human examples, and this step trains on exactly that file with
``human_data_alpha`` pinned to 0.0.

No ``torch`` or ``transformers`` import. The model stack lives in the upstream
checkout this shells out to.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from human_data_budget.runner.upstream_driver import (
    UpstreamStepError,
    optimizer_consumed_tokens,
    run_upstream_step,
    sha256_tree,
)

REQUIRED_KEYS = (
    "upstream_dir", "generation", "model_identifier", "train_file", "test_file",
    "output_dir", "block_size", "loss_on_last_n_tokens", "batch_size",
    "num_train_epochs", "save_steps", "torch_dtype", "low_cpu_mem_usage",
)


def build_train_command(state: dict[str, Any], seed: int) -> list[str]:
    """Upstream ``train.py`` invocation for one generation.

    Kept separate from execution so tests can assert the argument list without a
    GPU, mirroring how the positive control's builders are pinned by test.
    """
    missing = [key for key in REQUIRED_KEYS if key not in state]
    if missing:
        raise UpstreamStepError(f"real_train_step state missing keys: {sorted(missing)}")

    generation = int(state["generation"])
    command = [
        sys.executable, "src/train.py",
        "--model_name_or_path", str(state["model_identifier"]),
        "--output_dir", f"{state['output_dir']}",
        "--per_device_train_batch_size", str(state["batch_size"]),
        "--per_device_eval_batch_size", str(state["batch_size"]),
        "--train_file", str(state["train_file"]),
        "--test_file", str(state["test_file"]),
        "--do_train",
        "--do_eval",
        "--block_size", str(state["block_size"]),
        "--loss_on_last_n_tokens", str(state["loss_on_last_n_tokens"]),
        "--num_train_epochs", str(state["num_train_epochs"]),
        "--save_steps", str(state["save_steps"]),
        "--seed", str(seed),
        "--torch_dtype", str(state["torch_dtype"]),
        "--low_cpu_mem_usage", str(state["low_cpu_mem_usage"]),
        "--run_name", f"train_iteration_{generation}",
        "--iteration", str(generation),
        # The caller already assembled the mixture. Pin alpha to 0 so upstream adds
        # nothing on top of the corpus the policy selected.
        "--human_data_alpha", "0.0",
        "--ai_beta", str(state.get("ai_beta", 1.0)),
        "--preprocessing_num_workers", str(state.get("preprocessing_num_workers", 1)),
    ]
    if "revision" in state and state["revision"]:
        command += ["--model_revision", str(state["revision"])]
    return command


def real_train_step(state: dict[str, Any], seed: int) -> dict[str, Any]:
    """Train one generation and return a serializable result.

    Deterministic for a fixed ``state`` and ``seed`` on fixed hardware: the seed is
    passed to upstream, which seeds sampling, initialization, and dropout. Exact
    bitwise reproducibility across different accelerators is not claimed -- the
    positive control measured a 0.006% spread between two same-seed runs of an
    identical command.
    """
    upstream_dir = Path(state["upstream_dir"])
    output_dir = Path(state["output_dir"])
    log_path = Path(state.get("log_path", output_dir.parent / "stdout_stderr.log"))
    command = build_train_command(state, seed)

    elapsed = run_upstream_step(
        command,
        upstream_dir=upstream_dir,
        log_path=log_path,
        cuda_device=int(state.get("cuda_device", 0)),
        shim_dir=Path(state["shim_dir"]) if state.get("shim_dir") else None,
        dry_run=bool(state.get("dry_run", False)),
    )

    if state.get("dry_run"):
        return {"generation": int(state["generation"]), "seed": seed, "dry_run": True,
                "command": command}

    checkpoint = output_dir / "final_model"
    if not checkpoint.is_dir():
        raise UpstreamStepError(f"training produced no checkpoint at {checkpoint}")
    train_results = output_dir / "train_results.json"

    return {
        "generation": int(state["generation"]),
        "seed": seed,
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": sha256_tree(checkpoint),
        "optimizer_consumed_tokens": optimizer_consumed_tokens(
            train_results, int(state["block_size"])
        ),
        "wall_seconds": elapsed,
    }
