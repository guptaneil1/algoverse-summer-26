import json
from pathlib import Path

import pytest

from human_data_budget.analysis.generate import (
    FIXTURE_WARNING,
    aggregate_results,
    paired_summary,
    render_fixture_latex,
)


def make_result(
    *,
    policy: str,
    seed: int,
    nll_values: list[float],
    human_tokens: int = 100,
    total_tokens: int = 10_000,
    valid: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "run_id": f"fixture-{policy}-{seed}",
        "policy": policy,
        "chain_seed": seed,
        "budget_id": "fixture-budget-100",
        "generations_completed": len(nll_values),
        "valid": valid,
        "metrics": [
            {
                "generation": generation,
                "human_nll": value,
                "tail_retention": 0.5,
            }
            for generation, value in enumerate(nll_values)
        ],
        "consumed_human_tokens": human_tokens,
        "consumed_total_tokens": total_tokens,
        "exclusion_reason": None,
    }


def paired_fixture_results() -> list[dict[str, object]]:
    return [
        make_result(
            policy="joint",
            seed=101,
            nll_values=[3.0, 2.0, 1.0],
        ),
        make_result(
            policy="selection_only",
            seed=101,
            nll_values=[3.0, 3.0, 3.0],
        ),
        make_result(
            policy="joint",
            seed=202,
            nll_values=[4.0, 3.0, 2.0],
        ),
        make_result(
            policy="selection_only",
            seed=202,
            nll_values=[4.0, 4.0, 4.0],
        ),
    ]


def test_paired_summary_uses_complete_chain_pairs() -> None:
    summary = paired_summary(
        paired_fixture_results(),
        bootstrap_samples=100,
        bootstrap_seed=7,
    )

    assert summary["fixture_only"] is True
    assert summary["scientific_evidence"] is False
    assert summary["warning"] == FIXTURE_WARNING
    assert summary["paired_seeds"] == [101, 202]
    assert summary["human_token_budget"] == 100
    assert summary["total_optimizer_token_budget"] == 10_000
    assert summary["paired_mean_difference"] == pytest.approx(-2.0)
    assert summary["bootstrap_interval"] == [-2.0, -2.0]


def test_latex_output_is_visibly_fixture_only() -> None:
    summary = paired_summary(
        paired_fixture_results(),
        bootstrap_samples=100,
    )

    latex = render_fixture_latex(summary)

    assert latex.splitlines()[0] == f"% {FIXTURE_WARNING}"
    assert "Fixture-only paired NLL-regret analysis" in latex
    assert "joint mean AUC" in latex
    assert r"selection\_only mean AUC" in latex
    assert "Paired mean difference & -2.000000" in latex


def test_mismatched_seed_sets_are_rejected() -> None:
    results = paired_fixture_results()
    results.pop()

    with pytest.raises(ValueError, match="same chain seeds"):
        paired_summary(results)


def test_mismatched_human_budgets_are_rejected() -> None:
    results = paired_fixture_results()
    results[0]["consumed_human_tokens"] = 90

    with pytest.raises(ValueError, match="equal lifetime human tokens"):
        paired_summary(results)


def test_mismatched_total_budgets_are_rejected() -> None:
    results = paired_fixture_results()
    results[0]["consumed_total_tokens"] = 9_000

    with pytest.raises(ValueError, match="equal total optimizer tokens"):
        paired_summary(results)


def test_invalid_chains_are_not_aggregated() -> None:
    results = [
        make_result(
            policy="joint",
            seed=101,
            nll_values=[3.0, 2.0, 1.0],
        ),
        make_result(
            policy="joint",
            seed=202,
            nll_values=[9.0, 9.0, 9.0],
            valid=False,
        ),
    ]

    aggregate = aggregate_results(results)

    assert aggregate["policies"]["joint"]["chain_count"] == 1
    assert aggregate["warning"] == FIXTURE_WARNING

FIXTURE_ROOT = Path("tests/analysis/fixtures")
EXPECTED_LATEX = Path(
    "tests/analysis/expected/fixture_primary_results.tex"
)


def load_fixture_directory(
    directory_name: str,
) -> list[dict[str, object]]:
    directory = FIXTURE_ROOT / directory_name

    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]


def test_committed_fixture_latex_regenerates_exactly() -> None:
    results = load_fixture_directory("valid")

    summary = paired_summary(
        results,
        bootstrap_samples=5000,
        bootstrap_seed=0,
    )
    rendered = render_fixture_latex(summary)
    expected = EXPECTED_LATEX.read_text(encoding="utf-8")

    assert rendered == expected
    assert expected.splitlines()[0] == f"% {FIXTURE_WARNING}"


def test_all_committed_json_fixtures_are_labeled() -> None:
    paths = sorted(FIXTURE_ROOT.glob("*/*.json"))

    assert paths

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))

        assert payload["fixture_only"] is True, path
        assert payload["scientific_evidence"] is False, path
        assert payload["warning"] == FIXTURE_WARNING, path