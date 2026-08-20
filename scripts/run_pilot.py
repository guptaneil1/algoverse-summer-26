#!/usr/bin/env python3
"""Run a pilot: every arm crossed with every frozen seed, one chain at a time.

``run_real_chain.py`` executes one policy at one seed. A pilot is a grid --
``arms x seeds`` -- so something has to expand the config and sequence the chains.
This does that, and nothing else: it makes no scientific choice, reads every value
from the pilot config, and refuses the same way the single-chain launcher does.

**Sequential, and resumable per chain.** Each chain gets its own output directory
under ``output_dir/<arm>/seed<N>``. A completed chain is skipped on re-run; an
interrupted one resumes from its last checkpoint. So a session that dies at chain
17 of 25 costs the 17th chain, not the run.

**Budget matching is asserted, not assumed.** Every arm draws on the same
``lifetime_human_budget``, and the summary reports what each actually consumed.
`PROTOCOL.md` section 4 makes identical lifetime human-origin spend the fairness
constraint, and an unequal comparison is invalid rather than interesting, so a
violation exits non-zero rather than printing a warning under the results.

The assertion itself lives in ``human_data_budget.runner.budget_matching``, which
holds each spending arm to within one indivisible candidate of the ceiling instead
of to exact equality. Exact equality was the earlier guard here and no
configuration could satisfy it: the control arm's structural zero always differed
from the spending arms, so it fired on a grid whose realised spread was 0.04%. See
FAILURE_LOG.md F-015 and F-016, and decision P-008.

Usage:
  python scripts/run_pilot.py --config configs/experiment/<pilot>.json \\
      --upstream-dir /workspace/model_collapse --shim-dir /workspace/shim
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

from human_data_budget.policies import spends_human_tokens
from human_data_budget.runner.budget_matching import (
    check_realised_budget_matching,
    max_candidate_optimizer_tokens,
)
from human_data_budget.runner.real_chain import run_real_chain

UNFROZEN = "AWAITING_JULY_31_FREEZE"


def budget_report(pilot: dict, chains: list[dict]):
    """Assert realised budget matching over ``chains`` using the pilot's own values.

    The indivisibility bound comes from the frozen rescue-candidate manifest rather
    than a constant, so it tracks the manifest the run actually drew from.
    """
    manifest = pilot["data"]["manifests"]["rescue_candidates"]["path"]
    return check_realised_budget_matching(
        chains,
        lifetime_human_budget=pilot["lifetime_human_budget"],
        indivisibility_bound=max_candidate_optimizer_tokens(manifest),
        practical_effect_threshold_relative=pilot["practical_effect_threshold_relative"],
        is_spending_arm=spends_human_tokens,
    )


def load_grid_chains(root: Path) -> list[dict]:
    """Collect completed chains from every shard summary under ``root``.

    Shards write one summary each so concurrent writers cannot clobber one another.
    Reassembling them is what makes a whole-grid verdict possible after a sharded
    run, which no single shard process is in a position to reach.
    """
    chains: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for path in sorted(root.glob("pilot_summary*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for chain in payload.get("chains", []):
            if chain.get("status") != "complete":
                continue
            key = (chain["arm"], chain["seed"])
            # A resumed shard can re-emit a chain another summary already carries.
            # Counting it twice would not change min or max, but it would misreport
            # how much of the grid the verdict actually covers.
            if key in seen:
                continue
            seen.add(key)
            chains.append(chain)
    return chains


def chain_config(pilot: dict, arm: str, seed: int) -> dict:
    """Flatten the pilot grid into one chain config for ``run_real_chain``."""
    data = pilot["data"]
    corpora = data["corpora"]
    config = {
        "run_id": f"{pilot['run_id']}__{arm}__seed{seed}",
        "budget_id": pilot["budget_id"],
        "stage": pilot.get("stage", "pilot"),
        "policy": arm,
        "chain_seed": seed,
        "horizon": pilot["horizon"],
        "lifetime_human_budget": pilot["lifetime_human_budget"],
        "per_generation_human_budget": pilot["per_generation_human_budget"],
        "total_optimizer_tokens": pilot["total_optimizer_tokens"],
        "upstream_dir": pilot.get("upstream_dir", "upstream"),
        "shim_dir": pilot.get("shim_dir"),
        "cuda_device": pilot.get("cuda_device", 0),
        # The whole data block, not just the paths the chain consumes. new_manifest
        # resolves data.partitions from it, and without it every chain writes a
        # manifest with no provenance and certifies invalid with
        # SEPARATION_MISSING_PROVENANCE. FAILURE_LOG.md F-019.
        "data": data,
        "rescue_manifest": data["manifests"]["rescue_candidates"]["path"],
        "validation_manifest": data["manifests"]["validation"]["path"],
        "base_corpus": corpora["base_corpus"],
        "prompt_corpus": corpora["prompt_corpus"],
        "test_corpus": corpora["test_corpus"],
        # P-011. Null or absent keeps additive assembly, which is what the 2026-08-18
        # grid ran and what F-021 records as confounding training volume with strategy.
        "corpus_record_budget": pilot.get("corpus_record_budget"),
        # Operational only; see --preprocessing-workers. Not a frozen value.
        "preprocessing_workers": pilot.get("preprocessing_workers", 1),
        "tail_modes": pilot["tail_modes"],
        "model": pilot["model"],
        "training": pilot["training"],
        "decoding": pilot["decoding"],
        "detector": pilot["detector"],
    }
    if arm == "schedule_only":
        # ScheduleOnlyPolicy needs an explicit per-generation schedule. Built from
        # the frozen back-loaded shape in docs/method/week2_method_freeze.md:
        # nothing for the first half, the cap thereafter.
        horizon = pilot["horizon"]
        cap = pilot["maximum_generation_human_budget"]
        config["schedule"] = {
            str(g): (0 if g < horizon // 2 else cap) for g in range(horizon)
        }
    return config


def summary_name(seeds: list[int] | None, shard_index: int, shard_count: int) -> str:
    """Name this process's shard summary.

    One summary per writer, because concurrent shards writing one path would race
    and the last writer would silently discard the others' chains. A seed subset is
    part of a writer's identity for the same reason: successive phases of a grid
    finished block by block share a shard index, so without the seeds in the name
    each phase would overwrite the previous phase's summary -- and ``--check-only``
    reads summaries, so the whole-grid verdict would quietly cover only the last
    block run.

    ``seeds`` is None for a full run, which keeps the historical names exactly.
    Every form still matches the ``pilot_summary*.json`` glob that reassembles them.
    """

    parts = ["pilot_summary"]
    if seeds is not None:
        parts.append("seeds" + "-".join(str(seed) for seed in seeds))
    if shard_count > 1:
        parts.append(f"shard{shard_index}of{shard_count}")
    return "_".join(parts) + ".json"


def select_seeds(config_seeds: list[int], only_seeds: str | None) -> list[int]:
    """Restrict a run to a subset of the frozen seeds.

    The frozen seed set is not changed by this; a subset of it is run. A grid
    stopped by infrastructure leaves arms at uneven progress, and finishing it one
    seed block at a time means every stopping point is a fully crossed design
    rather than a ragged one -- which is the difference between a reduced design
    and no design. ``docs/decisions/powered_design_sizing_2026-08-19.md`` sizes
    three chains per arm against the preregistered threshold, so a three-seed
    block is a complete experiment, not a partial one.

    Order comes from the config, never from the command line: the shard deal is
    positional, so a reordered seed list would move chains between shards without
    saying so.
    """

    if not only_seeds:
        return list(config_seeds)
    requested = [int(token) for token in only_seeds.split(",") if token.strip()]
    if not requested:
        raise SystemExit("run_pilot: --only-seeds was given no seeds")
    unknown = [seed for seed in requested if seed not in config_seeds]
    if unknown:
        raise SystemExit(
            f"run_pilot: --only-seeds names {unknown}, which the config does not\n"
            f"  declare. Frozen seeds are {list(config_seeds)}. A seed absent from\n"
            "  the frozen set would produce chains nobody can certify."
        )
    return [seed for seed in config_seeds if seed in requested]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--upstream-dir", type=Path)
    parser.add_argument("--shim-dir", type=Path)
    parser.add_argument(
        "--preprocessing-workers", type=int, default=1,
        help="upstream tokenisation worker processes (default 1). Purely operational: "
             "HuggingFace `map` shards the dataset and reassembles it in order, so the "
             "tokenised output is identical whatever this is set to. It is deliberately "
             "NOT part of the frozen training block, because it changes how fast a "
             "chain runs and nothing about what it computes. Raising it is the cheapest "
             "speed-up available -- the 2026-08-18 grid ran at 1 and left the GPUs idle "
             "through every tokenisation phase.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check-only", action="store_true",
        help="run no chains; assert realised budget matching over every shard "
             "summary already written under --output-dir, and exit non-zero if it "
             "does not hold. This is the whole-grid verdict a sharded run needs.",
    )
    parser.add_argument("--only-arm", help="run one arm; for debugging, not for a pilot")
    parser.add_argument(
        "--only-seeds",
        help="comma-separated subset of the config's seeds, e.g. 303,404,505. The "
             "frozen seed set is unchanged -- this runs part of it. A grid stopped "
             "by infrastructure leaves arms at uneven progress, and completing it "
             "seed block by seed block yields a fully crossed design at every "
             "stopping point instead of a ragged one. Seeds keep their config "
             "order, so sharding is unchanged for the seeds that remain.")
    parser.add_argument(
        "--shard-index", type=int, default=0,
        help="0-based index of this shard. Chains are dealt round-robin across "
             "shards, so every shard gets a mix of arms and finishes at a similar "
             "time even though arms differ in cost.")
    parser.add_argument(
        "--shard-count", type=int, default=1,
        help="total shards. Chains are independent -- unlike the positive control's "
             "two arms, no chain consumes another's output -- so N shards on N GPUs "
             "cost the same as one shard on one GPU and finish in 1/N the time.")
    parser.add_argument("--cuda-device", type=int, default=None,
                        help="GPU for this shard. Upstream is single-device; this "
                             "selects which one, mirroring cuda_device in the "
                             "positive-control config.")
    args = parser.parse_args()

    if not 0 <= args.shard_index < args.shard_count:
        raise SystemExit(
            f"run_pilot: --shard-index {args.shard_index} outside "
            f"[0, {args.shard_count})"
        )

    pilot = json.loads(args.config.read_text(encoding="utf-8"))
    if pilot.get("_freeze_status") == UNFROZEN and pilot.get("stage") not in {
        "screening",
        "fixture",
    }:
        raise SystemExit(
            f"run_pilot: refusing to launch {args.config}\n"
            f"  _freeze_status is {UNFROZEN!r}. Its scientific values have not been\n"
            "  set from a results freeze. A pilot launched against unfrozen values\n"
            "  produces chains nobody can certify."
        )

    if args.check_only:
        root = args.output_dir or Path(pilot["output_dir"])
        # --only-seeds narrows the check to the seed blocks it names, so a grid being
        # completed block by block can be certified over the crossed design that
        # exists rather than over the whole plan. Without this the flag would be
        # accepted and silently ignored, which is the F-024 shape.
        checked_seeds = select_seeds(list(pilot["seeds"]), args.only_seeds)
        chains = [c for c in load_grid_chains(root) if c["seed"] in checked_seeds]
        expected = len(pilot["arms"]) * len(checked_seeds)
        print(f"run_pilot --check-only: {pilot['run_id']}")
        if args.only_seeds:
            print(f"  seeds {checked_seeds} of {list(pilot['seeds'])}")
        print(f"  {len(chains)} of {expected} chains found under {root}\n")
        report = budget_report(pilot, chains)
        print(report.render())
        if len(chains) < expected:
            # Reported, not failed. An operator checking a run in progress should see
            # a real verdict on what exists; treating partial coverage as a violation
            # would make the check useless until the last chain lands.
            print(f"\n   INCOMPLETE: {expected - len(chains)} chain(s) missing. This "
                  "verdict covers only the chains above.")
        return 0 if report.ok else 1

    if args.upstream_dir:
        pilot["upstream_dir"] = str(args.upstream_dir)
    if args.shim_dir:
        pilot["shim_dir"] = str(args.shim_dir)
    # Pin this whole process, not just its subprocesses. `run_upstream_step` sets
    # CUDA_VISIBLE_DEVICES for the children it spawns, but the evaluation step runs
    # *here*: real_chain._evaluate calls evaluation.real.score_examples, which resolves
    # to "cuda" -- physical device 0 unless the environment says otherwise. So every
    # shard evaluated on GPU 0 whatever --cuda-device said, four CUDA contexts and two
    # workloads landed on one card, and the detector OOMed during generation.
    # FAILURE_LOG.md F-025.
    if "CUDA_VISIBLE_DEVICES" in os.environ:
        # A caller already pinned us. The single visible device is index 0 to us and to
        # anything we spawn; passing the physical index through would name a device the
        # children cannot see.
        pilot["cuda_device"] = 0
    elif args.cuda_device is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_device)
        pilot["cuda_device"] = 0
    pilot["preprocessing_workers"] = args.preprocessing_workers

    root = args.output_dir or Path(pilot["output_dir"])
    arms = [args.only_arm] if args.only_arm else list(pilot["arms"])
    seeds = list(pilot["seeds"])
    seeds = select_seeds(seeds, args.only_seeds)

    grid = [(arm, seed) for arm in arms for seed in seeds]
    total = len(grid)
    mine = [(i, a, s) for i, (a, s) in enumerate(grid, 1)
            if (i - 1) % args.shard_count == args.shard_index]

    print(f"run_pilot: {pilot['run_id']}")
    print(f"  arms:  {arms}")
    print(f"  seeds: {seeds}")
    print(f"  chains: {total} total, {len(mine)} in this shard "
          f"({args.shard_index + 1}/{args.shard_count}), "
          f"cuda_device {pilot.get('cuda_device', 0)}")
    print(f"  horizon {pilot['horizon']}, lifetime budget "
          f"{pilot['lifetime_human_budget']:,} optimizer tokens")
    print(f"  output: {root}\n", flush=True)

    summary: list[dict] = []
    started = time.perf_counter()

    for position, arm, seed in mine:
        out = root / arm / f"seed{seed}"
        done = out / "chain_result.json"
        label = f"[{position}/{total}] {arm} seed {seed}"

        if done.is_file():
            payload = json.loads(done.read_text(encoding="utf-8"))
            print(f"{label}: already complete, skipping", flush=True)
            summary.append({"arm": arm, "seed": seed, "status": "complete",
                            **{k: payload.get(k) for k in
                               ("consumed_human_tokens", "consumed_total_tokens")}})
            continue

        resume = (out / "checkpoints").is_dir()
        print(f"{label}: {'resuming' if resume else 'starting'}", flush=True)
        try:
            _, result = run_real_chain(
                chain_config(pilot, arm, seed),
                output_dir=out, resume=resume, dry_run=args.dry_run,
            )
            summary.append({
                "arm": arm, "seed": seed, "status": "complete",
                "consumed_human_tokens": result.consumed_human_tokens,
                "consumed_total_tokens": result.consumed_total_tokens,
                "metrics": [m.as_dict() for m in result.metrics],
            })
            print(f"{label}: complete, "
                  f"{result.consumed_human_tokens:,} human tokens", flush=True)
        except Exception as error:  # noqa: BLE001 - one chain must not end the pilot
            summary.append({"arm": arm, "seed": seed, "status": "failed",
                            "error": f"{type(error).__name__}: {error}"})
            print(f"{label}: FAILED {type(error).__name__}: {error}", flush=True)
            traceback.print_exc()

    elapsed = time.perf_counter() - started
    root.mkdir(parents=True, exist_ok=True)
    name = summary_name(
        seeds if args.only_seeds else None, args.shard_index, args.shard_count)
    (root / name).write_text(
        json.dumps({"run_id": pilot["run_id"], "wall_seconds": elapsed,
                    "chains": summary}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    complete = [c for c in summary if c["status"] == "complete"]
    failed = [c for c in summary if c["status"] != "complete"]
    print(f"\n{len(complete)}/{total} chains complete in {elapsed/3600:.2f} h")

    report = budget_report(pilot, complete)
    print()
    print(report.render())
    if args.shard_count > 1:
        print("   NOTE: this shard saw "
              f"{len(complete)} of {total} chains. The authoritative check is over "
              "the whole grid:")
        print(f"   python scripts/run_pilot.py --config {args.config} "
              f"--output-dir {root} --check-only")

    for chain in failed:
        print(f"  failed: {chain['arm']} seed {chain['seed']}: {chain['error']}")
    print(f"\nsummary: {root / name}")
    if failed:
        return 1
    # A sharded process sees a subset, so its verdict is advisory: failing the shard
    # on a partial grid would abort three healthy shards over a spread that the full
    # grid may not have. --check-only is what gates the comparison.
    if not report.ok and args.shard_count == 1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
