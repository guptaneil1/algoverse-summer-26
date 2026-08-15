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
    """One data example with stable identity and provenance."""

    example_id: str
    text: str
    origin: str
    mode: str
    source: str
    source_offset: int
    token_count: int
    content_hash: str

    @classmethod
    def from_dict(cls, record: dict) -> Example:
        """Build an Example from a manifest record.

        Two record shapes are accepted. A text-bearing record (fixtures, freshly
        prepared data) carries ``text`` and its hash is computed here. A frozen,
        text-free record (the immutable manifests this policy commits to git per
        ``data/README.md`` — raw text is never committed) carries a precomputed
        ``content_hash`` instead. If both are present they must agree, so a
        frozen manifest can never silently drift from the text it was built from.
        """
        missing_provenance = _PROVENANCE_FIELDS - record.keys()
        if missing_provenance:
            raise ProvenanceError(
                f"Missing provenance fields: {sorted(missing_provenance)}"
            )
        missing = _REQUIRED_FIELDS - record.keys()
        if missing:
            raise ManifestError(f"Missing required fields: {sorted(missing)}")
        text = record.get("text")
        provided_hash = record.get("content_hash")
        if text is not None:
            resolved_hash = content_hash(text)
            if provided_hash is not None and provided_hash != resolved_hash:
                raise ManifestError(
                    f"content_hash mismatch for {record.get('example_id')!r}: "
                    f"recorded {provided_hash!r} does not match text-derived {resolved_hash!r}"
                )
            resolved_text = text
        elif provided_hash is not None:
            resolved_hash = provided_hash
            resolved_text = ""
        else:
            raise ManifestError("record must include either 'text' or a precomputed 'content_hash'")
        return cls(
            example_id=record["example_id"],
            text=resolved_text,
            origin=record["origin"],
            mode=record["mode"],
            source=record["source"],
            source_offset=int(record["source_offset"]),
            token_count=int(record["token_count"]),
            content_hash=resolved_hash,
        )


def _manifest_hash(examples: list[Example]) -> str:
    h = hashlib.sha256()
    for ex in sorted(examples, key=lambda e: e.example_id):
        h.update(f"{ex.example_id}:{ex.content_hash}\n".encode())
    return h.hexdigest()


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
        return {
            "partition": self.partition,
            "manifest_hash": self.manifest_hash,
            "examples": [
                {
                    "example_id": e.example_id,
                    "content_hash": e.content_hash,
                    "origin": e.origin,
                    "mode": e.mode,
                    "source": e.source,
                    "source_offset": e.source_offset,
                    "token_count": e.token_count,
                }
                for e in self.examples
            ],
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
