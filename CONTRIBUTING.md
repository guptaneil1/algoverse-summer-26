# Contributing

This repository uses evidence-gated research rather than feature-driven development.

## Before opening a pull request

Confirm that the change:

- does not describe planned work as implemented;
- does not add an experimental number without a run manifest;
- does not weaken data-partition or provenance controls;
- updates `CLAIMS.md` when scientific wording changes;
- updates `DECISIONS.md` when a protocol choice changes;
- updates `FAILURE_LOG.md` when a run or attempted replication fails;
- records primary sources in `docs/evidence/sources.yaml`;
- keeps generated results separate from manually written documentation.

## Claim labels

Every nontrivial research statement should be treated as one of:

- **Fact:** supported by a cited primary source.
- **Inference:** derived from facts, with assumptions stated.
- **Hypothesis:** a falsifiable statement not yet tested.
- **Decision:** a project choice, not a scientific fact.
- **Result:** supported by immutable run artifacts and analysis code.
- **Unknown:** unresolved and not safe to present as fact.

## Blocking review checklist

- [ ] Exact claim and scope are stated.
- [ ] Strongest counterargument is documented.
- [ ] Closest primary source is cited.
- [ ] Data and model revisions are pinned when applicable.
- [ ] Experimental unit and independence are correct.
- [ ] Token budgets are exact rather than approximate.
- [ ] Randomness and exclusions are recorded.
- [ ] Output is reproducible from an exact command.
- [ ] Failure conditions are stated.

No expensive experiment should be merged before the novelty, positive-control, leakage, baseline, power, and compute gates in `PLAN.md` pass.
