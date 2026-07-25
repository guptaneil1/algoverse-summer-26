"""Run manifest lifecycle: creation, append-only status transitions, atomic writes.

Field shape matches ``schemas/run_manifest.schema.json`` and
``docs/interfaces/run_manifest.md``: scientific settings are immutable after
``running``; only status and the appended history may change afterward.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
_DEFAULT_ENVIRONMENT = {"python": ">=3.10", "hardware": "cpu-fixture"}


def new_manifest(
    config: dict[str, Any],
    *,
    policy_name: str,
    git_commit: str = "0" * 40,
    working_tree_clean: bool = True,
) -> dict[str, Any]:
    """Build the initial run manifest in ``planned`` status."""

    return {
        "schema_version": "1.0",
        "run_id": config["run_id"],
        "stage": config.get("stage", "fixture"),
        "git_commit": git_commit,
        "working_tree_clean": working_tree_clean,
        "model": config.get("model", _DEFAULT_MODEL),
        "data": config.get("data", _DEFAULT_DATA),
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
        "environment": config.get("environment", _DEFAULT_ENVIRONMENT),
        "horizon": config["horizon"],
        "status": "planned",
        "status_history": [{"status": "planned"}],
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


def write_manifest_atomic(manifest: dict[str, Any], path: Path) -> None:
    """Atomically write the manifest as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)
