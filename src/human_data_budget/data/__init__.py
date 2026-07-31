"""Data identity, separation, provenance, and token-accounting utilities."""

from human_data_budget.data.hashing import content_hash, normalize_text
from human_data_budget.data.manifest import (
    Example,
    ManifestError,
    PartitionManifest,
    ProvenanceError,
    load_manifest_from_jsonl,
)
from human_data_budget.data.overlap import check_near_duplicate_overlap, find_near_duplicate_pairs
from human_data_budget.data.token_accounting import consumed_tokens

__all__ = [
    "Example",
    "ManifestError",
    "PartitionManifest",
    "ProvenanceError",
    "check_near_duplicate_overlap",
    "consumed_tokens",
    "content_hash",
    "find_near_duplicate_pairs",
    "load_manifest_from_jsonl",
    "normalize_text",
]
