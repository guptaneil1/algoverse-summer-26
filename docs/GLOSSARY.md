# Glossary

**Recursive chain:** A complete sequence of dependent model generations under one independent chain seed and policy.

**Generation:** One step inside a recursive chain; not an independent experimental unit.

**Human-origin optimizer token:** A non-padding token originating from documented human data and actually consumed by an optimizer step. Repeated presentations count repeatedly.

**Lifetime budget:** Total human-origin optimizer tokens allowed across the entire recursive chain.

**Mode:** A frozen region or group in the human reference distribution, such as a semantic cluster. The operational definition must be documented before primary outcomes.

**Under-coverage:** A frozen measure indicating that a monitored mode is insufficiently represented or modeled relative to a human reference.

**Rescue:** Addition or increased presentation of human-origin examples during recursive training.

**Schedule-only:** A policy that changes allocation across generations without targeted mode selection.

**Selection-only:** A policy that targets examples/modes under a fixed time schedule.

**Joint policy:** A policy that chooses both time allocation and mode selection under one lifetime budget.

**Monitoring reference:** Data used to estimate coverage and guide selection; it must be distinct from the final test set.

**Monitoring bias:** Failure caused by an incomplete or distorted monitoring reference.

**Positive control:** A published condition expected to show a known direction/order, used to verify the experimental pipeline.

**NLL:** Negative log-likelihood on frozen held-out human data; lower is better under the fixed definition.

**NLL regret:** Difference between policy NLL and a frozen reference NLL definition.

**Tail retention:** Frozen evaluation of preservation of underrepresented human modes.

**Run manifest:** Immutable metadata linking a run to code, configs, assets, seeds, budgets, and environment.

**Fixture:** Small synthetic artifact used to develop one component without another person's live implementation.

**Primary result:** Outcome governed by the frozen primary protocol and completed by the results freeze.

**Exploratory result:** Later or non-primary analysis that cannot replace a failed primary outcome.
