"""Adapter contracts for swapping real training/generation into the chain runner.

Implements the `docs/weekly/WEEK_2.md` Khantushig clause "Prepare the real pilot
runner adapter against frozen Week 1 contracts."

`runner/chain.py` currently calls three concrete toy implementations directly:
``toy_train_step``, ``toy_generate_step``, and ``NullEvaluator.evaluate``. A real
pilot must substitute GPU-backed implementations for the first two without
touching orchestration — checkpointing, resume, manifests, failure capture, and
budget accounting all stay identical.

This module states the shape those replacements must have. The Protocols are
transcribed from the existing call sites, so conformance is checkable **today**
against the toy implementations (see ``tests/runner/test_adapter_contract.py``)
rather than discovered when a real trainer is first plugged in.

Nothing here trains a model. It is a typed contract plus a component bundle.

Design notes
------------
Protocols rather than base classes: a real implementation is likely to be a
closure over a loaded model, or a bound method on a trainer object, and should
not be forced to inherit from this package.

``ChainComponents`` is the injection point. ``toy_components()`` returns the
current fixture behaviour, so a future ``run_toy_chain(..., components=...)``
parameter can default to it and leave every existing caller unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TrainStep(Protocol):
    """One optimizer pass over this generation's training mixture.

    Transcribed from ``chain.py``::

        train_state = {"generation": generation, "consumed_tokens": consumed_human}
        toy_train_step(train_state, policy_seed)

    A real implementation must:

    - be deterministic given ``(state, seed)``, per ``PROTOCOL.md`` §3 seed
      propagation;
    - return a JSON-serializable dict, because the runner may checkpoint it;
    - report tokens actually consumed by the optimizer, never an estimate
      (``PROTOCOL.md`` §3 token accounting).
    """

    def __call__(self, state: dict[str, Any], seed: int) -> dict[str, Any]: ...


@runtime_checkable
class GenerateStep(Protocol):
    """Produce this generation's synthetic corpus from the just-trained model.

    Transcribed from ``chain.py``::

        generate_state = {"generation": generation, "examples_per_generation": 2}
        toy_generate_step(generate_state, policy_seed)

    A real implementation must emit records carrying ``example_id``, ``origin``
    (``"synthetic"``), and ``generation``, so provenance survives into the next
    generation's training mixture.
    """

    def __call__(self, state: dict[str, Any], seed: int) -> dict[str, Any]: ...


@runtime_checkable
class Evaluator(Protocol):
    """Held-out evaluation of one generation's checkpoint.

    Keyword-only, matching ``NullEvaluator.evaluate``. A real implementation must
    never read the final-test partition for anything that feeds selection,
    thresholds, early stopping, or hyperparameters (``PROTOCOL.md`` §3).
    """

    def evaluate(
        self,
        *,
        run_id: str,
        generation: int,
        checkpoint_sha256: str,
        evaluation_manifest_sha256: str,
        current_mode_scores: dict[str, float],
        reference_mode_scores: dict[str, float],
        tail_modes: set[str],
        target_log_probabilities: list[float],
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ChainComponents:
    """The three swappable pieces of one recursive generation.

    Everything else in ``chain.py`` — checkpointing, resume, manifest
    transitions, failure capture, allocation validation — is orchestration and is
    not swappable. Keeping the boundary this narrow is what lets the pilot reuse
    the tested resume path instead of reimplementing it.
    """

    train_step: TrainStep
    generate_step: GenerateStep
    evaluator: Evaluator
    label: str = "toy"

    @property
    def is_fixture(self) -> bool:
        """True when these components train no real model.

        The runner should stamp this into the manifest so a chain produced by
        fixture components can never be mistaken for a pilot chain.
        """
        return self.label == "toy"


def toy_components() -> ChainComponents:
    """Return the fixture components ``chain.py`` currently uses.

    Imported lazily so that importing this module does not pull in the toy
    implementations for callers that only want the Protocols.
    """
    from human_data_budget.generation.toy import toy_generate_step
    from human_data_budget.runner.evaluator import NullEvaluator
    from human_data_budget.training.toy import toy_train_step

    return ChainComponents(
        train_step=toy_train_step,
        generate_step=toy_generate_step,
        evaluator=NullEvaluator(),
        label="toy",
    )
