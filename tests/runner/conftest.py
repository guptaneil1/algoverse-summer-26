"""Shared fixtures for the positive-control runner tests.

These build a *synthetic stand-in* for an upstream experiment directory. They let the
adapter, its resume path, and its hash verification be tested on any machine, including
one with no accelerator. Nothing produced here is scientific evidence, and no test in
this directory may be read as evidence that the positive control reproduced.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATHS = {
    "fully_synthetic": ROOT / "configs/experiment/positive_control_fully_synthetic.json",
    "human_mixed": ROOT / "configs/experiment/positive_control_human_mixed.json",
}

#: Values the executing host must resolve, standing in for real Hugging Face revisions.
_TEST_RESOLUTIONS = {
    "model": {
        "revision": "0" * 40,
        "tokenizer_revision": "0" * 40,
    },
    "data": {
        "revision": "1" * 40,
        "train_manifest_sha256": "2" * 64,
    },
}


@pytest.fixture
def make_upstream_experiment(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory building a fake upstream experiment directory.

    The layout mirrors ``main.py`` at the pinned upstream commit: one directory per
    generation holding ``model/final_model/``, ``model/eval_results.json``, and, above
    generation zero, the ``data.json`` that generation trained on.
    """

    def _make(perplexities: list[float], *, name: str = "upstream") -> Path:
        experiment_path = tmp_path / name
        for generation, perplexity in enumerate(perplexities):
            generation_dir = experiment_path / str(generation)
            model_dir = generation_dir / "model" / "final_model"
            model_dir.mkdir(parents=True)
            (model_dir / "config.json").write_text(
                json.dumps({"generation": generation}), encoding="utf-8"
            )
            (model_dir / "model.safetensors").write_bytes(
                b"fake-weights-generation-" + str(generation).encode("ascii")
            )
            (generation_dir / "model" / "eval_results.json").write_text(
                json.dumps({"perplexity": perplexity, "eval_loss": math.log(perplexity)}),
                encoding="utf-8",
            )
            if generation > 0:
                (generation_dir / "data.json").write_text(
                    json.dumps({"generation": generation, "text": "fake synthetic text"}),
                    encoding="utf-8",
                )
        return experiment_path

    return _make


@pytest.fixture
def resolved_arm_config() -> Callable[..., dict[str, Any]]:
    """Return a factory yielding a real arm config with runtime identifiers filled in.

    The committed configs deliberately carry ``resolve_at_runtime`` sentinels, and the
    adapter refuses to run while they are unresolved. Tests exercising the ingest path
    must therefore resolve them first, exactly as the accelerator host would.
    """

    def _make(arm: str = "fully_synthetic", *, horizon: int | None = None) -> dict[str, Any]:
        config = json.loads(CONFIG_PATHS[arm].read_text(encoding="utf-8"))
        for section, resolutions in _TEST_RESOLUTIONS.items():
            config[section].update(resolutions)
        if horizon is not None:
            config["horizon"] = horizon
        return config

    return _make
