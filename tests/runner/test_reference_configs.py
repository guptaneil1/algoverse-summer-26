"""The primary configs carry no hidden defaults and cannot run unfrozen.

Today these configs are skeletons awaiting the July 31 freeze, so the tests
assert the guard rails. The moment ``_freeze_status`` becomes ``FROZEN`` the
same tests start enforcing structure, positivity, ordered seeds, and budget
equality between the two reference arms. Nothing needs to be rewritten then.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs" / "experiment"

NO_RESCUE = CONFIG_DIR / "primary_no_rescue.json"
FRESH_RANDOM = CONFIG_DIR / "primary_fresh_random.json"
PRIMARY_PILOT = CONFIG_DIR / "primary_pilot.json"

REFERENCE_ARMS = (NO_RESCUE, FRESH_RANDOM)
ALL_PRIMARY = (NO_RESCUE, FRESH_RANDOM, PRIMARY_PILOT)

# Present in every primary config regardless of freeze state.
REQUIRED_KEYS = (
    "run_id",
    "budget_id",
    "stage",
    "horizon",
    "seeds",
    "lifetime_human_budget",
    "total_optimizer_tokens",
    "model",
    "data",
    "artifact_destination",
)

BUDGET_KEYS = ("lifetime_human_budget", "total_optimizer_tokens")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_frozen(config: dict) -> bool:
    return config.get("_freeze_status") == "FROZEN"


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_config_exists_and_parses(path: Path) -> None:
    assert path.is_file(), f"{path.name} is missing"
    assert isinstance(load(path), dict)


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_required_keys_are_declared(path: Path) -> None:
    config = load(path)
    missing = [key for key in REQUIRED_KEYS if key not in config]
    assert not missing, f"{path.name} does not declare {missing}"


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_freeze_status_is_one_of_two_values(path: Path) -> None:
    status = load(path).get("_freeze_status")
    assert status in {"AWAITING_JULY_31_FREEZE", "FROZEN"}, (
        f"{path.name} has _freeze_status={status!r}; a config is either awaiting "
        "the freeze or frozen, never anything else"
    )


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_unfrozen_config_holds_no_scientific_values(path: Path) -> None:
    """An awaiting config must be visibly empty, so it cannot be mistaken for real."""
    config = load(path)
    if is_frozen(config):
        pytest.skip("config is frozen; structural tests below apply instead")

    filled = [
        key
        for key in BUDGET_KEYS + ("horizon", "seeds", "model", "data")
        if config.get(key) is not None
    ]
    assert not filled, (
        f"{path.name} is still AWAITING_JULY_31_FREEZE but has values for {filled}. "
        "Either it is frozen and should say so, or these values were invented."
    )


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_frozen_config_records_its_freeze_source(path: Path) -> None:
    config = load(path)
    if not is_frozen(config):
        pytest.skip("config is not frozen yet")
    assert config.get("_freeze_source"), (
        f"{path.name} is FROZEN but does not record which freeze supplied its values"
    )


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_frozen_config_has_positive_budgets_and_horizon(path: Path) -> None:
    config = load(path)
    if not is_frozen(config):
        pytest.skip("config is not frozen yet")

    for key in (*BUDGET_KEYS, "horizon"):
        value = config[key]
        assert isinstance(value, int) and not isinstance(value, bool), (
            f"{path.name}: {key} must be an integer, got {value!r}"
        )
    assert config["total_optimizer_tokens"] > 0
    assert config["horizon"] > 0
    assert config["lifetime_human_budget"] >= 0


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_frozen_config_has_an_ordered_seed_list(path: Path) -> None:
    config = load(path)
    if not is_frozen(config):
        pytest.skip("config is not frozen yet")

    seeds = config["seeds"]
    assert isinstance(seeds, list) and seeds, f"{path.name}: seeds must be a non-empty list"
    assert all(isinstance(seed, int) for seed in seeds), f"{path.name}: seeds must be integers"
    assert len(set(seeds)) == len(seeds), f"{path.name}: duplicate seeds"
    assert seeds == sorted(seeds), (
        f"{path.name}: the seed list must be in its frozen order; "
        "reordering changes which chain is which"
    )


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_frozen_config_names_its_model_and_data(path: Path) -> None:
    config = load(path)
    if not is_frozen(config):
        pytest.skip("config is not frozen yet")

    model = config["model"]
    for field in ("identifier", "revision", "tokenizer_revision"):
        assert model.get(field), f"{path.name}: model.{field} is required"

    data = config["data"]
    for field in ("train_manifest", "train_manifest_sha256"):
        assert data.get(field), f"{path.name}: data.{field} is required"


def test_reference_arms_declare_identical_budgets() -> None:
    """The fairness constraint, checked at config level before any compute is spent."""
    configs = {path.stem: load(path) for path in REFERENCE_ARMS}
    if not all(is_frozen(config) for config in configs.values()):
        pytest.skip("both reference arms must be frozen before budgets can be compared")

    for key in BUDGET_KEYS:
        values = {name: config[key] for name, config in configs.items()}
        assert len(set(values.values())) == 1, (
            f"budget mismatch on {key}: {values}. Compared arms must consume "
            "identical lifetime human-origin and total optimizer tokens."
        )


def test_reference_arms_use_the_same_seed_set() -> None:
    configs = {path.stem: load(path) for path in REFERENCE_ARMS}
    if not all(is_frozen(config) for config in configs.values()):
        pytest.skip("both reference arms must be frozen before seeds can be compared")

    seed_sets = {name: tuple(config["seeds"]) for name, config in configs.items()}
    assert len(set(seed_sets.values())) == 1, (
        f"paired analysis requires identical seed sets across arms: {seed_sets}"
    )


@pytest.mark.parametrize("path", ALL_PRIMARY, ids=lambda p: p.stem)
def test_config_documents_what_the_freeze_must_supply(path: Path) -> None:
    config = load(path)
    if is_frozen(config):
        pytest.skip("config is frozen; the checklist has served its purpose")
    assert config.get("_required_from_freeze"), (
        f"{path.name} must list what the freeze has to supply"
    )


def test_toy_config_is_not_marked_frozen() -> None:
    """The toy fixture is not a primary config and must never claim to be."""
    toy = load(CONFIG_DIR / "toy_cpu.json")
    assert toy.get("_freeze_status") is None
    assert toy.get("stage", "fixture") == "fixture"
