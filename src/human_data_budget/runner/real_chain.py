"""Real recursive chain: policy-allocated human rescue over real training.

Closes the Week 2 deliverable "prepare the real pilot runner adapter against
frozen Week 1 contracts" (``docs/weekly/WEEK_2.md``). Design agreed in
``docs/interfaces/recursive_steps.md``.

**Separate from ``chain.py`` on purpose.** The toy loop exists to prove the
component contracts connect and is the only path CI can run, having no model
stack. The real loop differs structurally -- it assembles a training corpus
between steps, captures a generation-0 reference snapshot, and derives mode
statistics from a real evaluator rather than a synthetic decay -- so branching the
toy loop would put real-mode conditionals inside the path a dozen CPU tests
depend on. The orchestration helpers (checkpoint, resume, manifest, failure
state) are shared; the loop body is not.

**The recursion travels through data.** ``chain.py`` calls the toy steps and
discards their return values, so one generation's output never reaches the next.
Here each decoded corpus is bound and fed forward, which is the behaviour the
recursion is named for.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from human_data_budget.data.corpus import (
    assemble_training_corpus,
    candidates_from_manifest,
)
from human_data_budget.data.manifest import load_manifest_from_jsonl
from human_data_budget.evaluation.real import mode_nll_to_retention_scores
from human_data_budget.evaluation.tail import tail_retention
from human_data_budget.models import ChainResult, GenerationMetric, PolicyState
from human_data_budget.policies.base import validate_allocation
from human_data_budget.runner.chain import policy_from_config
from human_data_budget.runner.checkpoint import (
    checkpoint_path,
    latest_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from human_data_budget.runner.failure import FailureState, write_failure
from human_data_budget.runner.manifest import (
    attach_failure,
    new_manifest,
    record_generation,
    transition_status,
    write_manifest_atomic,
)

REFERENCE_SNAPSHOT = "reference_mode_scores.json"


def _require(config: dict[str, Any], *keys: str) -> None:
    missing = [key for key in keys if key not in config]
    if missing:
        raise ValueError(f"real chain config missing keys: {sorted(missing)}")


def _write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_reference_snapshot(output_dir: Path) -> dict[str, float] | None:
    """Return the frozen generation-0 reference mode scores, if captured."""
    path = Path(output_dir) / REFERENCE_SNAPSHOT
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))["reference_mode_scores"]


def tail_modes_from(config: dict[str, Any]) -> set[str]:
    """Tail modes named by the frozen ``article_length_quantile`` definition."""
    modes = set(config.get("tail_modes") or ())
    if not modes:
        raise ValueError(
            "config must name tail_modes; tail_retention is undefined without them "
            "(docs/data/mode_definition_audit.md)"
        )
    return modes


def _resolver(config: dict[str, Any]):
    """Text resolver for rescued examples; lazy so CPU tests need no corpus."""
    if config.get("resolve_text") is not None:
        return config["resolve_text"]
    from human_data_budget.data.wikitext_source import resolve_text  # noqa: PLC0415

    return resolve_text


def _evaluate(
    config: dict[str, Any], trained: dict[str, Any], *, dry_run: bool
) -> dict[str, Any]:
    """Per-mode NLL for the current checkpoint on the validation partition."""
    if config.get("evaluator") is not None:
        return config["evaluator"](trained)
    if dry_run:
        modes = sorted(tail_modes_from(config) | {"common"})
        return {
            "mode_nll": dict.fromkeys(modes, 1.0),
            "human_nll": 1.0,
            "tokens_evaluated": 0,
        }
    from human_data_budget.evaluation.real import score_examples  # noqa: PLC0415

    validation = load_manifest_from_jsonl(config["validation_manifest"], "validation")
    resolve = _resolver(config)
    pairs = [(e.mode, resolve(e)) for e in validation.examples]
    return score_examples(
        trained["checkpoint_path"], pairs, max_length=config["training"]["block_size"]
    )


def run_real_chain(
    config: dict[str, Any],
    *,
    output_dir: Path,
    resume: bool = False,
    dry_run: bool = False,
) -> tuple[dict[str, Any], ChainResult]:
    """Run one recursive chain with real training, generation and evaluation.

    ``dry_run`` skips every subprocess and model load, so the orchestration --
    resume, budget arithmetic, corpus wiring, manifest writes -- is exercisable on
    CPU. It is how this loop is tested; it is not a scientific mode.
    """
    _require(
        config, "run_id", "budget_id", "policy", "horizon", "chain_seed",
        "lifetime_human_budget", "total_optimizer_tokens", "upstream_dir",
        "rescue_manifest", "base_corpus", "model", "training", "decoding", "detector",
    )

    from human_data_budget.generation.real import real_generate_step  # noqa: PLC0415
    from human_data_budget.training.real import real_train_step  # noqa: PLC0415

    output_dir = Path(output_dir)
    experiment = output_dir / "upstream"
    tail_modes = tail_modes_from(config)

    rescue = load_manifest_from_jsonl(config["rescue_manifest"], "rescue_candidates")
    candidates = tuple(candidates_from_manifest(rescue))
    policy = policy_from_config(config)

    manifest = new_manifest(config, policy_name=policy.name)
    checkpoint = None
    if resume:
        found = latest_checkpoint(output_dir)
        checkpoint = load_checkpoint(found) if found is not None else None
    manifest = transition_status(manifest, "running")
    write_manifest_atomic(manifest, output_dir / "run_manifest.json")

    if checkpoint is not None:
        start = checkpoint["generation"] + 1
        remaining = checkpoint["remaining_human_tokens"]
        consumed_human = checkpoint["consumed_human_tokens"]
        consumed_total = checkpoint.get("consumed_total_tokens", 0)
        allocations = list(checkpoint["allocations"])
        metrics = [GenerationMetric(**m) for m in checkpoint["metrics"]]
        pending = checkpoint.get("pending_selection") or []
        pending_scores = checkpoint.get("pending_scores") or {}
        prev_corpus = checkpoint.get("previous_corpus")
        mode_statistics = dict(checkpoint["mode_statistics"])
    else:
        start, remaining = 0, config["lifetime_human_budget"]
        consumed_human = consumed_total = 0
        allocations, metrics, pending = [], [], []
        pending_scores = {}
        prev_corpus = None
        mode_statistics = {}

    reference = load_reference_snapshot(output_dir)
    active = None

    try:
        for generation in range(start, config["horizon"]):
            active = generation
            seed = config["chain_seed"] * 1000 + generation
            gen_dir = experiment / str(generation)

            # 1. Training corpus. Generation 0 trains on the frozen human base;
            #    later generations train on the previous decode plus exactly the
            #    examples the policy bought.
            if generation == 0:
                train_file = Path(config["base_corpus"])
                human_tokens = 0
            else:
                assembled = assemble_training_corpus(
                    synthetic_corpus=prev_corpus,
                    rescue_manifest=rescue,
                    selected_example_ids=pending,
                    output_path=gen_dir / "data.json",
                    generation=generation,
                    selection_policy=policy.name,
                    selection_scores=pending_scores,
                    resolve_text=_resolver(config),
                )
                train_file = Path(assembled["corpus_path"])
                human_tokens = assembled["human_token_count"]

            # 2. Train.
            trained = real_train_step(
                {
                    "upstream_dir": config["upstream_dir"],
                    "generation": generation,
                    "model_identifier": config["model"]["identifier"],
                    "revision": config["model"].get("revision"),
                    "train_file": str(train_file),
                    "test_file": config["test_corpus"],
                    "output_dir": str(gen_dir / "model"),
                    **config["training"],
                    "shim_dir": config.get("shim_dir"),
                    "cuda_device": config.get("cuda_device", 0),
                    "log_path": str(output_dir / "stdout_stderr.log"),
                    "dry_run": dry_run,
                },
                seed,
            )
            consumed_total += int(trained.get("optimizer_consumed_tokens", 0))
            consumed_human += human_tokens

            # 3. Decode the corpus the next generation trains on. Binding this
            #    return value is what the toy path never did.
            generated = real_generate_step(
                {
                    "upstream_dir": config["upstream_dir"],
                    "generation": generation + 1,
                    "model_identifier": config["model"]["identifier"],
                    "checkpoint_path": trained.get("checkpoint_path", ""),
                    "experiment_path": str(experiment),
                    "dataset_filepath": str(train_file),
                    **config["training"],
                    **config["decoding"],
                    "detector_tokenizer_name": config["detector"]["tokenizer_name"],
                    "detector_path": config["detector"]["model_path"],
                    "detector_threshold": config["detector"]["ai_confidence_threshold"],
                    "detector_temperature": config["detector"]["temperature"],
                    "shim_dir": config.get("shim_dir"),
                    "cuda_device": config.get("cuda_device", 0),
                    "log_path": str(output_dir / "stdout_stderr.log"),
                    "dry_run": dry_run,
                },
                seed,
            )
            prev_corpus = generated.get("corpus_path")

            # 4. Evaluate, and freeze the reference snapshot at generation 0.
            scores = _evaluate(config, trained, dry_run=dry_run)
            mode_statistics = mode_nll_to_retention_scores(scores["mode_nll"])
            if generation == 0 and reference is None:
                reference = dict(mode_statistics)
                _write_json(
                    {
                        "generation": 0,
                        "reference_mode_scores": reference,
                        "mode_nll": scores["mode_nll"],
                        "checkpoint_sha256": trained.get("checkpoint_sha256"),
                    },
                    output_dir / REFERENCE_SNAPSHOT,
                )

            metrics.append(
                GenerationMetric(
                    generation=generation,
                    human_nll=scores["human_nll"],
                    tail_retention=tail_retention(
                        mode_statistics, reference, tail_modes
                    ),
                )
            )

            # 5. Allocate the next generation's rescue against the remaining budget.
            state = PolicyState(
                generation=generation,
                remaining_human_tokens=remaining,
                mode_statistics=mode_statistics,
                candidates=candidates,
                history=tuple(allocations),
            )
            allocation = policy.allocate(state, seed)
            validate_allocation(allocation, state)
            remaining -= allocation.selected_human_tokens
            allocations.append(allocation.as_dict())
            # Allocation records optimizer presentations per example; a positive
            # count is what 'selected' means. Scores ride along for provenance.
            pending = [eid for eid, n in allocation.presentations.items() if n > 0]
            pending_scores = dict(allocation.scores)

            save_checkpoint(
                {
                    "generation": generation,
                    "remaining_human_tokens": remaining,
                    "consumed_human_tokens": consumed_human,
                    "consumed_total_tokens": consumed_total,
                    "mode_statistics": mode_statistics,
                    "allocations": allocations,
                    "metrics": [m.as_dict() for m in metrics],
                    "pending_selection": pending,
                    "pending_scores": pending_scores,
                    "previous_corpus": prev_corpus,
                },
                checkpoint_path(output_dir, generation),
            )
            manifest = record_generation(manifest, generation)
            write_manifest_atomic(manifest, output_dir / "run_manifest.json")

    except Exception as error:
        failure = FailureState(
            run_id=config["run_id"],
            category="implementation_defect",
            message=str(error),
            generation=active,
            evidence={"error_type": type(error).__name__},
        )
        write_failure(failure, output_dir / "failure.json")
        manifest = attach_failure(manifest, failure.as_dict())
        manifest = transition_status(manifest, "failed")
        write_manifest_atomic(manifest, output_dir / "run_manifest.json")
        raise

    result = ChainResult(
        run_id=config["run_id"],
        policy=policy.name,
        chain_seed=config["chain_seed"],
        budget_id=config["budget_id"],
        generations_completed=config["horizon"],
        valid=True,
        metrics=tuple(metrics),
        consumed_human_tokens=consumed_human,
        consumed_total_tokens=consumed_total,
    )
    manifest = transition_status(manifest, "complete")
    write_manifest_atomic(manifest, output_dir / "run_manifest.json")
    _write_json(result.as_dict(), output_dir / "chain_result.json")
    return manifest, result
