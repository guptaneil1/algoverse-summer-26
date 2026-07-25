"""Deterministic toy generation step producing small fixture examples.

No real model generates text here. ``toy_generate_step`` exists so the
runner orchestration (checkpoint/resume/manifest) can be exercised end to
end before a real generation pipeline lands behind the same contract.
"""

from __future__ import annotations

import random
from typing import Any

_TOY_VOCAB = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta")


def toy_generate_step(state: dict[str, Any], seed: int) -> dict[str, Any]:
    """Return deterministic synthetic fixture examples for one generation.

    The same ``state`` and ``seed`` always produce byte-identical output.
    Randomness is drawn only from a ``random.Random(seed)`` instance local to
    this call; no global or unseeded randomness is used.
    """

    rng = random.Random(seed)
    generation = int(state.get("generation", 0))
    count = int(state.get("examples_per_generation", 2))
    examples = []
    for index in range(count):
        length = rng.randint(3, 6)
        tokens = [rng.choice(_TOY_VOCAB) for _ in range(length)]
        examples.append(
            {
                "example_id": f"synthetic-g{generation}-{index}",
                "text": " ".join(tokens),
                "origin": "synthetic",
                "generation": generation,
            }
        )
    return {"generation": generation, "seed": seed, "examples": examples}
