"""Assemble one generation's training corpus from synthetic output plus rescued human text.

This is the join the recursion needs and the toy path never had: generation *g*'s
decoded corpus plus the specific human examples generation *g*'s policy selected,
written in the format upstream's ``train.py`` consumes.

**Why the policy cannot do this itself.** ``models.Candidate`` carries
``example_id``, ``human_token_count``, ``mode``, and ``undercoverage_score`` -- and
deliberately no text. Allocation is a decision over identifiers and token counts, so
the policy layer never touches corpus bytes. Materialising the decision into a
trainable file is this module's job, and it needs the rescue-candidate
``PartitionManifest`` to resolve identifiers back to text.

**Format.** Upstream writes and reads a JSON array of objects carrying a ``text``
key (``src/utils/utils.py`` and ``src/load_data.py``). Extra keys are preserved on
synthetic records so a corpus round-trips without losing detector scores.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from human_data_budget.data.manifest import Example, ManifestError, PartitionManifest
from human_data_budget.runner.upstream_driver import sha256_file


class CorpusAssemblyError(ValueError):
    """Raised when a generation's training corpus cannot be assembled."""


def _load_synthetic(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise CorpusAssemblyError(f"{path} is not a JSON array of records")
    for record in records:
        if "text" not in record:
            raise CorpusAssemblyError(f"{path} has a record with no 'text' key")
    return records


def _resolve(manifest: PartitionManifest, example_ids: Sequence[str]) -> list[Example]:
    index = {example.example_id: example for example in manifest.examples}
    missing = [eid for eid in example_ids if eid not in index]
    if missing:
        raise CorpusAssemblyError(
            f"selected example_ids absent from the {manifest.partition!r} manifest: "
            f"{sorted(missing)}. Refusing to drop them silently -- a policy that spent "
            "budget on an example must train on that example, or budget matching is void."
        )
    return [index[eid] for eid in example_ids]


def assemble_training_corpus(
    *,
    synthetic_corpus: Path | str | None,
    rescue_manifest: PartitionManifest,
    selected_example_ids: Sequence[str],
    output_path: Path | str,
    generation: int,
    selection_policy: str,
    selection_scores: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Write generation ``generation``'s training corpus and its provenance sidecar.

    ``synthetic_corpus`` is ``None`` at generation 0, where no prior decode exists and
    the corpus is human-only.

    Returns a serializable summary. ``human_token_count`` is summed from the
    manifest's frozen ``token_count`` values, which are non-padding tokens per
    optimizer presentation under the frozen tokenizer -- the same quantity the policy
    budgeted against, so the ledger and the allocation cannot drift apart.
    """
    output_path = Path(output_path)
    synthetic = _load_synthetic(Path(synthetic_corpus) if synthetic_corpus else None)

    try:
        rescued = _resolve(rescue_manifest, selected_example_ids)
    except ManifestError as error:  # pragma: no cover - defensive
        raise CorpusAssemblyError(str(error)) from error

    records: list[dict[str, Any]] = list(synthetic)
    provenance: list[dict[str, Any]] = []
    scores = dict(selection_scores or {})

    for example in rescued:
        if not example.text:
            raise CorpusAssemblyError(
                f"example {example.example_id!r} carries no text. A manifest is a "
                "reference to a corpus; load it with the text populated before assembly."
            )
        records.append({"text": example.text})
        provenance.append({
            "example_id": example.example_id,
            "content_hash": example.content_hash,
            "source": example.source,
            "source_revision": example.source_revision,
            "origin": example.origin,
            "mode": example.mode,
            "generation": generation,
            "selection_policy": selection_policy,
            "selection_score": scores.get(example.example_id),
            "selected": True,
            "token_count": example.token_count,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=4), encoding="utf-8")

    provenance_path = output_path.with_name(f"{output_path.stem}_provenance.json")
    provenance_path.write_text(
        json.dumps({
            "generation": generation,
            "selection_policy": selection_policy,
            "synthetic_record_count": len(synthetic),
            "human_record_count": len(rescued),
            "examples": provenance,
        }, indent=2),
        encoding="utf-8",
    )

    return {
        "generation": generation,
        "corpus_path": str(output_path),
        "corpus_sha256": sha256_file(output_path),
        "provenance_path": str(provenance_path),
        "synthetic_record_count": len(synthetic),
        "human_record_count": len(rescued),
        "human_token_count": sum(example.token_count for example in rescued),
    }
