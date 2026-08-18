"""Real generation step: decode one synthetic corpus through upstream's generate.py.

Stands behind the same contract as ``generation.toy.toy_generate_step`` so the
runner selects between them by configuration rather than by import.

Upstream writes the decoded corpus to ``{experiment_path}/{iteration}/data.json``.
That file is the next generation's training input, which is the data channel the
recursion actually travels along -- see ``docs/interfaces/recursive_steps.md`` for
why the toy path never wired it.

No ``torch`` or ``transformers`` import; the model stack lives in the upstream
checkout this shells out to.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from human_data_budget.runner.upstream_driver import (
    UpstreamStepError,
    run_upstream_step,
    sha256_file,
)

# Upstream's --self_bleu_n_sample defaults to 1000, an O(n^2) NLTK sweep of roughly a
# million BLEU calls per generation -- several times the cost of the decoding it
# describes. It is computed after data.json is written and read only by a disabled
# wandb.log and a diagnostic file, so it cannot change training data or any frozen
# metric. Recorded as deviation 9 in expected_vs_observed.md; kept identical here so
# Stage A and Stage B share one decode cost profile.
SELF_BLEU_N_SAMPLE = 50

REQUIRED_KEYS = (
    "upstream_dir", "generation", "model_identifier", "checkpoint_path",
    "experiment_path", "dataset_filepath", "block_size", "loss_on_last_n_tokens",
    "torch_dtype", "low_cpu_mem_usage", "temperature", "top_p", "top_k",
    "detector_tokenizer_name", "detector_path", "detector_threshold",
    "detector_temperature",
)


def build_generate_command(state: dict[str, Any], seed: int) -> list[str]:
    """Upstream ``generate.py`` invocation for one generation."""
    missing = [key for key in REQUIRED_KEYS if key not in state]
    if missing:
        raise UpstreamStepError(f"real_generate_step state missing keys: {sorted(missing)}")

    return [
        sys.executable, "src/generate.py",
        "--model_name", str(state["model_identifier"]),
        "--model_path", str(state["checkpoint_path"]),
        "--input_token_length",
        str(int(state["block_size"]) - int(state["loss_on_last_n_tokens"])),
        "--block_size", str(state["block_size"]),
        "--iteration", str(int(state["generation"])),
        "--experiment_path", str(state["experiment_path"]),
        "--dataset_filepath", str(state["dataset_filepath"]),
        "--seed", str(seed),
        "--temperature", str(state["temperature"]),
        "--top_p", str(state["top_p"]),
        "--top_k", str(state["top_k"]),
        "--torch_dtype", str(state["torch_dtype"]),
        "--low_cpu_mem_usage", str(state["low_cpu_mem_usage"]),
        "--classify_text", "1",
        "--detector_tokenizer_name", str(state["detector_tokenizer_name"]),
        "--detector_path", str(state["detector_path"]),
        "--detector_threshold", str(state["detector_threshold"]),
        "--detector_temperature", str(state["detector_temperature"]),
        "--self_bleu_n_sample", str(state.get("self_bleu_n_sample", SELF_BLEU_N_SAMPLE)),
    ]


def real_generate_step(state: dict[str, Any], seed: int) -> dict[str, Any]:
    """Decode one generation's synthetic corpus and return a serializable result.

    The returned ``corpus_path`` is what the caller must feed to the next
    generation's training step. Returning it is the point: the toy path discards
    this value, which is why no data flows between generations there.
    """
    upstream_dir = Path(state["upstream_dir"])
    experiment_path = Path(state["experiment_path"])
    generation = int(state["generation"])
    log_path = Path(state.get("log_path", experiment_path.parent / "stdout_stderr.log"))
    command = build_generate_command(state, seed)

    elapsed = run_upstream_step(
        command,
        upstream_dir=upstream_dir,
        log_path=log_path,
        cuda_device=int(state.get("cuda_device", 0)),
        shim_dir=Path(state["shim_dir"]) if state.get("shim_dir") else None,
        dry_run=bool(state.get("dry_run", False)),
    )

    if state.get("dry_run"):
        return {"generation": generation, "seed": seed, "dry_run": True, "command": command}

    corpus = experiment_path / str(generation) / "data.json"
    if not corpus.is_file():
        raise UpstreamStepError(f"generation produced no corpus at {corpus}")

    return {
        "generation": generation,
        "seed": seed,
        "corpus_path": str(corpus),
        "corpus_sha256": sha256_file(corpus),
        "wall_seconds": elapsed,
    }
