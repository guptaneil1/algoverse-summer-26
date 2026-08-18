"""Partition manifests: stable IDs, content hashes, provenance, and JSONL loading."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from human_data_budget.data.hashing import content_hash

PARTITIONS: frozenset[str] = frozenset(
    {"base_train", "rescue_candidates", "prompts", "validation", "test"}
)

_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"example_id", "origin", "mode", "source", "source_offset", "token_count"}
)
_PROVENANCE_FIELDS: frozenset[str] = frozenset({"source", "source_offset"})


class ManifestError(ValueError):
    """Raised for malformed manifest records."""


class ProvenanceError(ManifestError):
    """Raised when required provenance fields are missing or invalid."""


@dataclass(frozen=True)
class Example:
    """One data example with stable identity and provenance.

    The first eight fields are partition-time identity. The trailing optional
    fields are training-time provenance required by ``PROTOCOL.md`` §3; they are
    optional on the dataclass because a base-training example read from a frozen
    partition has not yet been selected by any policy or seen by any optimizer.
    Once an example enters training, ``validate_training_provenance`` requires
    all of them.
    """

    example_id: str
    text: str
    origin: str
    mode: str
    source: str
    source_offset: int
    token_count: int
    content_hash: str
    source_revision: str | None = None
    # Non-padding tokens under the frozen model tokenizer. Distinct from
    # ``token_count``, which is the whitespace word count the frozen
    # ``article_length_quantile`` mode definition is built on
    # (``docs/data/mode_definition_audit.md``). One field cannot serve both: mode
    # assignment is frozen on whitespace, while ``PROTOCOL.md`` §3 requires budget
    # accounting in tokens the optimizer actually consumes. See FAILURE_LOG F-010b.
    optimizer_token_count: int | None = None
    generation: int | None = None
    selection_policy: str | None = None
    selection_score: float | None = None
    selected: bool | None = None
    optimizer_presentations: int = 0

    @classmethod
    def from_dict(cls, record: dict) -> Example:
        missing_provenance = _PROVENANCE_FIELDS - record.keys()
        if missing_provenance:
            raise ProvenanceError(
                f"Missing provenance fields: {sorted(missing_provenance)}"
            )
        missing = _REQUIRED_FIELDS - record.keys()
        if missing:
            raise ManifestError(f"Missing required fields: {sorted(missing)}")

        # Round-trip fidelity. `to_dict` deliberately emits `content_hash` but not
        # `text`: a manifest is a reference to a corpus, not a copy of it. Before
        # this branch, reloading a serialized manifest recomputed the hash from an
        # absent text, yielding the hash of "" for every example and silently
        # changing the manifest's identity.
        text = record.get("text")
        supplied_hash = record.get("content_hash")
        if text is None and supplied_hash is None:
            raise ManifestError(
                "record must carry either 'text' or a precomputed 'content_hash'"
            )
        if text is None:
            resolved_hash = supplied_hash
        else:
            resolved_hash = content_hash(text)
            if supplied_hash is not None and supplied_hash != resolved_hash:
                raise ManifestError(
                    f"content_hash mismatch for {record['example_id']!r}: "
                    f"recorded {supplied_hash}, computed {resolved_hash}"
                )

        presentations = int(record.get("optimizer_presentations", 0))
        if presentations < 0:
            raise ManifestError("optimizer_presentations must not be negative")
        optimizer_tokens = record.get("optimizer_token_count")
        if optimizer_tokens is not None:
            optimizer_tokens = int(optimizer_tokens)
            if optimizer_tokens <= 0:
                raise ManifestError("optimizer_token_count must be positive")
        selection_score = record.get("selection_score")
        return cls(
            example_id=record["example_id"],
            text=text or "",
            origin=record["origin"],
            mode=record["mode"],
            source=record["source"],
            source_offset=int(record["source_offset"]),
            token_count=int(record["token_count"]),
            content_hash=resolved_hash,
            source_revision=record.get("source_revision"),
            optimizer_token_count=optimizer_tokens,
            generation=(
                None if record.get("generation") is None else int(record["generation"])
            ),
            selection_policy=record.get("selection_policy"),
            selection_score=(None if selection_score is None else float(selection_score)),
            selected=record.get("selected"),
            optimizer_presentations=presentations,
        )


def validate_training_provenance(example: Example) -> None:
    """Require the full ``PROTOCOL.md`` §3 provenance set for a trained-on example.

    PROTOCOL.md §3 lists eight fields that every training example must retain
    *after shuffling and batching*: stable ID, content hash, source dataset and
    revision, human/synthetic origin, recursive generation, selection policy and
    score, whether it was selected, and number of optimizer presentations.

    Partition-time identity covers the first three. This function enforces the
    rest, and is the check to call at the point an example is handed to the
    optimizer — not when it is read from a manifest.
    """
    missing: list[str] = []
    if not example.source_revision:
        missing.append("source_revision")
    if example.generation is None:
        missing.append("generation")
    if not example.selection_policy:
        missing.append("selection_policy")
    if example.selection_score is None:
        missing.append("selection_score")
    if example.selected is None:
        missing.append("selected")
    if missing:
        raise ProvenanceError(
            f"Example {example.example_id!r} is missing training provenance: {sorted(missing)}"
        )
    if example.selected and example.optimizer_presentations < 1:
        raise ProvenanceError(
            f"Example {example.example_id!r} is marked selected but records "
            "zero optimizer presentations"
        )
    if not example.selected and example.optimizer_presentations:
        raise ProvenanceError(
            f"Example {example.example_id!r} is marked unselected but records "
            f"{example.optimizer_presentations} optimizer presentations"
        )


def _manifest_hash(examples: list[Example]) -> str:
    """Content hash identifying one partition.

    Records are framed with ``json.dumps`` rather than ``f"{id}:{hash}\\n"``
    concatenation. Unframed concatenation lets a crafted ``example_id``
    containing ``:`` or a newline forge record boundaries, so two different
    manifests can hash identically — a partition could then be swapped without
    changing its recorded identity.

    Duplicate ``example_id`` values are rejected rather than hashed, because a
    partition with two records sharing an id has no well-defined membership.
    """

    ids = [example.example_id for example in examples]
    duplicates = sorted({name for name in ids if ids.count(name) > 1})
    if duplicates:
        raise ManifestError(f"duplicate example_id values in partition: {duplicates}")

    digest = hashlib.sha256()
    # Sort on the full (id, hash) pair: id alone is not a total order once two
    # records can share an id, and a non-total order makes the hash unstable.
    for example in sorted(examples, key=lambda e: (e.example_id, e.content_hash)):
        digest.update(
            json.dumps([example.example_id, example.content_hash]).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


@dataclass(frozen=True)
class PartitionManifest:
    """Immutable collection of examples for one data partition."""

    partition: str
    examples: tuple[Example, ...]
    manifest_hash: str

    @classmethod
    def from_examples(cls, partition: str, examples: list[Example]) -> PartitionManifest:
        if partition not in PARTITIONS:
            raise ManifestError(
                f"Unknown partition {partition!r}. Must be one of {sorted(PARTITIONS)}"
            )
        return cls(
            partition=partition,
            examples=tuple(examples),
            manifest_hash=_manifest_hash(examples),
        )

    def to_dict(self) -> dict:
        records = []
        for e in self.examples:
            record = {
                "example_id": e.example_id,
                "content_hash": e.content_hash,
                "origin": e.origin,
                "mode": e.mode,
                "source": e.source,
                "source_offset": e.source_offset,
                "token_count": e.token_count,
            }
            # Training-time provenance is emitted only when populated, so frozen
            # partition manifests keep stable hashes and stable serialized shape.
            for field_name in (
                "source_revision",
                "optimizer_token_count",
                "generation",
                "selection_policy",
                "selection_score",
                "selected",
            ):
                value = getattr(e, field_name)
                if value is not None:
                    record[field_name] = value
            if e.optimizer_presentations:
                record["optimizer_presentations"] = e.optimizer_presentations
            records.append(record)
        return {
            "partition": self.partition,
            "manifest_hash": self.manifest_hash,
            "examples": records,
        }


def load_manifest_from_jsonl(path: str | Path, partition: str) -> PartitionManifest:
    """Load and validate a partition manifest from a JSONL file."""
    path = Path(path)
    examples: list[Example] = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ManifestError(
                    f"Invalid JSON on line {lineno} of {path}: {exc}"
                ) from exc
            try:
                examples.append(Example.from_dict(record))
            except ProvenanceError as exc:
                raise ProvenanceError(
                    f"Provenance error on line {lineno} of {path}: {exc}"
                ) from exc
            except ManifestError as exc:
                raise ManifestError(
                    f"Manifest error on line {lineno} of {path}: {exc}"
                ) from exc
    return PartitionManifest.from_examples(partition, examples)
