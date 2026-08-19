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

**Committed manifests carry no text.** ``data/README.md`` forbids raw corpora on a
committed path, and ``scripts/build_wikitext103_manifests.py`` writes hash-only
records accordingly. Text is therefore rehydrated at assembly time through a
``resolve_text`` callable and checked against the frozen ``content_hash`` before it
can enter training. A mismatch is fatal: it means the corpus behind the manifest is
not the corpus the manifest describes.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from human_data_budget.data.hashing import content_hash
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


def _optimizer_tokens(example: Example) -> int:
    """The example's price in the unit the policy budgets in.

    Refuses to fall back to ``token_count``. That field is a whitespace word count
    (``FAILURE_LOG.md`` F-010b); substituting it here would make the ledger disagree
    with the allocation by the BPE ratio and make a fully-spent budget look
    under-spent.
    """
    if example.optimizer_token_count is None:
        raise CorpusAssemblyError(
            f"example {example.example_id!r} has no optimizer_token_count. Run "
            "scripts/add_optimizer_token_counts.py. Falling back to token_count "
            "would price this spend in words -- see FAILURE_LOG.md F-010b."
        )
    return int(example.optimizer_token_count)


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



def _text_for(example: Example, resolve_text: Callable[[Example], str] | None) -> str:
    """Return this example's text, verified against its frozen content hash.

    Prefers text already on the record (fixtures and in-memory manifests) and falls
    back to ``resolve_text`` for the hash-only manifests the builder commits. The
    hash check runs either way, so a resolver reading the wrong revision, offset, or
    preprocessing is caught here rather than silently training on the wrong bytes.
    """
    text = example.text
    if not text:
        if resolve_text is None:
            raise CorpusAssemblyError(
                f"example {example.example_id!r} carries no text and no resolve_text "
                "was supplied. Committed manifests are hash-only by policy "
                "(data/README.md), so assembly needs a resolver for the pinned source."
            )
        text = resolve_text(example)
    if not text:
        raise CorpusAssemblyError(f"resolved empty text for {example.example_id!r}")
    observed = content_hash(text)
    if observed != example.content_hash:
        raise CorpusAssemblyError(
            f"content hash mismatch for {example.example_id!r}: manifest records "
            f"{example.content_hash}, resolved text hashes to {observed}. The corpus "
            "behind this manifest is not the corpus the manifest describes."
        )
    return text


def assemble_training_corpus(
    *,
    synthetic_corpus: Path | str | None,
    rescue_manifest: PartitionManifest,
    selected_example_ids: Sequence[str],
    output_path: Path | str,
    generation: int,
    selection_policy: str,
    selection_scores: Mapping[str, float] | None = None,
    resolve_text: Callable[[Example], str] | None = None,
    corpus_record_budget: int | None = None,
) -> dict[str, Any]:
    """Write generation ``generation``'s training corpus and its provenance sidecar.

    ``synthetic_corpus`` is ``None`` at generation 0, where no prior decode exists and
    the corpus is human-only.

    ``corpus_record_budget`` implements **displacement** (``DECISIONS.md`` P-011): the
    assembled corpus holds at most that many records, and rescued human examples
    *replace* synthetic ones rather than being appended to them. Passing ``None``
    restores the additive behaviour the first pilot ran under, retained only so that
    run's artifacts stay reproducible.

    Why displacement is the specification. Under addition, an arm that spends its
    human budget trains on strictly more data than one that does not, so every contrast
    confounds allocation strategy with training volume -- including the control
    contrast, where "spending helps" cannot be separated from "more data helps". The
    executed pilot measured realised totals spanning 2.26% across arms while human
    spend matched to 0.04% (``FAILURE_LOG.md`` F-021, F-021a), which is that confound
    appearing in practice. Displacement makes ``PROTOCOL.md`` §4's total-token
    condition hold by construction rather than by luck.

    Returns a serializable summary. ``human_token_count`` is summed from
    ``optimizer_token_count`` -- the same field the policy prices candidates in
    (``DECISIONS.md`` P-002) -- so the ledger and the allocation cannot drift apart.
    Summing ``token_count`` instead would under-report every spend by the BPE ratio,
    measured at 1.096-1.318x per example in ``FAILURE_LOG.md`` F-010b, and the chain
    would appear to under-spend a budget it had in fact allocated in full.
    """
    output_path = Path(output_path)
    synthetic = _load_synthetic(Path(synthetic_corpus) if synthetic_corpus else None)

    try:
        rescued = _resolve(rescue_manifest, selected_example_ids)
    except ManifestError as error:  # pragma: no cover - defensive
        raise CorpusAssemblyError(str(error)) from error

    displaced = 0
    if corpus_record_budget is not None:
        if corpus_record_budget < len(rescued):
            raise CorpusAssemblyError(
                f"corpus_record_budget {corpus_record_budget} is smaller than the "
                f"{len(rescued)} rescued examples this generation allocated; the "
                "budget cannot displace the human data it exists to make room for"
            )
        # Drop synthetic records from the end, keeping the oldest. The decode order is
        # the prompt order, which is frozen, so this is deterministic across arms and
        # seeds -- dropping at random would make the corpus depend on chance rather
        # than on the policy.
        keep = max(0, corpus_record_budget - len(rescued))
        displaced = max(0, len(synthetic) - keep)
        synthetic = synthetic[:keep]

    records: list[dict[str, Any]] = list(synthetic)
    provenance: list[dict[str, Any]] = []
    scores = dict(selection_scores or {})

    for example in rescued:
        text = _text_for(example, resolve_text)
        records.append({"text": text})
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
        "human_token_count": sum(_optimizer_tokens(e) for e in rescued),
        "human_word_count": sum(e.token_count for e in rescued),
        # Recorded per generation so the total-token divergence F-021 found is
        # diagnosable next time without re-running. The pilot's artifacts carried
        # chain totals only, which is why its mechanism is still unconfirmed.
        "total_record_count": len(records),
        "displaced_synthetic_records": displaced,
        "corpus_record_budget": corpus_record_budget,
    }


def candidates_from_manifest(
    manifest: PartitionManifest,
    *,
    undercoverage_scores: Mapping[str, float] | None = None,
) -> list[Any]:
    """Build policy candidates from a rescue manifest, budgeted in optimizer tokens.

    **This is where the budget's unit is enforced.** ``models.Candidate`` documents
    ``human_token_count`` as "non-padding tokens consumed per optimizer presentation
    under the frozen tokenizer", and ``PROTOCOL.md`` §3 forbids estimated counts. The
    manifest's ``token_count`` is a whitespace word count -- the unit the frozen
    ``article_length_quantile`` mode definition is built on, and correct for that --
    so it is **not** what a candidate is priced in. ``optimizer_token_count`` is.

    An example missing ``optimizer_token_count`` raises rather than silently falling
    back to the word count, which would reintroduce ``FAILURE_LOG.md`` F-010b: two
    policies selecting different examples with equal word totals can differ by up to
    ~20% in tokens the optimizer consumes, and budget matching would fail unnoticed.
    """
    from human_data_budget.models import Candidate  # noqa: PLC0415 - avoids a cycle

    scores = dict(undercoverage_scores or {})
    missing = [e.example_id for e in manifest.examples if e.optimizer_token_count is None]
    if missing:
        raise CorpusAssemblyError(
            f"{len(missing)} example(s) in the {manifest.partition!r} manifest have no "
            f"optimizer_token_count, e.g. {sorted(missing)[:3]}. Run "
            "scripts/add_optimizer_token_counts.py. Budgeting on token_count instead "
            "would price candidates in words -- see FAILURE_LOG.md F-010b."
        )
    return [
        Candidate(
            example_id=e.example_id,
            human_token_count=int(e.optimizer_token_count),
            mode=e.mode,
            undercoverage_score=float(scores.get(e.example_id, 0.0)),
        )
        for e in manifest.examples
    ]
