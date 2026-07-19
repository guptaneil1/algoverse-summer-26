import json
from pathlib import Path

from human_data_budget.runner.chain import run_toy_chain

ROOT = Path(__file__).resolve().parents[2]


def test_toy_chain_is_deterministic_and_complete() -> None:
    config = json.loads((ROOT / "configs/experiment/toy_cpu.json").read_text())
    first = run_toy_chain(config)
    second = run_toy_chain(config)
    assert first == second
    _, result = first
    assert result.generations_completed == config["horizon"]
    assert result.consumed_human_tokens <= config["lifetime_human_budget"]
