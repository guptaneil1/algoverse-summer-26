"""Near-duplicate and exact overlap detection across data partitions."""

from __future__ import annotations

from human_data_budget.data.manifest import PartitionManifest


def _shingle(text: str, n: int = 5) -> frozenset[str]:
    if len(text) < n:
        return frozenset({text}) if text else frozenset()
    return frozenset(text[i : i + n] for i in range(len(text) - n + 1))


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    union = len(a | b)
    if union == 0:
        return 0.0
    return len(a & b) / union


def find_near_duplicate_pairs(
    manifest_a: PartitionManifest,
    manifest_b: PartitionManifest,
    threshold: float = 0.8,
    shingle_size: int = 5,
) -> list[tuple[str, str]]:
    """Return (id_a, id_b) pairs whose text Jaccard similarity meets the threshold."""
    shingles_a = {ex.example_id: _shingle(ex.text, shingle_size) for ex in manifest_a.examples}
    pairs: list[tuple[str, str]] = []
    for ex_b in manifest_b.examples:
        sh_b = _shingle(ex_b.text, shingle_size)
        for id_a, sh_a in shingles_a.items():
            if _jaccard(sh_a, sh_b) >= threshold:
                pairs.append((id_a, ex_b.example_id))
    return pairs


def check_near_duplicate_overlap(
    manifests: dict[str, PartitionManifest],
    threshold: float = 0.8,
) -> list[tuple[str, str, str, str]]:
    """Return (id_a, partition_a, id_b, partition_b) tuples for all near-duplicate pairs."""
    items = list(manifests.items())
    results: list[tuple[str, str, str, str]] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            name_a, manifest_a = items[i]
            name_b, manifest_b = items[j]
            for id_a, id_b in find_near_duplicate_pairs(manifest_a, manifest_b, threshold):
                results.append((id_a, name_a, id_b, name_b))
    return results
