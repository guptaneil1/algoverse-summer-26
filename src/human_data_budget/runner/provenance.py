"""Per-example partition provenance for the run manifest.

The auditor (``human_data_budget.validation.audit.check_separation``) verifies
partition disjointness and per-example provenance, and can only do so if the run
manifest actually carries the per-example record. A manifest without it is
classified ``invalid`` with ``SEPARATION_MISSING_PROVENANCE`` — correctly, since
separation is unverifiable rather than verified-absent.

**Partial coverage of PROTOCOL.md §3, stated plainly.** §3 "Provenance" requires
every training example to retain eight things: stable ID; content hash; source
dataset *and revision*; human or synthetic origin; recursive generation;
selection policy and score; whether it was selected; and number of optimizer
presentations.

This module emits the four the auditor checks — ``stable_id``,
``content_hash``, ``source_dataset``, ``origin`` — plus ``source_revision`` when
the source carries one, and ``text`` for the near-duplicate comparison. The four
remaining fields (generation, selection policy and score, selected, optimizer
presentations) are training-time facts that a partition manifest cannot know:
they are produced when a policy selects an example and an optimizer consumes it.
``human_data_budget.data.manifest.validate_training_provenance`` enforces those
at that point instead. Closing the gap end to end means recording selection and
presentation counts into the manifest as a chain runs, which is the runner
owner's work and is **not** done here.

Emitting these four satisfies the auditor and `docs/audits/week3_execution_required.md`
§1.2, which names exactly these four. It does not by itself satisfy §3.

Provenance is built **only** from declared partition sources. When a config
declares none, no block is emitted and the run stays uncertifiable. Synthesising
a provenance block the data does not support would convert an honest "cannot be
verified" into a false "verified", which is the one failure mode this module
exists to prevent.

Dependency direction (``docs/ARCHITECTURE.md``): ``runner`` may import ``data``.
The reverse is forbidden.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from human_data_budget.data.manifest import load_manifest_from_jsonl

# Partition names as they appear in the run manifest, matching
# PROTOCOL.md §3 "Data separation" and the auditor's FORBIDDEN_PARTITION_PAIRS.
RUN_MANIFEST_PARTITIONS = (
    "base_human_train",
    "rescue_candidates",
    "generation_prompts",
    "validation",
    "final_human_test",
)

# The data layer names the same five partitions differently
# (``human_data_budget.data.manifest.PARTITIONS``). That vocabulary is a frozen
# cross-workstream contract owned by the data workstream, so it is translated
# here rather than changed at either end.
_DATA_LAYER_PARTITION = {
    "base_human_train": "base_train",
    "rescue_candidates": "rescue_candidates",
    "generation_prompts": "prompts",
    "validation": "validation",
    "final_human_test": "test",
}


class PartitionSourceError(ValueError):
    """Raised when a declared partition source cannot be resolved or loaded."""


def project_root() -> Path:
    """Locate the repository root by walking up to the directory holding pyproject.toml.

    Partition sources are declared repository-relative, so resolving them against
    the process working directory would make a run's provenance depend on where
    the command happened to be typed. Deriving the root from ``__file__`` matches
    how the rest of the repository locates itself (for example
    ``scripts/validate_run.py``'s ``ROOT``), and keeps the chain runnable from any
    directory. Falls back to the working directory when no marker is found.
    """

    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path()


def _resolve(source: str | Path, root: Path) -> Path:
    candidate = Path(source)
    return candidate if candidate.is_absolute() else root / candidate


def build_partition_provenance(
    sources: dict[str, str | Path],
    *,
    root: Path | None = None,
    include_text: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """Build the manifest ``data.partitions`` block from declared sources.

    ``sources`` maps a run-manifest partition name to a JSONL partition file.
    Every content hash is recomputed from the example text by
    ``human_data_budget.data.hashing.content_hash`` rather than copied from the
    source record, so a source whose recorded hash disagrees with its own text is
    rejected by ``Example.from_dict`` instead of being propagated into the
    manifest.

    ``include_text`` controls whether each entry carries its example text. The
    auditor's near-duplicate check needs text; exact-hash separation does not.
    Emitting it is appropriate for small fixture partitions and is a size
    decision — not a correctness one — for a full corpus.
    """

    root = project_root() if root is None else root
    unknown = sorted(set(sources) - set(RUN_MANIFEST_PARTITIONS))
    if unknown:
        raise PartitionSourceError(
            f"unknown partition name(s) {unknown}; expected a subset of "
            f"{list(RUN_MANIFEST_PARTITIONS)}"
        )

    partitions: dict[str, list[dict[str, Any]]] = {}
    for name in RUN_MANIFEST_PARTITIONS:
        if name not in sources:
            continue
        path = _resolve(sources[name], root)
        if not path.is_file():
            raise PartitionSourceError(
                f"partition {name!r} declares source {path}, which does not exist"
            )
        manifest = load_manifest_from_jsonl(path, _DATA_LAYER_PARTITION[name])

        entries: list[dict[str, Any]] = []
        for example in manifest.examples:
            entry: dict[str, Any] = {
                "stable_id": example.example_id,
                "content_hash": example.content_hash,
                "source_dataset": example.source,
                "origin": example.origin,
            }
            if example.source_revision:
                entry["source_revision"] = example.source_revision
            if include_text:
                entry["text"] = example.text
            entries.append(entry)
        partitions[name] = entries

    return partitions


def partition_sources_from_config(config: dict[str, Any]) -> dict[str, str | Path]:
    """Read declared partition sources from a run config.

    Returns an empty mapping when the config declares none, which is the signal
    to emit no provenance block at all.
    """

    data_block = config.get("data")
    if not isinstance(data_block, dict):
        return {}
    sources = data_block.get("partition_sources")
    if not isinstance(sources, dict):
        return {}
    return dict(sources)
