"""Run manifest lifecycle: creation, append-only status transitions, atomic writes.

Field shape matches ``schemas/run_manifest.schema.json`` and
``docs/interfaces/run_manifest.md``: scientific settings are immutable after
``running``; only status and the appended history may change afterward.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

from human_data_budget.runner.provenance import (
    build_partition_provenance,
    partition_sources_from_config,
)

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"running", "failed", "invalid"},
    "running": {"complete", "failed", "invalid"},
    "complete": set(),
    "failed": set(),
    "invalid": set(),
}

_DEFAULT_MODEL = {
    "identifier": "toy-model",
    "revision": "fixture-v1",
    "tokenizer_revision": "fixture-v1",
}
_DEFAULT_DATA = {
    "train_manifest": "data/fixtures/toy_corpus.jsonl",
    "train_manifest_sha256": "fixture",
}


def _default_environment() -> dict[str, str]:
    return {"python": platform.python_version(), "hardware": "cpu-fixture"}


def _data_block(config: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Assemble the manifest ``data`` block, including per-example provenance.

    ``PROTOCOL.md`` §3 requires per-example provenance for the five partitions,
    and the auditor classifies a run ``invalid`` with
    ``SEPARATION_MISSING_PROVENANCE`` without it. The block is emitted only when
    the config declares partition sources: a config that declares none produces
    no block and stays honestly uncertifiable, rather than gaining a synthesised
    provenance record that no data supports.
    """

    data = dict(config.get("data", _DEFAULT_DATA))
    sources = partition_sources_from_config(config)
    if sources:
        data["partitions"] = build_partition_provenance(sources, root=data_root)
    return data


def new_manifest(
    config: dict[str, Any],
    *,
    policy_name: str,
    git_commit: str = "0" * 40,
    working_tree_clean: bool = True,
    data_root: Path = Path("."),
) -> dict[str, Any]:
    """Build the initial run manifest in ``planned`` status.

    ``data_root`` resolves relative partition-source paths declared in the
    config; it defaults to the process working directory, which is the
    repository root for the documented ``run_chain.sh`` invocation.
    """

    return {
        "schema_version": "1.0",
        "run_id": config["run_id"],
        "stage": config.get("stage", "fixture"),
        "git_commit": git_commit,
        "working_tree_clean": working_tree_clean,
        "model": config.get("model", _DEFAULT_MODEL),
        "data": _data_block(config, data_root),
        "policy": {
            "name": policy_name,
            "config": config.get("policy_config", "toy_cpu.json"),
            "config_sha256": config.get("policy_config_sha256", "fixture"),
        },
        "budget": {
            "lifetime_human_optimizer_tokens": config["lifetime_human_budget"],
            "total_optimizer_tokens": config["total_optimizer_tokens"],
        },
        "randomness": {"chain_seed": config["chain_seed"]},
        "environment": config.get("environment", _default_environment()),
        "horizon": config["horizon"],
        "status": "planned",
        "status_history": [{"status": "planned"}],
        "current_generation": None,
        "failure": None,
    }


def transition_status(manifest: dict[str, Any], new_status: str) -> dict[str, Any]:
    """Return a copy of ``manifest`` moved to ``new_status``.

    Appends to status history rather than erasing earlier state, and rejects
    transitions not reachable from the current status.
    """

    current = manifest["status"]
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(f"illegal status transition: {current} -> {new_status}")
    updated = dict(manifest)
    updated["status"] = new_status
    updated["status_history"] = [*manifest.get("status_history", []), {"status": new_status}]
    return updated


def record_generation(manifest: dict[str, Any], generation: int) -> dict[str, Any]:
    """Return a copy of ``manifest`` with ``current_generation`` advanced."""

    if generation < 0:
        raise ValueError("generation must be non-negative")
    updated = dict(manifest)
    updated["current_generation"] = generation
    return updated


def attach_failure(manifest: dict[str, Any], failure: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``manifest`` recording structured failure info.

    ``failure`` is expected to be a ``FailureState.as_dict()`` payload
    (``human_data_budget.runner.failure``), kept generic here to avoid a
    manifest -> failure import for a shape check alone.
    """

    updated = dict(manifest)
    updated["failure"] = failure
    return updated


def write_manifest_atomic(manifest: dict[str, Any], path: Path) -> None:
    """Atomically write the manifest as JSON with LF line endings.

    The auditor records ``sha256(run_manifest.json)`` as the run's provenance
    hash. ``Path.write_text`` translates ``\\n`` to ``\\r\\n`` on Windows, so the
    same logical run hashed to two different values depending on the operating
    system that produced it. ``newline="\\n"`` pins the bytes, matching the
    ``.gitattributes`` policy for content-hashed artifacts.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")
    tmp_path.replace(path)
