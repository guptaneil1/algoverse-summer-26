# The Human Data Budget

> **Status: design and verification stage — no experimental results yet.**

This repository studies a provisional research question in recursive language-model training:

> Under a fixed lifetime budget of human-origin tokens, when should those tokens be used, and which under-covered parts of the human distribution should they target?

The project is intended to test whether a joint time-and-mode allocation policy can preserve model quality more efficiently than fresh random mixing, schedule-only allocation, selection-only allocation, and data accumulation.

## Current status

| Component | Status |
|---|---|
| Research framing | Provisional |
| Literature review | Active; novelty not established |
| Published positive-control reproduction | Not started |
| Training and generation pipeline | Not implemented |
| Human Data Budget method | Not implemented |
| Experimental results | None |
| Main-conference claim | Not yet supported |

The immediate milestone is to reproduce a published ten-generation recursive-training condition from the official Drayson et al. implementation. Novel experiments are blocked until that reproduction and the required leakage, token-accounting, determinism, hashing, and resume checks pass.

## Contribution under test

The intended contribution is **not** that human data helps, that fresh data helps, that high-surprise samples are useful, or that scheduling matters. Prior work already addresses those ideas separately.

The provisional contribution is the joint problem of allocating a **finite lifetime human-token budget** across:

1. recursive generations;
2. budget amount per generation; and
3. under-covered modes of a human reference distribution;

while measuring how biased or incomplete monitoring can make targeted selection fail.

This wording remains provisional until the closest-work search and external novelty review are complete.

## Evidence gates

The project must pass these gates in order:

1. Truthful repository and claim ledger.
2. Hostile closest-work and contradiction search.
3. Published positive-control reproduction.
4. Data leakage, provenance, exact-token, determinism, and resume tests.
5. Small 160M mechanism pilot and chain-level power analysis.
6. Powered multi-scale and multi-domain confirmation.
7. Independent mock review using the current NeurIPS criteria.

See [PLAN.md](PLAN.md) for the complete go/no-go sequence.

## Repository contents

```text
.
├── README.md
├── PLAN.md
├── CONTRIBUTING.md
├── DECISIONS.md
├── CLAIMS.md
├── PROTOCOL.md
├── PREREGISTRATION.md
├── COMPUTE.md
├── FAILURE_LOG.md
├── docs/
│   ├── STATUS.md
│   └── evidence/
│       ├── claims.yaml
│       └── sources.yaml
├── data/
│   ├── README.md
│   └── manifests/README.md
└── results/
    ├── README.md
    └── aggregates/README.md
```

There is currently no `src/`, `scripts/`, `configs/`, `tests/`, CI workflow, checkpoint, or result figure because those artifacts do not yet exist.

## Research rules

- No result may be entered manually into the README or paper.
- Every result must trace to a run manifest and a versioned analysis command.
- Every literature claim must point to a primary source and its exact supporting location.
- “First,” “novel,” “optimal,” and “prevents collapse” are prohibited until specifically established.
- Recursive chains—not generations or individual samples—are the experimental units.
- Expensive runs are prohibited until novelty, reproduction, leakage, power, baseline, and compute gates pass.
- Failed and contradictory results are retained in [FAILURE_LOG.md](FAILURE_LOG.md).

## Target

The working target is a future NeurIPS main-track submission, currently planned around the 2027 cycle. The official rules for that cycle must be rechecked when released. A 2026 workshop may be used only for feedback, not as evidence that the main-track bar has been reached.

## License

This repository is released under the [MIT License](LICENSE).
