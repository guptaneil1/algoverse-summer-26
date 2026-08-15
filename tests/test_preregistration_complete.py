import json
from pathlib import Path

REQUIRED_TEXT_FILES = (
    Path("PREREGISTRATION.md"),
    Path("DECISIONS.md"),
    Path("docs/method/week2_method_freeze.md"),
)

REQUIRED_CONFIG_FILES = (
    Path("configs/policy/random.json"),
    Path("configs/policy/schedule_only.json"),
    Path("configs/policy/selection_only.json"),
    Path("configs/policy/joint.json"),
    Path("configs/experiment/primary_pilot.json"),
)

PROHIBITED_PLACEHOLDERS = (
    "TBD",
    "REPLACE_ME",
    "AWAITING_TEAM",
    "‹",
    "›",
)


def test_required_week2_files_exist_and_are_not_empty() -> None:
    for path in REQUIRED_TEXT_FILES + REQUIRED_CONFIG_FILES:
        assert path.exists(), f"missing required file: {path}"
        assert path.read_text(encoding="utf-8").strip(), (
            f"required file is empty: {path}"
        )


def test_no_unresolved_placeholders_remain() -> None:
    for path in REQUIRED_TEXT_FILES + REQUIRED_CONFIG_FILES:
        content = path.read_text(encoding="utf-8")

        for placeholder in PROHIBITED_PLACEHOLDERS:
            assert placeholder not in content, (
                f"{path} contains unresolved placeholder {placeholder!r}"
            )


def test_primary_pilot_config_has_required_fields() -> None:
    config = json.loads(
        Path("configs/experiment/primary_pilot_week2_preregistration.json").read_text(
            encoding="utf-8"
        )
    )

    assert config["primary_horizon"] == 10
    assert config["primary_lifetime_human_tokens"] == 100
    assert config["total_optimizer_tokens_per_chain"] == 10_000

    assert config["ordered_chain_seeds"]
    assert config["ordered_replacement_seeds"]

    assert config["primary_outcome"]
    assert config["primary_contrast"]
    assert config["baseline_selection_rule"]
    assert config["meaningful_effect_threshold"] > 0

    assert config["outcome_based_stopping_allowed"] is False


def test_real_model_execution_is_explicitly_blocked() -> None:
    config = json.loads(
        Path("configs/experiment/primary_pilot_week2_preregistration.json").read_text(
            encoding="utf-8"
        )
    )

    status = config["scientific_status"]
    blocker = config["real_run_blocker"]

    assert "blocked" in status
    assert "tokenizer-counted" in blocker