#!/usr/bin/env python3
"""Run the cross-model grid unattended, one model after another.

``scripts/run_pilot.py`` already runs all five arms across all five seeds for one
config, so this is a thin loop over per-model configs plus a ledger, not a
reimplementation of it. Each model is one invocation of the real pilot runner with
the same upstream and shim directories.

Idempotent, because a pod session will be interrupted. A model whose config is
missing is reported and skipped rather than guessed at; a model that already
succeeded is skipped on the next invocation. Rerun the same command until it says
nothing is left.

    python scripts/run_cross_model.py --upstream-dir /workspace/model_collapse \\
        --shim-dir /workspace/shim
    python scripts/run_cross_model.py --models qwen --dry-run

Exit codes: 0 all attempted models succeeded or nothing was left, 1 at least one
failed, 2 refused to start.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUDGET = REPO / "configs/experiment/cross_model_budget.json"


def die(message: str) -> None:
    print(f"REFUSING TO START: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-dir", type=Path, required=True)
    ap.add_argument("--shim-dir", type=Path)
    ap.add_argument("--models", nargs="*",
                    help="short_names to run; default is every planned model")
    ap.add_argument("--cuda-device", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not BUDGET.exists():
        die(f"the frozen budget rule is missing at {BUDGET}")
    budget = json.loads(BUDGET.read_text(encoding="utf-8"))

    wanted = set(args.models) if args.models else None
    ledger_path = REPO / "runs/cross_model_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}

    queue, missing, done = [], [], []
    for model in budget["models"]:
        short = model["short_name"]
        if wanted is not None and short not in wanted:
            continue
        if short == "gpt2":
            done.append(f"{short} (executed 2026-08-20, satisfies the rule as run)")
            continue
        config = REPO / f"configs/experiment/pilot_{short}.json"
        if not config.exists():
            missing.append(short)
            continue
        if ledger.get(short, {}).get("ok"):
            done.append(short)
            continue
        queue.append((short, config))

    print(f"already done  {done}")
    print(f"to run        {[s for s, _ in queue]}")
    if missing:
        print(f"\nSKIPPED, no config: {missing}")
        print("  build each model's manifests, then its config:")
        print("    python scripts/add_optimizer_token_counts.py --tokenizer <id> \\")
        print("        --out-dir data/manifests/<short_name>")
        print("    python scripts/make_model_pilot.py --model <short_name>")

    if args.dry_run or not queue:
        if not queue and not args.dry_run:
            print("\nnothing left to do")
        return

    failures = 0
    for index, (short, config) in enumerate(queue, 1):
        cmd = [sys.executable, "scripts/run_pilot.py", "--config", str(config),
               "--upstream-dir", str(args.upstream_dir)]
        if args.shim_dir:
            cmd += ["--shim-dir", str(args.shim_dir)]
        if args.cuda_device is not None:
            cmd += ["--cuda-device", str(args.cuda_device)]

        print(f"\n[{index}/{len(queue)}] {short}")
        print(f"  $ {' '.join(cmd)}", flush=True)
        started = time.time()
        completed = subprocess.run(cmd, cwd=REPO)
        elapsed = time.time() - started

        ok = completed.returncode == 0
        failures += not ok
        ledger[short] = {"ok": ok, "returncode": completed.returncode,
                         "hours": round(elapsed / 3600, 3), "config": str(config.name)}
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        print(f"  {'ok' if ok else 'FAILED'} after {elapsed / 3600:.2f} h")

    print(f"\n{len(queue) - failures}/{len(queue)} models succeeded; ledger at "
          f"runs/cross_model_ledger.json")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
