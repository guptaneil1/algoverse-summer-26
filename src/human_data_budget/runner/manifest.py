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

from human_data_budget.data.manifest import load_manifest_from_jsonl
from human_data_budget.data.separation import assert_disjoint

#: Partition vocabulary required by the validator (``validation/audit.py``) and
#: documented in ``docs/evaluation/week3_data_evaluation_appendix.md``. This is the
#: canonical set for the run manifest.
#:
#: Note for @Neil: ``data/manifest.py`` uses a different vocabulary
#: (``base_train``/``prompts``/``test`` with ``example_id``/``source``). The runner
#: translates via ``_DATA_MODULE_PARTITIONS`` and ``_load_partition_manifests``
#: rather than editing either module. See ``docs/interfaces/run_manifest.md``.
MANIFEST_PARTITIONS: tuple[str, ...] = (
    "base_human_train",
    "rescue_candidates",
    "generation_prompts",
    "validation",
    "final_human_test",
)

#: Per-example provenance required by ``validation/audit.py``. A missing field is an
#: invalidating condition, so the runner refuses to build a manifest without them
#: rather than discovering it after a chain has burned compute.
PROVENANCE_FIELDS: tuple[str, ...] = (
    "stable_id",
    "content_hash",
    "source_dataset",
    "origin",
)

#: Canonical partition name -> the name ``data/manifest.py`` accepts.
_DATA_MODULE_PARTITIONS: dict[str, str] = {
    "base_human_train": "base_train",
    "rescue_candidates": "rescue_candidates",
    "generation_prompts": "prompts",
    "validation": "validation",
    "final_human_test": "test",
}

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


class ManifestProvenanceError(ValueError):
    """Raised when a declared provenance source is unusable.

    Raised at manifest creation, before a chain launches. A run that reaches the
    validator without provenance is spent compute that cannot be certified, and the
    frozen rules do not permit back-filling provenance after the fact.
    """


def _check_records(partition: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ``records`` if every one carries complete provenance, else raise."""

    if not records:
        raise ManifestProvenanceError(
            f"partition {partition!r} declares a provenance source but resolved to zero "
            "examples; refusing to record an empty partition"
        )
    for index, record in enumerate(records):
        missing = [field for field in PROVENANCE_FIELDS if not record.get(field)]
        if missing:
            raise ManifestProvenanceError(
                f"{partition}[{index}] is missing provenance {sorted(missing)}; "
                f"every example needs {list(PROVENANCE_FIELDS)}"
            )
    return records


def _load_partition_manifests(sources: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """Load canonical partitions from JSONL manifests owned by ``data/``.

    Translates the canonical partition name to the one ``data/manifest.py`` accepts,
    then translates each loaded ``Example`` into the validator's field names.
    """

    partitions: dict[str, list[dict[str, Any]]] = {}
    for partition, path in sources.items():
        if partition not in MANIFEST_PARTITIONS:
            raise ManifestProvenanceError(
                f"unknown partition {partition!r}; expected one of {list(MANIFEST_PARTITIONS)}"
            )
        target = Path(path)
        if not target.is_file():
            raise ManifestProvenanceError(
                f"partition {partition!r} declares manifest {path!r}, which does not exist"
            )
        loaded = load_manifest_from_jsonl(target, _DATA_MODULE_PARTITIONS[partition])
        partitions[partition] = _check_records(
            partition,
            [
                {
                    "stable_id": example.example_id,
                    "content_hash": example.content_hash,
                    "source_dataset": example.source,
                    "origin": example.origin,
                }
                for example in loaded.examples
            ],
        )
    return partitions


def build_partitions(data_config: dict[str, Any]) -> dict[str, list[dict[str, Any]]] | None:
    """Resolve the manifest's ``data.partitions`` block from a config's data block.

    Two sources, checked in order: inline ``partitions`` records already in canonical
    form, or ``partition_manifests`` mapping canonical partition names to JSONL paths.

    Returns ``None`` when neither is declared. That is deliberate: a run with no
    provenance source must keep classifying ``invalid`` rather than silently passing.
    """

    inline = data_config.get("partitions")
    sources = data_config.get("partition_manifests")

    if inline and sources:
        raise ManifestProvenanceError(
            "data declares both 'partitions' and 'partition_manifests'; "
            "pick one provenance source so the manifest has a single origin"
        )

    if inline:
        unknown = [name for name in inline if name not in MANIFEST_PARTITIONS]
        if unknown:
            raise ManifestProvenanceError(
                f"unknown partition(s) {sorted(unknown)}; "
                f"expected names from {list(MANIFEST_PARTITIONS)}"
            )
        partitions = {
            partition: _check_records(partition, list(records))
            for partition, records in inline.items()
        }
    elif sources:
        partitions = _load_partition_manifests(sources)
    else:
        return None

    # Fail before launch on a forbidden overlap rather than after the chain runs.
    assert_disjoint(
        {
            partition: [record["content_hash"] for record in records]
            for partition, records in partitions.items()
        }
    )
    return partitions


def new_manifest(
    config: dict[str, Any],
    *,
    policy_name: str,
    git_commit: str = "0" * 40,
    working_tree_clean: bool = True,
) -> dict[str, Any]:
    """Build the initial run manifest in ``planned`` status."""

    data = dict(config.get("data", _DEFAULT_DATA))
    partitions = build_partitions(data)
    if partitions is None:
        data.pop("partitions", None)
    else:
        data["partitions"] = partitions
    data.pop("partition_manifests", None)

    return {
        "schema_version": "1.0",
        "run_id": config["run_id"],
        "stage": config.get("stage", "fixture"),
        "git_commit": git_commit,
        "working_tree_clean": working_tree_clean,
        "model": config.get("model", _DEFAULT_MODEL),
        "data": data,
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
    """Atomically write the manifest as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)
