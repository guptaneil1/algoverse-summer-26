import json
from pathlib import Path

from human_data_budget.runner.chain import run_toy_chain
from human_data_budget.runner.schema import validate_json

ROOT = Path(__file__).resolve().parents[2]


def test_toy_artifacts_match_schemas() -> None:
    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text())
    manifest, result = run_toy_chain(config)
    validate_json(manifest, ROOT / "schemas/run_manifest.schema.json")
    validate_json(result.as_dict(), ROOT / "schemas/chain_result.schema.json")
