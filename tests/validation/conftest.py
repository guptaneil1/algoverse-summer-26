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
    """One partition provenance entry.

    ``text`` is emitted as well as hashed: the auditor's near-duplicate check
    compares text, and an entry without it yields
    ``LIMIT_NEAR_DUPLICATE_NOT_CHECKED`` rather than a clean pass. A fixture that
    is meant to represent a fully certifiable run therefore has to carry it.
    """
    return {
        "stable_id": stable_id,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_dataset": "toy/v1",
        "origin": origin,
        "text": text,
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


def write_batch_records(directory: Path, chain_result: dict[str, Any]) -> None:
    """Write realized batch records consistent with the result's declared ledger.

    The auditor recomputes the token ledger from these records rather than
    trusting the declaration, so a fixture without them is classified
    ``valid_with_limitation`` (``LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE``) no matter
    how clean it otherwise is.

    Records are *derived from* each fixture's own declared totals rather than
    fixed, so mutating a fixture's consumed tokens keeps its batches in step and
    changes only the code under test. A fixture that wants a ledger mismatch
    writes its own records — see
    ``tests/validation/test_token_ledger_recompute.py``.
    """
    human = chain_result.get("consumed_human_tokens")
    total = chain_result.get("consumed_total_tokens")
    if not isinstance(human, int) or not isinstance(total, int):
        return
    if human < 0 or total < human:
        # Impossible-accounting fixtures: leave the ledger unrecomputable rather
        # than inventing batches that cannot exist.
        return

    rows: list[tuple[list[int], str]] = []
    if human:
        rows.append(([1] * human, "human"))
    if total - human:
        rows.append(([1] * (total - human), "synthetic"))
    if not rows:
        return

    record = {
        "attention_mask": [mask for mask, _ in rows],
        "origins": [origin for _, origin in rows],
    }
    with (directory / "batch_records.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(record) + "\n")


def write_run(
    directory: Path,
    manifest: dict[str, Any],
    chain_result: dict[str, Any],
    *,
    checkpoint_text: str | None = "checkpoint-bytes",
    batch_records: bool = True,
) -> Path:
    """Materialise a run directory, hashing any checkpoint it declares."""
    directory.mkdir(parents=True, exist_ok=True)

    if batch_records:
        write_batch_records(directory, chain_result)

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
        batch_records: bool = True,
    ) -> Path:
        counter["n"] += 1
        manifest = valid_manifest()
        chain_result = valid_chain_result()
        if mutate_manifest is not None:
            mutate_manifest(manifest)
        if mutate_result is not None:
            mutate_result(chain_result)
        target = tmp_path / (name or f"run_{counter['n']}")
        return write_run(
            target,
            manifest,
            chain_result,
            checkpoint_text=checkpoint_text,
            batch_records=batch_records,
        )

    return factory


@pytest.fixture
def valid_run(make_run: Callable[..., Path]) -> Path:
    """A run directory that must classify as valid."""
    return make_run(name="fixture_valid")
