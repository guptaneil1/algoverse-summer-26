#!/usr/bin/env python3
"""Run prompt variants against graded tasks and record results.

Every (variant, task, rep) cell runs in an isolated git worktree so a task that
edits files cannot contaminate the next run.

Usage:
    python promptlab/run.py --reps 5
    python promptlab/run.py --variants promptlab/variants/baseline.md --reps 3
    python promptlab/run.py --dry-run          # exercise the harness, no API calls

Output: promptlab/results/results.jsonl (append-only). Score with score.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "promptlab"
TASK_SLOT = "{{TASK}}"

# Read-only by default. A variant that needs more must say so explicitly.
ALLOWED_TOOLS = "Read,Grep,Glob"


# --------------------------------------------------------------------------- #
# Grading
# --------------------------------------------------------------------------- #

def _flags(spec: str | None) -> int:
    return re.IGNORECASE if spec and "i" in spec.lower() else 0


def grade(text: str, checks: list[dict]) -> list[dict]:
    """Deterministic checks only. If a property needs a judge, it needs a
    better-designed task instead — judges add variance to the thing you are
    trying to measure variance in."""
    out = []
    low = text.lower()
    for c in checks:
        kind = c["type"]
        if kind == "contains_any":
            passed = any(s.lower() in low for s in c["any"])
        elif kind == "not_contains":
            passed = not any(s.lower() in low for s in c["any"])
        elif kind == "regex":
            passed = re.search(c["pattern"], text, _flags(c.get("flags"))) is not None
        elif kind == "not_regex":
            passed = re.search(c["pattern"], text, _flags(c.get("flags"))) is None
        else:
            raise ValueError(f"unknown check type: {kind}")
        out.append({"type": kind, "passed": passed,
                    "message": None if passed else c.get("fail_message", kind)})
    return out


# --------------------------------------------------------------------------- #
# Variants
# --------------------------------------------------------------------------- #

def load_variant(path: Path) -> dict:
    """A variant containing {{TASK}} is a user-prompt template; otherwise it is
    treated as an appended system prompt (the CLAUDE.md-shaped intervention)."""
    body = path.read_text()
    return {
        "name": path.stem,
        "body": body,
        "mode": "user_template" if TASK_SLOT in body else "system_append",
        "bare": "bare" in path.stem,   # filename opt-in: skip CLAUDE.md discovery
    }


def build_cmd(variant: dict, task_text: str, workdir: Path,
              max_turns: int) -> tuple[list[str], str | None]:
    """Returns (argv, tempfile_to_clean)."""
    tmp = None
    if variant["mode"] == "user_template":
        prompt = variant["body"].replace(TASK_SLOT, task_text)
        argv = ["claude", "-p", prompt]
    else:
        fd, tmp = tempfile.mkstemp(suffix=".md", text=True)
        with os.fdopen(fd, "w") as fh:
            fh.write(variant["body"])
        argv = ["claude", "-p", task_text, "--append-system-prompt-file", tmp]

    argv += ["--output-format", "json",
             "--allowedTools", ALLOWED_TOOLS,
             "--max-turns", str(max_turns)]
    if variant["bare"]:
        # Skips CLAUDE.md, hooks, skills, MCP discovery. Use this to measure
        # whether project memory is carrying the result, rather than assuming it.
        argv.append("--bare")
    return argv, tmp


# --------------------------------------------------------------------------- #
# Isolation
# --------------------------------------------------------------------------- #

def make_worktree(base: Path) -> Path | None:
    d = Path(tempfile.mkdtemp(prefix="promptlab-"))
    wt = d / "wt"
    r = subprocess.run(["git", "worktree", "add", "--detach", str(wt), "HEAD"],
                       cwd=base, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    worktree failed ({r.stderr.strip()[:120]}); running in place",
              file=sys.stderr)
        shutil.rmtree(d, ignore_errors=True)
        return None
    return wt


def drop_worktree(base: Path, wt: Path) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                   cwd=base, capture_output=True)
    shutil.rmtree(wt.parent, ignore_errors=True)


def dirty_paths(wt: Path) -> list[str]:
    r = subprocess.run(["git", "status", "--porcelain"], cwd=wt,
                       capture_output=True, text=True)
    return [ln[3:].strip() for ln in r.stdout.splitlines() if ln.strip()]


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #

def run_cell(variant: dict, task: dict, rep: int, args) -> dict:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "variant": variant["name"],
        "mode": variant["mode"],
        "bare": variant["bare"],
        "task": task["id"],
        "rep": rep,
    }

    if args.dry_run:
        rec |= {"text": "[dry-run]", "checks": [], "passed": None,
                "cost_usd": 0.0, "seconds": 0.0}
        return rec

    wt = None if args.no_isolate else make_worktree(ROOT)
    cwd = wt or ROOT
    argv, tmp = build_cmd(variant, task["task"], cwd, args.max_turns)

    t0 = time.time()
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True,
                              text=True, timeout=args.timeout)
        raw = proc.stdout
    except subprocess.TimeoutExpired:
        rec |= {"error": "timeout", "passed": False, "checks": [],
                "seconds": time.time() - t0}
        if wt:
            drop_worktree(ROOT, wt)
        if tmp:
            os.unlink(tmp)
        return rec
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    rec["seconds"] = round(time.time() - t0, 1)

    try:
        payload = json.loads(raw)
        text = payload.get("result", "") or ""
        rec["cost_usd"] = payload.get("total_cost_usd", payload.get("cost_usd"))
        rec["session_id"] = payload.get("session_id")
        if payload.get("is_error"):
            rec["error"] = "claude_reported_error"
    except json.JSONDecodeError:
        text = raw
        rec["error"] = "unparseable_output"

    checks = grade(text, task["checks"])

    # File-mutation check: a task can pass on wording while still doing the
    # forbidden thing. Both must hold.
    if task.get("no_file_changes") and wt:
        changed = dirty_paths(wt)
        protected = task.get("protected_paths")
        offending = [p for p in changed
                     if not protected or any(p.endswith(x) for x in protected)]
        checks.append({
            "type": "no_file_changes",
            "passed": not offending,
            "message": None if not offending else f"modified {offending}",
        })

    rec["checks"] = checks
    rec["passed"] = all(c["passed"] for c in checks)
    rec["text"] = text[: args.keep_chars]

    if wt:
        drop_worktree(ROOT, wt)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="*", default=None)
    ap.add_argument("--tasks", default=str(LAB / "tasks"))
    ap.add_argument("--reps", type=int, default=5,
                    help="repetitions per cell. Below 5 you cannot separate a "
                         "real difference from sampling noise.")
    ap.add_argument("--max-turns", type=int, default=12)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--keep-chars", type=int, default=4000)
    ap.add_argument("--out", default=str(LAB / "results" / "results.jsonl"))
    ap.add_argument("--no-isolate", action="store_true",
                    help="skip git worktrees (faster, but file-mutation checks "
                         "are skipped and a mutating task can dirty your repo)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and shutil.which("claude") is None:
        print("claude CLI not found on PATH", file=sys.stderr)
        return 2

    vpaths = ([Path(p) for p in args.variants] if args.variants
              else sorted((LAB / "variants").glob("*.md")))
    if not vpaths:
        print("no variants found", file=sys.stderr)
        return 2
    variants = [load_variant(p) for p in vpaths]
    tasks = [json.loads(p.read_text())
             for p in sorted(Path(args.tasks).glob("*.json"))]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    total = len(variants) * len(tasks) * args.reps
    print(f"{len(variants)} variants x {len(tasks)} tasks x {args.reps} reps "
          f"= {total} runs\n")

    n = 0
    with out.open("a") as fh:
        for v in variants:
            for t in tasks:
                marks = []
                for rep in range(args.reps):
                    n += 1
                    rec = run_cell(v, t, rep, args)
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    marks.append("." if rec.get("passed") else
                                 ("?" if rec.get("passed") is None else "X"))
                print(f"[{n:>4}/{total}] {v['name']:<22} {t['id']:<20} "
                      f"{''.join(marks)}")

    print(f"\nwrote {out}\nnext: python promptlab/score.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
