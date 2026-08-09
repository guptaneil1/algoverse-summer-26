#!/usr/bin/env python3
"""Leave-one-block-out ablation for a prompt.

Splits a prompt into blocks, generates one variant per block with that block
removed, and runs the whole set. Any block whose removal does not lower the
score is not earning its place — delete it.

This is the actual engineering step. Adding lines is free and feels productive;
ablation is what tells you which of them do anything. A prompt that has never
been ablated is a pile of guesses that happened to co-occur with a good run.

Usage:
    python promptlab/ablate.py promptlab/variants/full.md --reps 5
    python promptlab/ablate.py promptlab/variants/full.md --blocks   # preview only
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent


def split_blocks(text: str) -> list[str]:
    """Blocks are paragraphs, or individual items in a bulleted/numbered run.
    Bullets get split individually because a single bad rule inside a list is
    the common case, and paragraph-level ablation would hide it."""
    blocks: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.rstrip()
        if not para:
            continue
        lines = para.split("\n")
        if sum(bool(re.match(r"\s*([-*+]|\d+[.)])\s", ln)) for ln in lines) >= 2:
            cur: list[str] = []
            for ln in lines:
                if re.match(r"\s*([-*+]|\d+[.)])\s", ln) and cur:
                    blocks.append("\n".join(cur))
                    cur = [ln]
                else:
                    cur.append(ln)
            if cur:
                blocks.append("\n".join(cur))
        else:
            blocks.append(para)
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--blocks", action="store_true", help="preview blocks, then exit")
    ap.add_argument("--max-blocks", type=int, default=14,
                    help="refuse to ablate beyond this; cost is blocks x tasks x reps")
    args = ap.parse_args()

    src = Path(args.prompt)
    text = src.read_text()
    blocks = split_blocks(text)

    print(f"{src.name}: {len(blocks)} blocks\n")
    for i, b in enumerate(blocks):
        head = b.strip().split("\n")[0]
        print(f"  [{i:>2}] {head[:76]}")
    if args.blocks:
        return 0

    if len(blocks) > args.max_blocks:
        print(f"\n{len(blocks)} blocks exceeds --max-blocks={args.max_blocks}. "
              f"Ablate a section at a time, or raise the cap knowingly.",
              file=sys.stderr)
        return 2

    out = LAB / "variants" / "_ablation"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    (out / "00_full.md").write_text(text)
    for i, b in enumerate(blocks):
        kept = [x for j, x in enumerate(blocks) if j != i]
        head = re.sub(r"[^a-z0-9]+", "_",
                      b.strip().split("\n")[0].lower())[:28].strip("_")
        (out / f"{i + 1:02d}_no_{head or 'block'}.md").write_text(
            "\n\n".join(kept) + "\n")

    variants = sorted(str(p) for p in out.glob("*.md"))
    print(f"\ngenerated {len(variants)} variants in {out}")
    print(f"running {len(variants)} x tasks x {args.reps} reps ...\n")

    rc = subprocess.run(
        [sys.executable, str(LAB / "run.py"), "--variants", *variants,
         "--reps", str(args.reps),
         "--out", str(LAB / "results" / "ablation.jsonl")]).returncode
    if rc != 0:
        return rc

    print("\n" + "=" * 70)
    subprocess.run([sys.executable, str(LAB / "score.py"),
                    "--results", str(LAB / "results" / "ablation.jsonl"),
                    "--baseline", "00_full"])

    print("""
READING THIS
  A block whose removal leaves the score unchanged is dead weight. Delete it.
  Dead weight is not harmless: it dilutes attention across the prompt and makes
  the rules that do matter easier to skip.

  A block whose removal RAISES the score is actively hurting. Delete it first,
  then work out what it was doing — usually it was pulling toward a behaviour
  that conflicts with another rule.

  A block whose removal lowers the score has earned its place. Keep it, and
  write down which failure it prevents.

  Overlapping intervals mean you learned nothing about that block. Raise reps
  or accept that you cannot tell.
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
