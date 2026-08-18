#!/usr/bin/env python3
"""Materialise a training corpus from a frozen partition manifest.

The chain needs generation 0 to train on real human text, but committed manifests
are hash-only (``data/README.md``). This resolves them against the pinned corpus,
verifies each against its frozen ``content_hash``, and writes the JSON array of
``{"text": ...}`` records upstream reads.

``--limit`` takes the first N examples in manifest order, which is deterministic
because the manifest is. It exists so a pipeline-validation run can use a small
corpus without pretending to be the primary experiment; the resulting corpus
records what it was built from.

Build-time only: needs the pinned corpus cache and ``huggingface_hub``.

Usage:
  python scripts/build_base_corpus.py --partition base_train --out data/corpora/base.json
  python scripts/build_base_corpus.py --partition base_train --limit 200 --out small.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_data_budget.data.hashing import content_hash
from human_data_budget.data.manifest import load_manifest_from_jsonl
from human_data_budget.data.wikitext_source import resolve_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--manifest-dir", type=Path, default=Path("data/manifests"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    manifest = load_manifest_from_jsonl(
        args.manifest_dir / f"{args.partition}.jsonl", args.partition
    )
    examples = list(manifest.examples)
    if args.limit is not None:
        examples = examples[: args.limit]

    records, words, tokens = [], 0, 0
    for index, example in enumerate(examples, 1):
        text = resolve_text(example)
        observed = content_hash(text)
        if observed != example.content_hash:
            raise SystemExit(
                f"content hash mismatch for {example.example_id}: manifest records "
                f"{example.content_hash}, resolved text hashes to {observed}"
            )
        records.append({"text": text})
        words += example.token_count
        tokens += example.optimizer_token_count or 0
        if index % 2000 == 0:
            print(f"  {index}/{len(examples)}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, indent=4), encoding="utf-8")

    provenance = args.out.with_name(f"{args.out.stem}_provenance.json")
    provenance.write_text(
        json.dumps(
            {
                "partition": args.partition,
                "manifest_hash": manifest.manifest_hash,
                "examples_in_partition": len(manifest.examples),
                "examples_used": len(records),
                "limit": args.limit,
                "word_count": words,
                "optimizer_token_count": tokens,
                "every_content_hash_verified": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {args.out}: {len(records)} records, {words:,} words, "
        f"{tokens:,} optimizer tokens (manifest {manifest.manifest_hash[:16]})"
    )


if __name__ == "__main__":
    main()
