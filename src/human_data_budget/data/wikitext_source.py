"""Rehydrate manifest text from the pinned WikiText-103 release.

Committed manifests are hash-only (``data/README.md``), so anything that trains on
a rescued example must fetch its text at run time. ``source_offset`` is the article's
start row in the pinned split, which is exactly what
``scripts/build_wikitext103_manifests.py`` recorded when it hashed the text.

**The builder's own parsing is imported, not reimplemented.** Article reconstruction
from the line-based release depends on blank-line placement and title detection; a
second implementation that drifted by one row would produce text whose hash no longer
matches the manifest. Importing the script keeps one definition. The hash check in
``data.corpus`` is the backstop if that ever fails.

Build-time dependency: ``huggingface_hub`` and ``pyarrow``, the same extras the
builder needs. Neither is a runtime dependency of this package, so this module is
imported lazily by callers that actually need text.
"""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType

from human_data_budget.data.manifest import Example

REPO_ROOT = Path(__file__).resolve().parents[3]
BUILDER_PATH = REPO_ROOT / "scripts" / "build_wikitext103_manifests.py"


class SourceUnavailableError(RuntimeError):
    """The pinned corpus could not be read."""


@lru_cache(maxsize=1)
def _builder() -> ModuleType:
    if not BUILDER_PATH.is_file():
        raise SourceUnavailableError(f"manifest builder not found at {BUILDER_PATH}")
    spec = importlib.util.spec_from_file_location("_wikitext103_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise SourceUnavailableError(f"cannot load {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=8)
def _articles_by_offset(split: str) -> dict[int, str]:
    """Map article start row to article text for one pinned split.

    Cached per split: the train split parses into tens of thousands of articles and
    a per-example reparse would dominate assembly time.
    """
    builder = _builder()
    rows = builder._download_split(split)
    return {start: text for start, _end, text in builder._parse_articles(rows)}


def split_for(example: Example) -> str:
    """Which pinned split an example came from, read from its stable ID prefix.

    ``_stable_id`` in the builder formats identifiers as ``{split}-{digest}``, and the
    three train-family partitions all originate in the train split.
    """
    prefix = example.example_id.split("-", 1)[0]
    if prefix not in {"train", "validation", "test"}:
        raise SourceUnavailableError(
            f"cannot infer source split from example_id {example.example_id!r}"
        )
    return prefix


def resolve_text(example: Example) -> str:
    """Return this example's text from the pinned corpus.

    Callers pass this to ``data.corpus.assemble_training_corpus``, which verifies the
    result against the manifest's ``content_hash`` before it can enter training.
    """
    articles = _articles_by_offset(split_for(example))
    text = articles.get(int(example.source_offset))
    if text is None:
        raise SourceUnavailableError(
            f"no article at row {example.source_offset} of the "
            f"{split_for(example)!r} split for {example.example_id!r}"
        )
    return text
