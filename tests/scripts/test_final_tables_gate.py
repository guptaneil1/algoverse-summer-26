"""Tests for `scripts/generate_final_tables.py`, and for its budget gate in particular.

The pilot produced perfectly readable numbers for comparisons that were not
interpretable, because one arm had received ten per cent less human data
(`FAILURE_LOG.md` F-020) and the totals differed by more than the permitted spread
(F-021). The gate exists so a table cannot print those numbers as though they were
results.

Three of the pilot's seven defects shared one shape: a check whose intent was
documented and whose implementation did not achieve it, with no test asserting the
intent. So the gate is asserted here in both directions -- it fires when an axis is
violated, and it does not fire when both axes hold.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


final_tables = load_script("generate_final_tables")

# Practical-equivalence half-width in outcome units: 2% of the baseline arm's AUC
# regret, which is 0.45 for the fixture below. The gate is the separate, tighter
# quantity P-008 sets.
THRESHOLD_UNITS = 0.009
PERMITTED = 0.2


def chain(policy: str, seed: int, human: int, total: int, drift: float) -> dict:
    """One chain whose NLL rises by ``drift`` per generation from a common start."""
    return {
        "policy": policy,
        "chain_seed": seed,
        "consumed_human_tokens": human,
        "consumed_total_tokens": total,
        "generations_completed": 4,
        "valid": True,
        "exclusion_reason": None,
        "metrics": [
            {"generation": g, "human_nll": 3.0 + drift * g, "tail_retention": 1.0 - 0.01 * g}
            for g in range(4)
        ],
    }


def arms(treatment_human: int, treatment_total: int) -> dict[str, list[dict]]:
    return {
        "random": [chain("random", s, 750_000, 16_000_000, 0.10) for s in (101, 202, 303)],
        "selection_only": [
            chain("selection_only", s, treatment_human, treatment_total, 0.08)
            for s in (101, 202, 303)
        ],
    }


def test_gate_passes_when_both_axes_hold():
    contrast = final_tables.contrast(
        arms(750_000, 16_000_000), "selection_only", "random"
    )
    label, reportable = final_tables.verdict(contrast, THRESHOLD_UNITS, PERMITTED)

    assert reportable, "a contrast matched on both axes must be reportable"
    assert label == "beneficial", label


def test_gate_fires_on_the_human_axis():
    # Ten per cent less human data: the F-020 shape.
    contrast = final_tables.contrast(
        arms(675_000, 16_000_000), "selection_only", "random"
    )
    _, reportable = final_tables.verdict(contrast, THRESHOLD_UNITS, PERMITTED)

    assert not reportable


def test_gate_fires_on_the_total_axis():
    # Human spend matched, totals apart by more than the permitted spread: F-021.
    contrast = final_tables.contrast(
        arms(750_000, 16_300_000), "selection_only", "random"
    )
    _, reportable = final_tables.verdict(contrast, THRESHOLD_UNITS, PERMITTED)

    assert not reportable


def test_a_gated_row_prints_no_numbers():
    """The rendered row must not carry the effect it is refusing to establish."""
    contrast = final_tables.contrast(
        arms(675_000, 16_000_000), "selection_only", "random"
    )
    rendered = "\n".join(
        final_tables.table_contrasts(
            None, [contrast], THRESHOLD_UNITS, PERMITTED, "note", "run", "source"
        )
    )

    assert "not established" in rendered
    assert f"{contrast['mean']:.4f}" not in rendered


def test_an_interval_inside_the_equivalence_region_is_negligible():
    """The primary result's shape: matched, precise, and practically equivalent."""
    contrast = final_tables.contrast(
        arms(750_000, 16_000_000), "selection_only", "random"
    )
    # A region wide enough to contain the whole interval turns the same numbers from a
    # beneficial effect into a negligible one. That is the preregistered rule, not a
    # judgement call at reporting time.
    label, reportable = final_tables.verdict(contrast, 0.5, PERMITTED)

    assert reportable
    assert label == "negligible", label


def test_the_permitted_spread_is_the_projects_own():
    """The gate must track P-008, not a constant copied into this script."""
    from human_data_budget.runner.budget_matching import SPREAD_MARGIN_BELOW_THRESHOLD

    assert final_tables.SPREAD_MARGIN_BELOW_THRESHOLD is SPREAD_MARGIN_BELOW_THRESHOLD
