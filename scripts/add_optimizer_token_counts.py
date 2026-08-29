#!/usr/bin/env python3
"""Populate ``optimizer_token_count`` on the frozen partition manifests.

``FAILURE_LOG.md`` F-010b: ``token_count`` is ``len(text.split())``, a whitespace
word count. The frozen ``article_length_quantile`` mode definition is built on that
and stays as it is (``docs/data/mode_definition_audit.md`` explicitly names the
"whitespace-split rule" as frozen). But ``PROTOCOL.md`` §3 requires budget
accounting in tokens the optimizer actually consumes, and
``models.Candidate.human_token_count`` documents exactly that. One field cannot be
both, so this adds a second.

**Partition identity is preserved.** ``_manifest_hash`` digests only
``[example_id, content_hash]`` pairs, so populating a new field cannot change a
manifest hash. The script asserts that rather than trusting it.

**One tokenizer per manifest set.** ``optimizer_token_count`` is only meaningful
against the tokenizer that produced it, and the budget is denominated in it, so a
second model needs its own manifests rather than a second field. Pass
``--tokenizer`` with ``--out-dir`` to build a parallel set; the default writes in
place with the GPT-2 tokenizer, which is the behaviour the frozen pilot used.

Build-time only; needs ``transformers`` and the pinned corpus cache.
Usage:
  python scripts/add_optimizer_token_counts.py [partition ...]
  python scripts/add_optimizer_token_counts.py --tokenizer Qwen/Qwen2.5-0.5B \\
      --out-dir data/manifests/qwen
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_data_budget.data.manifest import load_manifest_from_jsonl
from human_data_budget.data.wikitext_source import resolve_text

MANIFEST_DIR = Path("data/manifests")
TOKENIZER = "openai-community/gpt2"
DEFAULT_PARTITIONS = ("rescue_candidates", "validation", "test", "prompts", "base_train")


def augment(partition: str, *, tokenizer_name: str = TOKENIZER,
            manifest_dir: Path = MANIFEST_DIR,
            out_dir: Path | None = None) -> dict[str, float]:
    from transformers import AutoTokenizer  # noqa: PLC0415 - build-time only

    source = manifest_dir / f"{partition}.jsonl"
    path = (out_dir or manifest_dir) / f"{partition}.jsonl"
    manifest = load_manifest_from_jsonl(source, partition)
    before = manifest.manifest_hash
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    records, words, tokens = [], 0, 0
    for index, example in enumerate(manifest.examples, 1):
        text = resolve_text(example)
        count = len(tokenizer(text, add_special_tokens=False)["input_ids"])
        record = example.to_dict() if hasattr(example, "to_dict") else None
        record = {
            "example_id": example.example_id, "content_hash": example.content_hash,
            "origin": example.origin, "mode": example.mode, "source": example.source,
            "source_offset": example.source_offset, "token_count": example.token_count,
            "optimizer_token_count": count,
        }
        if example.source_revision is not None:
            record["source_revision"] = example.source_revision
        records.append(record)
        words += example.token_count
        tokens += count
        if index % 2000 == 0:
            print(f"  {partition}: {index}/{len(manifest.examples)}", flush=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
                   encoding="utf-8")
    tmp.replace(path)

    after = load_manifest_from_jsonl(path, partition).manifest_hash
    if before != after:
        raise SystemExit(f"{partition}: manifest hash changed {before} -> {after}")
    ratio = tokens / words if words else float("nan")
    print(f"{partition}: {len(records)} examples, {words:,} words -> {tokens:,} tokens "
          f"(x{ratio:.4f}), hash unchanged {after[:16]}")
    return {"words": words, "tokens": tokens, "ratio": ratio}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("partitions", nargs="*", default=None)
    parser.add_argument("--tokenizer", default=TOKENIZER,
                        help="HuggingFace tokenizer id; the counts are only valid "
                             "against this one")
    parser.add_argument("--manifest-dir", type=Path, default=MANIFEST_DIR,
                        help="where to read the frozen manifests from")
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="where to write them; defaults to --manifest-dir, which "
                             "rewrites in place")
    args = parser.parse_args()

    out_dir = args.out_dir or args.manifest_dir
    if args.tokenizer != TOKENIZER and out_dir == args.manifest_dir:
        raise SystemExit(
            f"refusing to overwrite {args.manifest_dir} with counts from "
            f"{args.tokenizer}: the frozen pilot manifests are denominated in "
            f"{TOKENIZER} tokens and the budget depends on them. Pass --out-dir."
        )

    partitions = args.partitions or list(DEFAULT_PARTITIONS)
    summary = {
        p: augment(p, tokenizer_name=args.tokenizer,
                   manifest_dir=args.manifest_dir, out_dir=out_dir)
        for p in partitions
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "OPTIMIZER_TOKEN_COUNTS.json"
    out.write_text(json.dumps({"tokenizer": args.tokenizer, "partitions": summary},
                              indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
