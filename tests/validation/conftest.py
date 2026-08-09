"""Adversarial run fixtures for the independent validity audit.

Every fixture is synthetic. The validator is developed against these attacks so
that no unfinished branch or real experimental artifact is required.
"""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

CLEAN_COMMIT = "a" * 40


def _example(stable_id: str, text: str, origin: str = "human") -> dict[str, Any]:
    return {
        "stable_id": stable_id,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_dataset": "toy/v1",
        "origin": origin,
    }


def valid_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": "fixture_valid",
        "stage": "fixture",
        "git_commit": CLEAN_COMMIT,
        "working_tree_clean": True,
        "model": {"identifier": "toy", "revision": "r1", "tokenizer_revision": "r1"},
        "data": {
            "train_manifest": "data/manifests/toy.json",
            "train_manifest_sha256": "b" * 64,
            "partitions": {
                "base_human_train": [_example("train-1", "alpha")],
                "rescue_candidates": [_example("rescue-1", "beta")],
                "generation_prompts": [_example("prompt-1", "gamma", "synthetic")],
                "validation": [_example("val-1", "delta")],
                "final_human_test": [_example("test-1", "epsilon")],
            },
        },
        "policy": {
            "name": "joint",
            "config": "configs/policy/joint.json",
            "config_sha256": "c" * 64,
        },
        "budget": {"lifetime_human_optimizer_tokens": 100, "total_optimizer_tokens": 1000},
        "randomness": {"chain_seed": 1},
        "environment": {"python": "3.10", "platform": "linux"},
        "horizon": 2,
        "status": "complete",
        "artifacts": [],
    }


def valid_chain_result() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": "fixture_valid",
        "policy": "joint",
        "chain_seed": 1,
        "budget_id": "budget-a",
        "generations_completed": 2,
        "valid": True,
        "metrics": [
            {"generation": 0, "human_nll": 3.1, "tail_retention": 0.92},
            {"generation": 1, "human_nll": 3.4, "tail_retention": 0.81},
        ],
        "consumed_human_tokens": 100,
        "consumed_total_tokens": 1000,
        "exclusion_reason": None,
    }


def write_run(
    directory: Path,
    manifest: dict[str, Any],
    chain_result: dict[str, Any],
    *,
    checkpoint_text: str | None = "checkpoint-bytes",
) -> Path:
    """Materialise a run directory, hashing any checkpoint it declares."""
    directory.mkdir(parents=True, exist_ok=True)

    if checkpoint_text is not None:
        checkpoint = directory / "checkpoint.txt"
        checkpoint.write_text(checkpoint_text, encoding="utf-8")
        digest = hashlib.sha256(checkpoint_text.encode("utf-8")).hexdigest()
        manifest.setdefault("artifacts", []).append(
            {"path": "checkpoint.txt", "sha256": digest}
        )

    (directory / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (directory / "chain_result.json").write_text(
        json.dumps(chain_result, indent=2), encoding="utf-8"
    )
    return directory


@pytest.fixture
def make_run(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a run directory with optional mutations."""
    counter = {"n": 0}

    def factory(
        mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
        mutate_result: Callable[[dict[str, Any]], None] | None = None,
        *,
        checkpoint_text: str | None = "checkpoint-bytes",
        name: str | None = None,
    ) -> Path:
        counter["n"] += 1
        manifest = valid_manifest()
        chain_result = valid_chain_result()
        if mutate_manifest is not None:
            mutate_manifest(manifest)
        if mutate_result is not None:
            mutate_result(chain_result)
        target = tmp_path / (name or f"run_{counter['n']}")
        return write_run(target, manifest, chain_result, checkpoint_text=checkpoint_text)

    return factory


@pytest.fixture
def valid_run(make_run: Callable[..., Path]) -> Path:
    """A run directory that must classify as valid."""
    return make_run(name="fixture_valid")
