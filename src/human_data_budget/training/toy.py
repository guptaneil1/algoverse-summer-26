"""Deterministic toy training step standing in for a real optimizer update.

No real model is trained here. ``toy_train_step`` exists so the runner
orchestration (checkpoint/resume/manifest) can be exercised end to end before
a real training pipeline lands behind the same contract.
"""

from __future__ import annotations

import random
from typing import Any


def toy_train_step(state: dict[str, Any], seed: int) -> dict[str, Any]:
    """Return a small deterministic serializable training-state update.

    The same ``state`` and ``seed`` always produce byte-identical output.
    Randomness is drawn only from a ``random.Random(seed)`` instance local to
    this call; no global or unseeded randomness is used.
    """

    rng = random.Random(seed)
    generation = int(state.get("generation", 0))
    consumed_tokens = int(state.get("consumed_tokens", 0))
    loss_jitter = rng.uniform(-0.01, 0.01)
    weight_signature = rng.getrandbits(64)
    return {
        "generation": generation,
        "seed": seed,
        "consumed_tokens": consumed_tokens,
        "toy_loss": round(1.0 / (generation + 1) + loss_jitter, 6),
        "weight_signature": weight_signature,
    }
