# Ten-Minute Presentation Outline

## 0:00-0:55 - Motivation without hype

- Define recursive model-data chains and the range of observed degradation endpoints.
- Explain why “model collapse is inevitable” is too broad: accumulation, real-data mixing, verification, and curation can stabilize some workflows.
- Human-origin data can be licensed, scarce, costly to curate, or deliberately reserved, so allocation matters.

## 0:55-1:45 - Formal question

- Horizon $G$, monitored modes $M$, lifetime human-origin optimizer-token budget $B$, total optimizer-token budget $T$.
- Allocation $b_{g,m}$ satisfies $\sum_{g,m} b_{g,m}=B$; repeated presentations count repeatedly and padding follows one frozen rule.
- Question: does joint allocation across generation and mode outperform the strongest eligible matched non-joint policy?

## 1:45-2:45 - Four policies and fair baselines

- Fresh random, schedule-only, selection-only, joint.
- No-rescue is diagnostic; accumulation, fixed-fraction, detector-resampling, and oracle conditions are added when feasible.
- Explain what each policy can observe and why final-test information is excluded.
- Deterministic tie-breaking and stable IDs make decisions auditable.

## 2:45-3:40 - Closest work and novelty threat

- Recursive mixing/accumulation: Alemohammad, Gerstgrasser, Kazdan, Drayson.
- Dynamic domain mixtures: DoReMi, RegMix, RegMix-D, TiKMiX.
- July 2026 additions: KITE targets current weaknesses under an equal labeling budget; Qiao et al. prove hazards from fragmented monitoring references.
- Allowed distinction uses all qualifiers: recursive chain, one lifetime human-origin optimizer-token stock, allocation across generation and monitored human modes, and matched schedule-only/selection-only controls.
- `PENDING_EXTERNAL_REVIEW`: no first-of-kind statement until a qualified outsider completes the hostile review.

## 3:40-4:30 - Positive control

- Reproduce Drayson et al.'s fully synthetic and human-mixed official arms.
- Pin upstream commit, assets, model/tokenizer, data, decoding, horizon, expected ordering, endpoint, and tolerance before running.
- A complete evidence-backed failure is acceptable; relabeling failure as success is not.

## 4:30-5:35 - Data and experimental design

- One legally usable domain and one screening-scale model.
- Five disjoint manifest-backed partitions with exact and near-duplicate checks.
- Paired chains share starting assets, seed, prompts, evaluation data, budgets, and frozen configs.
- Resume must preserve the declared scientific state or meet an honest frozen tolerance.

## 5:35-6:30 - Metrics and analysis

- Held-out human NLL excludes padding and records token count.
- Aggregate generation-wise NLL regret into a chain-level area under the curve.
- Freeze one independent tail-retention metric after reliability checks.
- Paired chain-level contrast; uncertainty across chains, not generations.
- Primary budget, horizon, baseline-selection rule, meaningful-effect threshold, and multiplicity treatment are preregistered.

## 6:30-7:20 - Monitoring-omission intervention

- Policy monitor hides one important mode; untouched evaluation retains it.
- A targeted policy may look efficient locally while damaging global distribution support.
- Connect to Qiao et al.; describe this as a transfer/falsification test under human-rescue token accounting.

## 7:20-8:00 - Artifact and validity controls

- Immutable manifests; hashes for configs, checkpoints, generations, and figures.
- Exact allocation history and optimizer-consumed human/total token counters.
- Failure log preserves divergent and interrupted runs.
- Tables/figures generated from validated chain results only.

## 8:00-8:55 - Limitations

- One domain and small model do not establish frontier-scale or universal behavior.
- Monitored modes can be incomplete or noisy.
- Equal token counts do not equal licensing cost or information content.
- Limited chain count may yield wide uncertainty.
- Strong alternatives may dominate or remain unaffordable to implement fully.

## 8:55-9:40 - Outcome-contingent conclusion

- Favorable: narrow improvement under the frozen setting.
- Equivalent: simpler baseline preferred.
- Harmful: joint rule not supported; identify main or omission-condition harm.
- Inconclusive: interval spans decision regions.
- Invalid: no efficacy conclusion after positive-control, leakage, accounting, or artifact failure.
- Novelty failure: withdraw novelty even if experiments are favorable.

## 9:40-10:00 - Current status

- Result-independent manuscript and presentation language are prepared.
- Two new high-threat 2026 papers are audited.
- `RESULT_PENDING`: novel-treatment outcomes are not available.
- Remaining gates belong to the positive-control, data/evaluation, method/preregistration, and external-review owners.
