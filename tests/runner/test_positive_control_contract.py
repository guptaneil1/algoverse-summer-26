"""Both arm configs carry every frozen identifier, budget, seed, and horizon field.

This is the test that stops a run from being launched against a half-specified
condition. It checks not only that fields exist but that the two arms form a
*controlled contrast*: identical in everything except the mixture that defines them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from human_data_budget.runner.positive_control_adapter import (
    UNRESOLVED,
    UPSTREAM_COMMIT,
    UPSTREAM_REPOSITORY,
    PositiveControlError,
    arm_invariant_view,
    assert_resolved,
    load_arm_config,
    unresolved_identifiers,
    validate_arm_config,
)

ROOT = Path(__file__).resolve().parents[2]

ARMS = {
    "fully_synthetic": ROOT / "configs/experiment/positive_control_fully_synthetic.json",
    "human_mixed": ROOT / "configs/experiment/positive_control_human_mixed.json",
}

FROZEN_HORIZON = 11
FROZEN_SEED = 42


@pytest.fixture(params=sorted(ARMS), ids=sorted(ARMS))
def arm_name(request: pytest.FixtureRequest) -> str:
    return request.param


def test_both_arm_configs_exist_and_validate(arm_name: str) -> None:
    config = load_arm_config(ARMS[arm_name])
    assert config["arm"] == arm_name
    assert config["stage"] == "positive_control"


def test_upstream_is_pinned_to_the_protocol_commit(arm_name: str) -> None:
    config = load_arm_config(ARMS[arm_name])
    assert config["upstream"]["repository"] == UPSTREAM_REPOSITORY
    assert config["upstream"]["commit"] == UPSTREAM_COMMIT
    assert len(config["upstream"]["commit"]) == 40


def test_protocol_pins_the_same_upstream_commit() -> None:
    """The config and PROTOCOL.md must not be allowed to drift apart."""

    protocol = (ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
    assert UPSTREAM_COMMIT in protocol
    assert "TODO(khantushig)" not in protocol, (
        "PROTOCOL.md still carries an unresolved freeze placeholder; "
        "expected behaviour must be frozen before any run"
    )


def test_frozen_seed_horizon_and_budgets_are_present(arm_name: str) -> None:
    config = load_arm_config(ARMS[arm_name])

    assert config["chain_seed"] == FROZEN_SEED
    assert config["horizon"] == FROZEN_HORIZON

    assert isinstance(config["lifetime_human_budget"], int)
    assert isinstance(config["total_optimizer_tokens"], int)
    assert config["total_optimizer_tokens"] >= 1
    assert config["lifetime_human_budget"] >= 0
    assert config["lifetime_human_budget"] <= config["total_optimizer_tokens"]


def test_planned_budgets_are_labelled_as_estimates_not_measurements(arm_name: str) -> None:
    """A pre-run budget is a plan. It must not be presentable as a measurement."""

    config = load_arm_config(ARMS[arm_name])
    assert config["budget_status"] == "planned_estimate"
    assert "NOT a measurement" in config["budget_basis"]


def test_model_and_data_identifiers_are_declared(arm_name: str) -> None:
    config = load_arm_config(ARMS[arm_name])

    assert config["model"]["identifier"] == "openai-community/gpt2"
    assert config["data"]["identifier"] == "wikitext/wikitext-2-raw-v1"
    for field in ("revision", "tokenizer_revision"):
        assert config["model"][field], f"model.{field} must be declared"


def test_unresolved_identifiers_block_execution(arm_name: str) -> None:
    """The sentinel is a contract, not a placeholder: it must actually stop a run.

    Checked against a config deliberately reverted to the sentinel, rather than against
    the committed one. Before Stage A ran, the committed configs carried sentinels and
    this test read them directly; they now carry the identifiers the executed run
    resolved, so testing the mechanism means constructing the unresolved case.
    """

    config = load_arm_config(ARMS[arm_name])
    config["model"]["revision"] = UNRESOLVED

    unresolved = unresolved_identifiers(config)
    assert unresolved, "reverting an identifier to the sentinel must be detected"
    assert all(value for value in unresolved)

    with pytest.raises(Exception) as excinfo:
        assert_resolved(config)
    assert UNRESOLVED in str(excinfo.value)


def test_committed_configs_are_fully_resolved(arm_name: str) -> None:
    """Post-run invariant: the configs must describe the run that actually happened.

    Stage A completed on 2026-08-07, so every deferred identifier now has a real value
    and no sentinel may reappear. A sentinel here would mean the committed configs no
    longer describe the executed run.
    """

    config = load_arm_config(ARMS[arm_name])

    assert unresolved_identifiers(config) == []
    assert_resolved(config)

    assert config["model"]["revision"] == config["model"]["tokenizer_revision"]
    assert len(config["model"]["revision"]) == 40
    assert len(config["data"]["revision"]) == 40
    assert len(config["data"]["train_manifest_sha256"]) == 64


def test_training_generation_and_evaluation_settings_are_frozen(arm_name: str) -> None:
    config = load_arm_config(ARMS[arm_name])

    assert config["training"] == {
        "block_size": 512,
        "loss_on_last_n_tokens": 256,
        "batch_size": 8,
        "num_train_epochs": 1,
        "save_steps": 2000,
        "torch_dtype": "bfloat16",
        "low_cpu_mem_usage": True,
    }
    assert config["decoding"] == {
        "strategy": "top_k",
        "temperature": 1.0,
        "top_p": 1.0,
        "top_k": 50,
        "beam_search": False,
    }
    assert config["evaluation"]["metric_field"] == "perplexity"
    assert config["evaluation"]["paired_baseline_generation"] == 0


def test_tolerance_is_declared_engineering_only(arm_name: str) -> None:
    """PROTOCOL.md forbids presenting the 5% band as proof of exact replication."""

    config = load_arm_config(ARMS[arm_name])
    assert config["expected"]["relative_tolerance"] == 0.05
    assert config["expected"]["tolerance_status"] == "engineering_only"


def test_the_two_arms_differ_only_in_their_mixture() -> None:
    """Anything varying beyond the declared arm fields would confound the contrast."""

    synthetic = load_arm_config(ARMS["fully_synthetic"])
    mixed = load_arm_config(ARMS["human_mixed"])

    assert arm_invariant_view(synthetic) == arm_invariant_view(mixed)

    assert synthetic["mixture"]["human_data_alpha"] == 0.0
    assert mixed["mixture"]["human_data_alpha"] == 1.0
    assert synthetic["mixture"]["ai_beta"] == mixed["mixture"]["ai_beta"] == 1.0
    assert synthetic["mixture"]["accumulate_ai_data"] is False
    assert mixed["mixture"]["accumulate_ai_data"] is False


def test_both_arms_disable_the_upstream_importance_sampling_default() -> None:
    """Leaving the paper's own mitigation on would confound the collapse baseline."""

    for path in ARMS.values():
        config = load_arm_config(path)
        assert "data_selection=no-selection" in config["upstream"]["overrides"]
        assert config["data_selection"]["strategy"] == "None"


def test_both_arms_share_seed_and_horizon_overrides() -> None:
    synthetic = load_arm_config(ARMS["fully_synthetic"])
    mixed = load_arm_config(ARMS["human_mixed"])

    for shared in ("seed=42", "num_iterations=10", "wandb_disabled=true"):
        assert shared in synthetic["upstream"]["overrides"]
        assert shared in mixed["upstream"]["overrides"]


def test_horizon_matches_the_upstream_iteration_count() -> None:
    """``num_iterations=10`` yields generations 0..10 inclusive, i.e. a horizon of 11."""

    config = load_arm_config(ARMS["fully_synthetic"])
    iterations = next(
        int(override.split("=", 1)[1])
        for override in config["upstream"]["overrides"]
        if override.startswith("num_iterations=")
    )
    assert config["horizon"] == iterations + 1


def test_validation_rejects_a_drafting_placeholder(tmp_path: Path) -> None:
    config = json.loads(ARMS["fully_synthetic"].read_text(encoding="utf-8"))
    config["budget_id"] = "TODO: decide this later"

    with pytest.raises(PositiveControlError, match="placeholder"):
        validate_arm_config(config)


def test_validation_rejects_an_unpinned_upstream_commit() -> None:
    config = json.loads(ARMS["fully_synthetic"].read_text(encoding="utf-8"))
    config["upstream"]["commit"] = "0" * 40

    with pytest.raises(PositiveControlError, match="upstream.commit"):
        validate_arm_config(config)


def test_validation_rejects_a_missing_frozen_field() -> None:
    config = json.loads(ARMS["fully_synthetic"].read_text(encoding="utf-8"))
    del config["chain_seed"]

    with pytest.raises(PositiveControlError, match="chain_seed"):
        validate_arm_config(config)


def test_validation_rejects_a_non_positive_control_stage() -> None:
    config = json.loads(ARMS["fully_synthetic"].read_text(encoding="utf-8"))
    config["stage"] = "fixture"

    with pytest.raises(PositiveControlError, match="positive_control"):
        validate_arm_config(config)
