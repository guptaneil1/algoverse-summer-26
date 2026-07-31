"""Fixture-only simulator for policy and analysis testing.

This does not train a language model and is not scientific evidence.
"""

from __future__ import annotations

from typing import Any

from human_data_budget.models import (
    Candidate,
    ChainResult,
    GenerationMetric,
    PolicyState,
)
from human_data_budget.policies import (
    JointPolicy,
    RandomPolicy,
    ScheduleOnlyPolicy,
    SelectionOnlyPolicy,
)
from human_data_budget.policies.base import Policy, validate_allocation

POLICY_NAMES = (
    "random",
    "schedule_only",
    "selection_only",
    "joint",
)


def build_policy(
    policy_name: str,
    *,
    horizon: int,
    per_generation_budget: int,
) -> Policy:
    """Construct one policy using a budget-matched fixture configuration."""
    if policy_name == "random":
        return RandomPolicy(per_generation_budget)

    if policy_name == "schedule_only":
        midpoint = horizon // 2

        return ScheduleOnlyPolicy(
            {
                generation: (
                    0
                    if generation < midpoint
                    else 2 * per_generation_budget
                )
                for generation in range(horizon)
            }
        )

    if policy_name == "selection_only":
        return SelectionOnlyPolicy(per_generation_budget)

    if policy_name == "joint":
        return JointPolicy(
            horizon=horizon,
            base_per_generation_budget=per_generation_budget,
        )

    raise ValueError(f"unknown policy: {policy_name}")


def simulate_policy(
    policy_name: str,
    *,
    chain_seed: int,
    horizon: int = 10,
    lifetime_human_budget: int = 100,
    total_optimizer_tokens: int = 10_000,
    hidden_modes: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Run one complete fake recursive chain.

    The common and tail modes degrade at different rates. Rescue reduces the
    degradation of the selected mode. Hidden modes are removed from the
    policy-visible monitoring state but remain in the true simulated state.
    """
    if horizon <= 0:
        raise ValueError("horizon must be positive")

    if lifetime_human_budget <= 0:
        raise ValueError("lifetime_human_budget must be positive")

    if lifetime_human_budget % horizon != 0:
        raise ValueError(
            "fixture lifetime budget must divide evenly across generations"
        )

    per_generation_budget = lifetime_human_budget // horizon

    # Each candidate costs exactly one generation's budget, so every policy
    # can consume an exactly matched lifetime budget.
    candidates = (
        Candidate(
            example_id="common-example",
            human_token_count=per_generation_budget,
            mode="common",
            undercoverage_score=0.0,
        ),
        Candidate(
            example_id="tail-example",
            human_token_count=per_generation_budget,
            mode="tail",
            undercoverage_score=0.0,
        ),
    )

    policy = build_policy(
        policy_name,
        horizon=horizon,
        per_generation_budget=per_generation_budget,
    )

    # True undercoverage is used for evaluation.
    true_undercoverage = {
        "common": 0.10,
        "tail": 0.20,
    }

    # Tail data deteriorates faster in this toy world.
    degradation_rates = {
        "common": 0.04,
        "tail": 0.10,
    }

    rescue_effect = {
        "common": 0.08,
        "tail": 0.14,
    }

    remaining_budget = lifetime_human_budget
    consumed_human_tokens = 0

    metrics: list[GenerationMetric] = []
    allocations: list[dict[str, Any]] = []

    for generation in range(horizon):
        observed_statistics = {
            mode: score
            for mode, score in true_undercoverage.items()
            if mode not in hidden_modes
        }

        state = PolicyState(
            generation=generation,
            remaining_human_tokens=remaining_budget,
            mode_statistics=observed_statistics,
            candidates=candidates,
            history=tuple(allocations),
        )

        allocation = policy.allocate(
            state,
            seed=chain_seed * 1000 + generation,
        )
        validate_allocation(allocation, state)

        remaining_budget -= allocation.selected_human_tokens
        consumed_human_tokens += allocation.selected_human_tokens
        allocations.append(allocation.as_dict())

        rescued_modes = set(allocation.mode_allocations)

        for mode in true_undercoverage:
            true_undercoverage[mode] += degradation_rates[mode]

            if mode in rescued_modes:
                true_undercoverage[mode] -= rescue_effect[mode]

            true_undercoverage[mode] = min(
                1.0,
                max(0.0, true_undercoverage[mode]),
            )

        mean_undercoverage = (
            sum(true_undercoverage.values()) / len(true_undercoverage)
        )

        metrics.append(
            GenerationMetric(
                generation=generation,
                human_nll=3.0 + mean_undercoverage,
                tail_retention=max(
                    0.0,
                    1.0 - true_undercoverage["tail"],
                ),
            )
        )

    if consumed_human_tokens != lifetime_human_budget:
        raise ValueError(
            f"{policy_name} consumed {consumed_human_tokens} human tokens; "
            f"expected exactly {lifetime_human_budget}"
        )

    chain_result = ChainResult(
        run_id=f"fixture-{policy_name}-seed-{chain_seed}",
        policy=policy_name,
        chain_seed=chain_seed,
        budget_id=f"fixture-budget-{lifetime_human_budget}",
        generations_completed=horizon,
        valid=True,
        metrics=tuple(metrics),
        consumed_human_tokens=consumed_human_tokens,
        consumed_total_tokens=total_optimizer_tokens,
    )

    return {
        "fixture_only": True,
        "scientific_evidence": False,
        "warning": (
            "Synthetic implementation test only. "
            "No language model was trained."
        ),
        "hidden_modes": sorted(hidden_modes),
        "allocations": allocations,
        "chain_result": chain_result.as_dict(),
    }


def simulate_all_policies(
    *,
    chain_seed: int,
    hidden_modes: frozenset[str] = frozenset(),
) -> dict[str, dict[str, Any]]:
    """Run every policy from the same initial state and chain seed."""
    return {
        policy_name: simulate_policy(
            policy_name,
            chain_seed=chain_seed,
            hidden_modes=hidden_modes,
        )
        for policy_name in POLICY_NAMES
    }