#!/usr/bin/env python3
"""Materialise a training corpus from a frozen partition manifest.

The chain needs generation 0 to train on real human text, but committed manifests
are hash-only (``data/README.md``). This resolves them against the pinned corpus,
verifies each against its frozen ``content_hash``, and writes the corpus upstream
reads.

**The corpus format is not raw text.** ``src/generate.py`` prompts from a
``context`` field and classifies a ``cls_text`` field, both produced by upstream's
own preprocessing in ``src/load_data.py``: block-group and tokenize, decode back to
``text``, slice the leading ``input_token_length`` tokens into ``context``, and the
trailing remainder into ``cls_text``. A corpus of bare ``{"text": ...}`` records
trains fine and then fails decoding with ``KeyError: 'context'``.

So this reuses upstream's functions rather than reimplementing them, mirroring
``load_data.py::process_dataset(train=True)`` step for step. If upstream changes
its preprocessing, this changes with it.

The detector pass is deliberately omitted: ``cls_score`` is read only under
``data_selection=importance_sampling``, which this project overrides to
``no-selection`` (``expected_vs_observed.md`` deviation 1). Omitting it saves a
GPU pass over the whole corpus. Pass ``--classify`` to include it.

Build-time only: needs the pinned corpus cache, ``transformers``, and an upstream
checkout.

Usage:
  python scripts/build_base_corpus.py --partition base_train --limit 200 \\
      --upstream-dir /workspace/model_collapse --out data/corpora/base.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from human_data_budget.data.hashing import content_hash
from human_data_budget.data.manifest import load_manifest_from_jsonl
from human_data_budget.data.wikitext_source import resolve_text


def _upstream_utils(upstream_dir: Path):
    """Import upstream's preprocessing helpers from its checkout."""
    src = (upstream_dir / "src").resolve()
    if not (src / "utils" / "utils.py").is_file():
        raise SystemExit(
            f"no upstream checkout at {upstream_dir.resolve()}\n"
            "  Expected its src/utils/utils.py. Pass --upstream-dir."
        )
    sys.path.insert(0, str(src))
    from utils.utils import (  # noqa: PLC0415 - path is only valid after insert
        decode,
        get_context,
        get_text_to_classify,
        group_texts_and_tokenize_data,
    )

    return decode, get_context, get_text_to_classify, group_texts_and_tokenize_data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--manifest-dir", type=Path, default=Path("data/manifests"))
    parser.add_argument("--upstream-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--block-size", type=int, default=512)
    parser.add_argument("--loss-on-last-n-tokens", type=int, default=256)
    parser.add_argument("--tokenizer", default="openai-community/gpt2")
    parser.add_argument(
        "--eval",
        action="store_true",
        help="build an evaluation corpus carrying only 'text', mirroring "
        "load_data.py::process_dataset(train=False). Required for test and "
        "validation: upstream loads train_file and test_file together and rejects "
        "columns present in one and absent from the other, and generated corpora "
        "carry cls_score/cls_confidence/diversity rather than context/cls_text.",
    )
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    decode, get_context, get_text_to_classify, group_texts = _upstream_utils(
        args.upstream_dir
    )
    from datasets import Dataset  # noqa: PLC0415 - build-time dependency
    from transformers import AutoTokenizer  # noqa: PLC0415

    manifest = load_manifest_from_jsonl(
        args.manifest_dir / f"{args.partition}.jsonl", args.partition
    )
    examples = list(manifest.examples)
    if args.limit is not None:
        examples = examples[: args.limit]

    texts, words, tokens = [], 0, 0
    for index, example in enumerate(examples, 1):
        text = resolve_text(example)
        observed = content_hash(text)
        if observed != example.content_hash:
            raise SystemExit(
                f"content hash mismatch for {example.example_id}: manifest records "
                f"{example.content_hash}, resolved text hashes to {observed}"
            )
        texts.append(text)
        words += example.token_count
        tokens += example.optimizer_token_count or 0
        if index % 2000 == 0:
            print(f"  resolved {index}/{len(examples)}", flush=True)

    # Mirrors load_data.py::process_dataset(train=True).
    input_token_length = args.block_size - args.loss_on_last_n_tokens
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    dataset = Dataset.from_dict({"text": texts})

    dataset = group_texts(
        raw_datasets=dataset,
        tokenizer=tokenizer,
        column_names=["text"],
        block_size=args.block_size,
        preprocessing_num_workers=1,
        overwrite_cache=True,
    )
    dataset = dataset.map(
        lambda e: decode(e, tokenizer, "text", "input_ids"), desc="decode text"
    )

    if args.eval:
        # process_dataset(train=False): text only. An evaluation corpus must not
        # carry context or cls_text, because from generation 1 onward the train
        # file is a generated corpus that has neither, and upstream rejects a
        # column present in one file and absent from the other.
        records = [{"text": row["text"]} for row in dataset]
    else:
        dataset = dataset.map(
            lambda e: get_context(
                e,
                input_token_length,
                input_ids_key="context_input_ids",
                attention_mask_key="context_attention_mask",
            ),
            desc="context",
        )
        dataset = dataset.map(
            lambda e: get_text_to_classify(e, input_token_length), desc="cls slice"
        )
        dataset = dataset.map(
            lambda e: decode(e, tokenizer, "context", "context_input_ids"),
            desc="decode context",
        )
        dataset = dataset.map(
            lambda e: decode(e, tokenizer, "cls_text", "cls_input_ids"),
            desc="decode cls_text",
        )
        records = [
            {"text": row["text"], "context": row["context"], "cls_text": row["cls_text"]}
            for row in dataset
        ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, indent=4), encoding="utf-8")

    provenance = args.out.with_name(f"{args.out.stem}_provenance.json")
    provenance.write_text(
        json.dumps(
            {
                "partition": args.partition,
                "manifest_hash": manifest.manifest_hash,
                "examples_in_partition": len(manifest.examples),
                "examples_used": len(texts),
                "limit": args.limit,
                "blocks_written": len(records),
                "block_size": args.block_size,
                "input_token_length": input_token_length,
                "tokenizer": args.tokenizer,
                "word_count": words,
                "optimizer_token_count": tokens,
                "every_content_hash_verified": True,
                "fields": sorted(records[0]) if records else [],
                "preprocessing": (
                    "upstream load_data.py process_dataset("
                    f"train={not args.eval})"
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {args.out}: {len(records)} blocks from {len(texts)} examples, "
        f"{words:,} words, {tokens:,} optimizer tokens "
        f"(manifest {manifest.manifest_hash[:16]})"
    )


if __name__ == "__main__":
    main()
