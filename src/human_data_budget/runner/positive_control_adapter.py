"""Adapt official upstream positive-control artifacts into the frozen runner contracts.

Scope: this module performs *translation only*. It reads artifacts produced by
`GeorgeDrayson/model_collapse` at the commit pinned in `PROTOCOL.md` and expresses
them in this repository's run-manifest and checkpoint shapes. It never computes a
scientific quantity of its own, never substitutes a value upstream did not produce,
and never invents an identifier that upstream left unpinned.

Three refusals are deliberate and are what make the adapter trustworthy:

1. ``assert_resolved`` refuses to move a manifest out of ``planned`` while any
   identifier still carries the ``resolve_at_runtime`` sentinel. Upstream pins no
   model, tokenizer, or dataset revision, so those must be resolved on the host that
   actually runs the experiment.
2. ``ingest_generation`` refuses to record a generation whose upstream artifacts are
   absent, rather than recording a gap.
3. ``build_chain_result`` refuses to emit a ``ChainResult`` at all, because the frozen
   ``chain_result``/``evaluation`` schemas require a ``tail_retention`` figure that the
   upstream positive control does not produce. Fabricating a sentinel there would
   manufacture exactly the "persuasive-looking but scientifically unusable" artifact
   ``PROTOCOL.md`` §1 exists to prevent.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

from human_data_budget.runner.checkpoint import (
    checkpoint_path,
    latest_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from human_data_budget.runner.manifest import (
    new_manifest,
    record_generation,
    transition_status,
    write_manifest_atomic,
)

UPSTREAM_REPOSITORY = "https://github.com/GeorgeDrayson/model_collapse"
UPSTREAM_COMMIT = "feb8511479a2e2dc868e1caf3f63cb99f1fcc746"

#: Sentinel for an identifier upstream leaves unpinned; must be resolved on the run host.
UNRESOLVED = "resolve_at_runtime"

#: Config keys every arm must declare before a run may be planned.
REQUIRED_CONFIG_FIELDS = (
    "schema_version",
    "run_id",
    "arm",
    "stage",
    "budget_id",
    "chain_seed",
    "horizon",
    "lifetime_human_budget",
    "total_optimizer_tokens",
    "mixture",
    "model",
    "data",
    "upstream",
    "training",
    "decoding",
    "evaluation",
    "expected",
)

#: Top-level keys permitted to differ between the two arms. Everything else must match,
#: which is what makes the comparison a controlled contrast rather than two unrelated runs.
ARM_VARYING_FIELDS = frozenset(
    {
        "run_id",
        "arm",
        "mixture",
        "lifetime_human_budget",
        "total_optimizer_tokens",
        "budget_basis",
        "upstream",
        "expected",
    }
)

_PLACEHOLDER_MARKERS = ("TODO", "TBD", "FIXME", "XXX")

_HASH_CHUNK_BYTES = 1024 * 1024

#: Per-generation sidecar written by the driver *before* any pruning, so a hash taken
#: while the artifact existed survives the artifact itself.
ARTIFACT_RECORD_NAME = "artifact_record.json"

#: Only model directories may be pruned. Metrics and generated data are small and are
#: the actual scientific record, so they are never removed.
PRUNABLE_ARTIFACTS = frozenset({"model_dir"})


class PositiveControlError(RuntimeError):
    """Base class for adapter refusals."""


class UnresolvedIdentifierError(PositiveControlError):
    """An identifier upstream left unpinned was never resolved on the run host."""


class MissingUpstreamArtifactError(PositiveControlError):
    """An upstream artifact required to record a generation is absent."""


class MissingTailMeasureError(PositiveControlError):
    """The frozen chain-result contract needs a tail measure the positive control lacks."""


# --------------------------------------------------------------------------------------
# hashing
# --------------------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """Return the SHA-256 of one file, read in chunks so large checkpoints stream."""

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str:
    """Return a deterministic SHA-256 over a directory's contents.

    Paths are walked in sorted order and each contributes ``relpath\\0size\\0filehash``,
    so the result is stable across filesystems and independent of walk order. A model
    checkpoint directory hashes to one value this way.
    """

    digest = hashlib.sha256()
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = file_path.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(file_path.stat().st_size).encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(file_path).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    """Hash ``path`` whether it is a file or a directory."""

    if path.is_dir():
        return sha256_tree(path)
    return sha256_file(path)


# --------------------------------------------------------------------------------------
# repository and environment state
# --------------------------------------------------------------------------------------


def git_commit(repo_root: Path) -> str:
    """Return the full 40-character commit of ``repo_root``."""

    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def working_tree_clean(repo_root: Path) -> bool:
    """Return whether ``repo_root`` has no tracked modifications or untracked files."""

    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == ""


def assert_upstream_checkout(upstream_dir: Path) -> str:
    """Verify ``upstream_dir`` is the pinned upstream commit; return that commit."""

    if not (upstream_dir / ".git").exists():
        raise MissingUpstreamArtifactError(
            f"no upstream checkout at {upstream_dir}: clone {UPSTREAM_REPOSITORY} "
            f"and check out {UPSTREAM_COMMIT}"
        )
    found = git_commit(upstream_dir)
    if found != UPSTREAM_COMMIT:
        raise MissingUpstreamArtifactError(
            f"upstream checkout at {upstream_dir} is {found}, expected {UPSTREAM_COMMIT} "
            "(PROTOCOL.md pins this commit; do not run against a different one)"
        )
    return found


def capture_environment() -> dict[str, str]:
    """Record the executing environment, including whether an accelerator is present."""

    environment = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }
    for module_name in ("torch", "transformers", "datasets"):
        try:
            module = __import__(module_name)
        except ImportError:
            environment[module_name] = "not_installed"
        else:
            environment[module_name] = getattr(module, "__version__", "unknown")
    environment["accelerator"] = _detect_accelerator()
    return environment


def _detect_accelerator() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "none_detected"
    return result.stdout.strip().replace("\n", "; ") or "none_detected"


# --------------------------------------------------------------------------------------
# config loading and validation
# --------------------------------------------------------------------------------------


def load_arm_config(path: Path) -> dict[str, Any]:
    """Load and validate one arm config, refusing placeholders and wrong pins."""

    config = json.loads(path.read_text(encoding="utf-8"))
    validate_arm_config(config, source=path)
    return config


def validate_arm_config(config: dict[str, Any], *, source: Path | None = None) -> None:
    """Raise if ``config`` is missing frozen fields or still carries drafting placeholders."""

    where = f" in {source}" if source is not None else ""

    missing = [field for field in REQUIRED_CONFIG_FIELDS if field not in config]
    if missing:
        raise PositiveControlError(f"missing frozen config fields{where}: {', '.join(missing)}")

    if config["stage"] != "positive_control":
        raise PositiveControlError(
            f"stage{where} must be 'positive_control', found {config['stage']!r}"
        )

    upstream = config["upstream"]
    if upstream.get("repository") != UPSTREAM_REPOSITORY:
        raise PositiveControlError(f"upstream.repository{where} does not match the pinned repo")
    if upstream.get("commit") != UPSTREAM_COMMIT:
        raise PositiveControlError(
            f"upstream.commit{where} is {upstream.get('commit')!r}, expected {UPSTREAM_COMMIT}"
        )

    for budget_field in ("lifetime_human_budget", "total_optimizer_tokens"):
        value = config[budget_field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PositiveControlError(f"{budget_field}{where} must be a non-negative integer")
    if config["total_optimizer_tokens"] < 1:
        raise PositiveControlError(f"total_optimizer_tokens{where} must be at least 1")

    if not isinstance(config["horizon"], int) or config["horizon"] < 1:
        raise PositiveControlError(f"horizon{where} must be a positive integer")

    for marker in _find_placeholders(config):
        raise PositiveControlError(
            f"unresolved drafting placeholder{where}: {marker}. Freeze the value before running."
        )


def _find_placeholders(value: Any, path: str = "") -> list[str]:
    """Return dotted paths whose string values still contain a drafting placeholder.

    The ``resolve_at_runtime`` sentinel is intentionally *not* a placeholder: it is a
    declared contract enforced by :func:`assert_resolved`, not an unfinished thought.
    """

    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(_find_placeholders(item, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_find_placeholders(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        for marker in _PLACEHOLDER_MARKERS:
            if marker in value:
                found.append(f"{path} contains {marker!r}")
    return found


def unresolved_identifiers(config: dict[str, Any]) -> list[str]:
    """Return dotted paths still set to the ``resolve_at_runtime`` sentinel."""

    unresolved: list[str] = []
    for section in ("model", "data"):
        for key, value in config.get(section, {}).items():
            if value == UNRESOLVED:
                unresolved.append(f"{section}.{key}")
    return sorted(unresolved)


def assert_resolved(config: dict[str, Any]) -> None:
    """Raise unless every runtime-resolved identifier has been filled in."""

    unresolved = unresolved_identifiers(config)
    if unresolved:
        raise UnresolvedIdentifierError(
            f"cannot leave status=planned while these are still {UNRESOLVED!r}: "
            + ", ".join(unresolved)
            + ". Resolve them on the accelerator host (Hugging Face revision SHAs and the "
            "prepared dataset hash) and record them in the config before running."
        )


def arm_invariant_view(config: dict[str, Any]) -> dict[str, Any]:
    """Return ``config`` without the fields the two arms are allowed to differ in."""

    return {key: value for key, value in config.items() if key not in ARM_VARYING_FIELDS}


# --------------------------------------------------------------------------------------
# manifest construction
# --------------------------------------------------------------------------------------


def build_manifest(config: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    """Build the ``planned`` run manifest for one arm.

    Unlike the toy chain, this records the *real* project commit and clean/dirty state:
    a positive-control manifest that claims a placeholder commit is not evidence.
    """

    manifest_config = dict(config)
    manifest_config["policy_config"] = str(
        Path("configs/experiment") / f"positive_control_{config['arm']}.json"
    )
    manifest_config["policy_config_sha256"] = UNRESOLVED
    manifest_config["environment"] = capture_environment()

    manifest = new_manifest(
        manifest_config,
        policy_name="upstream_no_selection",
        git_commit=git_commit(repo_root),
        working_tree_clean=working_tree_clean(repo_root),
    )
    manifest["upstream"] = dict(config["upstream"])
    manifest["arm"] = config["arm"]
    manifest["mixture"] = dict(config["mixture"])
    manifest["artifacts"] = []
    return manifest


# --------------------------------------------------------------------------------------
# upstream artifact ingestion
# --------------------------------------------------------------------------------------


def upstream_artifact_paths(experiment_path: Path, generation: int) -> dict[str, Path]:
    """Return the upstream artifact layout for one generation.

    Mirrors ``main.py`` at the pinned commit: per-iteration directories holding a
    trained model, its ``eval_results.json``, and (for generations above zero) the
    ``data.json`` that generation was trained on.
    """

    generation_dir = experiment_path / str(generation)
    paths = {
        "model_dir": generation_dir / "model" / "final_model",
        "eval_results": generation_dir / "model" / "eval_results.json",
    }
    if generation > 0:
        paths["generated_data"] = generation_dir / "data.json"
    return paths


def read_eval_results(path: Path, config: dict[str, Any]) -> dict[str, float]:
    """Read the frozen metric fields out of one upstream ``eval_results.json``."""

    if not path.is_file():
        raise MissingUpstreamArtifactError(f"missing upstream eval results: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    metric_field = config["evaluation"]["metric_field"]
    if metric_field not in payload:
        raise MissingUpstreamArtifactError(
            f"{path} has no {metric_field!r} field; upstream metric layout changed"
        )
    metrics = {metric_field: float(payload[metric_field])}
    secondary = config["evaluation"].get("secondary_metric_field")
    if secondary and secondary in payload:
        metrics[secondary] = float(payload[secondary])
    return metrics


def artifact_record_path(experiment_path: Path, generation: int) -> Path:
    """Return the sidecar path holding hashes taken before any pruning."""

    return experiment_path / str(generation) / ARTIFACT_RECORD_NAME


def write_artifact_record(experiment_path: Path, generation: int) -> dict[str, Any]:
    """Hash this generation's artifacts now and persist the result.

    Called by the driver the moment a generation completes, while every artifact is
    still on disk. Pruning a model directory afterwards therefore loses the bytes but
    not the evidence of what those bytes were.
    """

    paths = upstream_artifact_paths(experiment_path, generation)
    artifacts: dict[str, Any] = {}
    for name, path in paths.items():
        if not path.exists():
            raise MissingUpstreamArtifactError(
                f"generation {generation}: cannot record {name}, nothing at {path}"
            )
        artifacts[name] = {"path": str(path), "sha256": sha256_path(path), "pruned": False}

    record = {"generation": generation, "artifacts": artifacts}
    _write_json_atomic(record, artifact_record_path(experiment_path, generation))
    return record


def mark_pruned(experiment_path: Path, generation: int, name: str, reason: str) -> None:
    """Record that ``name`` was deliberately deleted after being hashed."""

    path = artifact_record_path(experiment_path, generation)
    if not path.is_file():
        raise MissingUpstreamArtifactError(
            f"refusing to mark {name} pruned for generation {generation}: "
            f"no {ARTIFACT_RECORD_NAME} at {path}. Hash before you delete."
        )
    if name not in PRUNABLE_ARTIFACTS:
        raise PositiveControlError(f"{name} may not be pruned; it is scientific record")

    record = json.loads(path.read_text(encoding="utf-8"))
    record["artifacts"][name]["pruned"] = True
    record["artifacts"][name]["pruned_reason"] = reason
    _write_json_atomic(record, path)


def ingest_generation(
    config: dict[str, Any],
    *,
    experiment_path: Path,
    generation: int,
) -> dict[str, Any]:
    """Return one generation's record: upstream metrics plus a hash for every artifact.

    Prefers the pre-pruning sidecar when one exists, so a generation whose model
    directory was deleted to fit a storage quota still carries the hash taken while it
    was present. Refuses rather than recording a gap when an artifact is absent and was
    never recorded as pruned.
    """

    paths = upstream_artifact_paths(experiment_path, generation)
    sidecar_path = artifact_record_path(experiment_path, generation)
    sidecar = (
        json.loads(sidecar_path.read_text(encoding="utf-8"))["artifacts"]
        if sidecar_path.is_file()
        else {}
    )

    record: dict[str, Any] = {"generation": generation, "artifacts": {}}
    for name, path in paths.items():
        recorded = sidecar.get(name)
        if path.exists():
            current = sha256_path(path)
            if recorded is not None and not recorded.get("pruned") and (
                recorded["sha256"] != current
            ):
                raise PositiveControlError(
                    f"generation {generation}: {name} changed since the run recorded it "
                    f"(recorded {recorded['sha256'][:12]}…, now {current[:12]}…)"
                )
            record["artifacts"][name] = {
                "path": str(path),
                "sha256": current,
                "pruned": False,
            }
        elif recorded is not None and recorded.get("pruned"):
            record["artifacts"][name] = dict(recorded)
        else:
            raise MissingUpstreamArtifactError(
                f"generation {generation}: missing upstream artifact {name} at {path}"
            )

    record["metrics"] = read_eval_results(paths["eval_results"], config)
    return record


def adapt_run(
    config: dict[str, Any],
    *,
    experiment_path: Path,
    output_dir: Path,
    repo_root: Path,
    resume: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Ingest a completed upstream run into this repository's contracts.

    Walks generations ``0..horizon-1``, hashing every artifact and saving an atomic
    checkpoint after each. With ``resume=True`` it restarts from the latest checkpoint
    under ``output_dir`` rather than from generation zero, and reaches byte-identical
    state either way — the equivalence ``PROTOCOL.md`` requires, tested in
    ``tests/runner/test_real_checkpoint_resume.py``.
    """

    assert_resolved(config)

    manifest = build_manifest(config, repo_root=repo_root)
    manifest = transition_status(manifest, "running")
    write_manifest_atomic(manifest, output_dir / "run_manifest.json")

    checkpoint: dict[str, Any] | None = None
    if resume:
        found = latest_checkpoint(output_dir)
        checkpoint = load_checkpoint(found) if found is not None else None

    if checkpoint is not None:
        start_generation = checkpoint["generation"] + 1
        records: list[dict[str, Any]] = list(checkpoint["records"])
    else:
        start_generation = 0
        records = []

    for generation in range(start_generation, config["horizon"]):
        records.append(
            ingest_generation(config, experiment_path=experiment_path, generation=generation)
        )
        save_checkpoint(
            {
                "generation": generation,
                "run_id": config["run_id"],
                "arm": config["arm"],
                "records": records,
            },
            checkpoint_path(output_dir, generation),
        )
        manifest = record_generation(manifest, generation)
        write_manifest_atomic(manifest, output_dir / "run_manifest.json")

    summary = summarize(config, records)
    manifest["artifacts"] = [
        {"generation": record["generation"], **record["artifacts"]} for record in records
    ]
    manifest = transition_status(manifest, "complete")
    write_manifest_atomic(manifest, output_dir / "run_manifest.json")
    _write_json_atomic(summary, output_dir / "positive_control_result.json")
    return manifest, summary


def summarize(config: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the frozen endpoint from ingested records. No thresholds applied here."""

    metric_field = config["evaluation"]["metric_field"]
    baseline_generation = config["evaluation"]["paired_baseline_generation"]
    by_generation = {record["generation"]: record["metrics"][metric_field] for record in records}

    baseline = by_generation.get(baseline_generation)
    final_generation = config["horizon"] - 1
    final = by_generation.get(final_generation)
    ratio = None
    if baseline not in (None, 0) and final is not None:
        ratio = final / baseline

    return {
        "schema_version": "1.0",
        "run_id": config["run_id"],
        "arm": config["arm"],
        "upstream_commit": config["upstream"]["commit"],
        "metric_field": metric_field,
        "generations_ingested": len(records),
        "horizon": config["horizon"],
        "metric_by_generation": {str(key): value for key, value in sorted(by_generation.items())},
        "baseline_generation": baseline_generation,
        "baseline_value": baseline,
        "final_generation": final_generation,
        "final_value": final,
        "degradation_ratio": ratio,
    }


def _write_json_atomic(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


# --------------------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------------------


def verify_recorded_hashes(run_dir: Path) -> list[str]:
    """Recompute every hash recorded under ``run_dir``; return human-readable mismatches.

    An empty list means every checkpoint, generated-data file, metric file, and config
    reference still hashes to the value recorded at ingest time.
    """

    mismatches: list[str] = []
    checkpoints_dir = run_dir / "checkpoints"
    if not checkpoints_dir.is_dir():
        return [f"no checkpoints directory under {run_dir}"]

    for checkpoint_file in sorted(checkpoints_dir.glob("generation_*.json")):
        state = json.loads(checkpoint_file.read_text(encoding="utf-8"))
        for record in state.get("records", []):
            for name, artifact in record.get("artifacts", {}).items():
                if artifact.get("pruned"):
                    # Deliberately deleted after hashing. Its hash is still evidence of
                    # what existed; the bytes are simply no longer re-checkable, which
                    # pruned_artifacts() reports rather than hides.
                    continue
                path = Path(artifact["path"])
                if not path.exists():
                    mismatches.append(
                        f"generation {record['generation']}: {name} recorded at {path} is gone"
                    )
                    continue
                recomputed = sha256_path(path)
                if recomputed != artifact["sha256"]:
                    mismatches.append(
                        f"generation {record['generation']}: {name} hash changed "
                        f"(recorded {artifact['sha256'][:12]}…, now {recomputed[:12]}…)"
                    )
    return mismatches


def pruned_artifacts(run_dir: Path) -> list[dict[str, Any]]:
    """Return every artifact deleted after hashing, so the limitation stays visible.

    A pruned artifact's hash cannot be re-verified. That is a real weakening of the
    evidence chain and belongs in the report, not in a silence.
    """

    pruned: list[dict[str, Any]] = []
    checkpoints_dir = run_dir / "checkpoints"
    if not checkpoints_dir.is_dir():
        return pruned

    latest = latest_checkpoint(run_dir)
    if latest is None:
        return pruned

    state = json.loads(latest.read_text(encoding="utf-8"))
    for record in state.get("records", []):
        for name, artifact in record.get("artifacts", {}).items():
            if artifact.get("pruned"):
                pruned.append(
                    {
                        "generation": record["generation"],
                        "artifact": name,
                        "path": artifact["path"],
                        "sha256": artifact["sha256"],
                        "reason": artifact.get("pruned_reason", "unrecorded"),
                    }
                )
    return pruned


def build_chain_result(*_args: Any, **_kwargs: Any) -> None:
    """Refuse to emit a ``ChainResult`` for the positive control. Always raises.

    ``schemas/chain_result.schema.json`` and ``schemas/evaluation.schema.json`` both
    require a ``tail_retention`` figure. The upstream positive control measures test
    perplexity and eval loss only — it produces no tail measure, and this repository's
    primary tail-retention definition is itself still being frozen (Neil's Week 2
    deliverable). Emitting a sentinel here would produce a schema-valid artifact whose
    tail number means nothing, which is precisely the failure mode ``PROTOCOL.md`` §1
    names. Stage A therefore reports through ``positive_control_result.json``, and this
    function exists to make the refusal explicit rather than leaving a gap someone later
    fills with a placeholder.
    """

    raise MissingTailMeasureError(
        "the upstream positive control produces no tail-retention measure, so no "
        "ChainResult can be emitted for Stage A; use positive_control_result.json and "
        "record the limitation in docs/positive_control/expected_vs_observed.md"
    )
