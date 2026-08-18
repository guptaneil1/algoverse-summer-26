#!/usr/bin/env python3
"""Run one real recursive chain from a config file.

Refuses any config still awaiting the results freeze, for the same reason
``scripts/run_chain.sh`` does: a chain launched against unfrozen scientific values
produces numbers nobody can certify, and the refusal is cheaper than the run.

A config carrying ``"stage": "screening"`` is allowed through without a freeze,
because a screening run is explicitly not a primary result. Its output is written
with that stage recorded, so it cannot later be mistaken for one.

Usage:
  python scripts/run_real_chain.py --config configs/experiment/<name>.json
  python scripts/run_real_chain.py --config <path> --dry-run   # no GPU, no model
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from human_data_budget.runner.real_chain import run_real_chain

UNFROZEN = "AWAITING_JULY_31_FREEZE"
STAGES_WITHOUT_FREEZE = {"fixture", "screening"}


def load_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))

    status = config.get("_freeze_status")
    stage = config.get("stage")
    if status == UNFROZEN and stage not in STAGES_WITHOUT_FREEZE:
        raise SystemExit(
            f"run_real_chain: refusing to launch {path}\n"
            f"  _freeze_status is {status!r} and stage is {stage!r}.\n"
            "  Its scientific values have not been set from a results freeze.\n"
            "  Fill every field listed under _required_from_freeze, set\n"
            "  _freeze_status to 'FROZEN', and record which freeze supplied them.\n"
            "  A pipeline-validation run belongs under stage 'screening' instead."
        )

    unset = sorted(key for key, value in config.items() if value is None)
    if unset:
        raise SystemExit(f"run_real_chain: config has unset values: {unset}")
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = args.output_dir or Path("runs") / config["run_id"]

    print(f"run_real_chain: {config['run_id']} "
          f"(stage={config.get('stage')}, policy={config['policy']}, "
          f"horizon={config['horizon']}, seed={config['chain_seed']})", flush=True)

    _, result = run_real_chain(
        config, output_dir=output_dir, resume=args.resume, dry_run=args.dry_run
    )

    print(f"\ncomplete: {result.generations_completed} generations")
    print(f"  human-origin optimizer tokens: {result.consumed_human_tokens:,}")
    print(f"  total optimizer tokens:        {result.consumed_total_tokens:,}")
    for metric in result.metrics:
        print(f"  generation {metric.generation}: human_nll={metric.human_nll:.4f} "
              f"tail_retention={metric.tail_retention:.4f}")
    print(f"\nartifacts: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
