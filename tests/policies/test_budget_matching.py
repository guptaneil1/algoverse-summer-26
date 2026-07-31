from human_data_budget.analysis.simulator import (
    POLICY_NAMES,
    simulate_all_policies,
)


def test_all_policies_match_lifetime_human_budget() -> None:
    results = simulate_all_policies(chain_seed=101)

    assert set(results) == set(POLICY_NAMES)

    consumed_human_tokens = {
        result["chain_result"]["consumed_human_tokens"]
        for result in results.values()
    }

    assert consumed_human_tokens == {100}


def test_all_policies_match_total_optimizer_budget() -> None:
    results = simulate_all_policies(chain_seed=101)

    consumed_total_tokens = {
        result["chain_result"]["consumed_total_tokens"]
        for result in results.values()
    }

    assert consumed_total_tokens == {10_000}


def test_budget_matching_survives_monitoring_omission() -> None:
    results = simulate_all_policies(
        chain_seed=101,
        hidden_modes=frozenset({"tail"}),
    )

    consumed_human_tokens = {
        result["chain_result"]["consumed_human_tokens"]
        for result in results.values()
    }
    consumed_total_tokens = {
        result["chain_result"]["consumed_total_tokens"]
        for result in results.values()
    }

    assert consumed_human_tokens == {100}
    assert consumed_total_tokens == {10_000}