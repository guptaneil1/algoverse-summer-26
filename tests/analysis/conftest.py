"""Synthetic chain results for aggregation tests."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


def build_chain_result(
    run_id: str,
    policy: str,
    chain_seed: int,
    *,
    nlls: tuple[float, ...] = (3.0, 3.5),
    tails: tuple[float, ...] = (0.9, 0.8),
    valid: bool = True,
    budget_id: str = "budget-a",
    exclusion_reason: str | None = None,
) -> dict[str, Any]:
    """Build one schema-valid chain result."""
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "policy": policy,
        "chain_seed": chain_seed,
        "budget_id": budget_id,
        "generations_completed": len(nlls),
        "valid": valid,
        "metrics": [
            {"generation": index, "human_nll": nll, "tail_retention": tail}
            for index, (nll, tail) in enumerate(zip(nlls, tails, strict=True))
        ],
        "consumed_human_tokens": 100,
        "consumed_total_tokens": 1000,
        "exclusion_reason": exclusion_reason,
    }


@pytest.fixture
def chain_payload() -> Callable[..., dict[str, Any]]:
    """Return the chain-result builder."""
    return build_chain_result


@pytest.fixture
def write_chain(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory writing one chain_result.json and returning its path."""

    def factory(payload: dict[str, Any], filename: str | None = None) -> Path:
        target = tmp_path / (filename or f"{payload['run_id']}.json")
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    return factory
