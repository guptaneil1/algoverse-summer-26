# Five-Minute Presentation Outline

## 0:00-0:35 - Why the question matters

- Later models may train on earlier models' outputs; some recursive workflows lose fit, diversity, or tail support.
- Prior work also shows that accumulation, real-data mixing, verification, and selection can prevent degradation in particular settings.
- Our question is therefore not “is synthetic data bad?” but “how should a finite human-data budget be spent?”

## 0:35-1:10 - Exact research question

- Fix a recursive horizon, one lifetime stock of human-origin tokens actually consumed by the optimizer, and the same total training-token budget for every matched policy.
- Ask whether choosing both **when** to spend and **which monitored mode** to support improves chain-level outcomes over strong non-joint policies.
- State `RESULT_PENDING`: no novel result is asserted.

## 1:10-1:55 - Four policy families

1. Fresh random: fixed schedule, random eligible human examples.
2. Schedule-only: adapt when to spend; mode sampling stays neutral.
3. Selection-only: fixed time schedule; adapt which modes/examples receive support.
4. Joint: adapt both timing and targeting.

Emphasize that the central comparison is joint versus the strongest eligible schedule-only or selection-only baseline, not only versus no rescue.

## 1:55-2:40 - Experiment

- One licensed text domain; one 124M-160M screening model; paired independently seeded recursive chains.
- Five disjoint partitions: base training, rescue candidates, generation prompts, validation, final test.
- Positive-control reproduction is a gate before the novel pilot.
- Exact human-origin and total optimizer-token accounting prevents a policy from winning by training longer or replaying human examples without cost.

## 2:40-3:20 - Outcomes and validity

- Primary: area under held-out human NLL-regret across the full horizon.
- Co-primary: separately frozen tail-retention metric that is not the policy score.
- Generations within a chain are repeated observations; the chain is the experimental unit.
- Leakage, budget mismatch, failed hashes, or positive-control failure invalidate efficacy claims.

## 3:20-4:00 - Novelty and strongest threats

- Dynamic mixture methods already change data domains across training time.
- KITE already targets diagnosed weaknesses under an equal per-iteration labeling budget.
- Qiao et al. already show biased monitoring references can make recursive selection erase minority modes.
- Remaining claim is deliberately narrow: recursion + one lifetime human-token stock + time and mode allocation + matched non-joint baselines. External hostile review is still pending.

## 4:00-4:35 - Monitoring-bias test

- Hide one preregistered important mode from the policy monitor while keeping full evaluation unchanged.
- This tests whether targeting can efficiently optimize the wrong reference.
- It is a falsification/boundary test, not a claim that monitoring bias is newly discovered.

## 4:35-5:00 - Honest possible endings

- Win: joint improves the frozen outcome in this narrow setting.
- Tie: simpler non-joint policy is preferred.
- Harm: joint adaptation worsens performance or stability.
- Uncertain: intervals are too wide.
- Invalid: positive control, leakage, accounting, or artifact gates fail.

End: “The project is designed so every one of those outcomes can be reported honestly.”
