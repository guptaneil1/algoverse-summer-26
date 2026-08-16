# Week 3 Positive-Control Verification

> **STATUS: VERIFIED BY INDEPENDENT RECOMPUTATION — NOT RERUN.**
> The Week 2 comparison was checked, not re-executed. Every value below was
> recomputed in this repository from the raw per-generation `eval_results.json`
> artifacts, independently of the summary files that also record them. All four
> frozen ordering claims hold and the recomputed ratios match the recorded ones
> exactly.
>
> The packet permits this: the Week 2 comparison is *"rerun **or checked**
> cleanly under its frozen protocol."* This is the check. What it cannot do is
> re-verify artifact bytes that no longer exist (§5).

The positive control asks one question: **does this pipeline reproduce a result
somebody else already published?** Until it does, no primary contrast can be
interpreted as evidence about allocation policy — a pipeline that cannot
reproduce a known result cannot be trusted to measure an unknown one.

Source of record: `week-2/khantushig-positive-control`, merged into
`integration/week-2-jul25-jul31` as PR #16. Full report and ledger live there
(`docs/positive_control/report.md`, `expected_vs_observed.md`); this file records
the Week 3 verification of it.

---

## 1. Upstream pin — resolved

| Field | Value |
|---|---|
| Upstream repository | `https://github.com/GeorgeDrayson/model_collapse` |
| Exact commit | `feb8511479a2e2dc868e1caf3f63cb99f1fcc746` |
| Published source | Drayson, Yilmaz & Lampos, EMNLP 2025 (`2025.emnlp-main.1506`) |
| Model / tokenizer | `openai-community/gpt2` @ `607a30d783dfa663caf39e06633721c8d4cfcd7e` |
| Dataset | `wikitext/wikitext-2-raw-v1` @ `b08601e04326c79dfdd32d625aee71d232d685c3` |
| Detector | `GeorgeDrayson/modernbert-ai-detection` @ `08f218f1d05791ad99c26ede421f69c781a50360` |
| Prepared train file | SHA-256 `77557c8514b11406580aa7d48515ad303eeb0b0748247b0fe76fb24e927ef9d6` |

Recorded in `docs/positive_control/resolved_identifiers.json`. The earlier
*"upstream commit still unpinned"* blocker in `docs/STATUS.md` is stale.

## 2. Frozen expected comparison

Frozen 2026-08-03, **before either arm ran**, in `PROTOCOL.md`
("Frozen endpoint, ordering, and tolerance"):

| Claim | Frozen expectation |
|---|---|
| 1 | `ratio(fully_synthetic) > 1.0` |
| 2 | `ratio(human_mixed) > 1.0`, strictly below the synthetic arm |
| 3 | `ratio(fully_synthetic) > ratio(human_mixed) > 1.0` |
| 4 | synthetic ≥ mixed for the majority of generations 1–10 |

Endpoint: `test_perplexity_at_final_generation`; ratio is `ppl₁₀ / ppl₀`;
engineering tolerance 5%.

## 3. Verification command

```bash
# Recompute both ratios and all four ordering claims from raw eval artifacts,
# independently of positive_control_result.json.
git show week-2/khantushig-positive-control:docs/positive_control/measurements/\
<arm>/generation_<NN>/eval_results.json
```

Inputs: 22 `eval_results.json` files (11 generations × 2 arms), each committed to
git and each carrying `perplexity`, `eval_loss`, and `eval_accuracy`.

## 4. Observed — recomputed 2026-08-12

| Quantity | Recomputed | Recorded in `positive_control_result.json` | Agree |
|---|---:|---:|:--:|
| fully_synthetic ppl gen 0 | 29.6179 | 29.6179 | yes |
| fully_synthetic ppl gen 10 | 50.9806 | 50.9806 | yes |
| fully_synthetic degradation ratio | **1.7213** | 1.7213 | yes |
| human_mixed ppl gen 0 | 29.6179 | 29.6179 | yes |
| human_mixed ppl gen 10 | 30.3730 | 30.3730 | yes |
| human_mixed degradation ratio | **1.0255** | 1.0255 | yes |

Frozen claims, evaluated against the recomputed values:

| Claim | Observed | Verdict |
|---|---|---|
| 1 | 1.7213 > 1.0 | **holds** |
| 2 | 1.0255 > 1.0 and 1.0255 < 1.7213 | **holds** |
| 3 | 1.7213 > 1.0255 > 1.0 | **holds** |
| 4 | synthetic ≥ mixed at **10 of 10** generations | **holds** |

Both arms share generation 0 by construction, so 29.6179 is one number computed
once, not two that happen to agree. The arms diverge from generation 1 and never
re-cross.

## 5. Deviations and limitations

Carried forward from `expected_vs_observed.md`; none is tuned away.

1. **The numeric comparison against published values was not pre-registered.**
   The paper was obtained 2026-08-07, after both arms had run and been committed.
   Both arms fall inside 5% on every published quantity (worst deviation 2.27%),
   but the comparison is post-hoc and is labelled as such.
2. **The published horizon is generation 9; this project's is generation 10.**
   The numeric comparison is made at the paper's Gen 9 endpoint.
3. **Artifact bytes are gone (§6).** Recorded hashes cannot be re-verified.
4. **`data_selection=no-selection`** overrides upstream's importance-sampling
   default, so the comparator is the paper's `baseline` row, not `ours`.
   Recorded as PROTOCOL.md deviation 1.
5. **Diversity, self-BLEU, MAUVE and readability were not compared** — the
   generated corpora needed to compute them were lost with the container.
6. **Wall-clock figures derive from commit timestamps**, not a timer. Training
   and evaluation time are measured directly; generation time is a residual
   (`COMPUTE.md`).

## 6. Artifact traceability

| Category | Count | Bytes retained | Re-verifiable |
|---|---:|---|---|
| Evaluation outputs (`eval_results.json`) | 22 | **yes** — committed to git | yes |
| Model directories | 22 | no | no — hash only |
| Generated corpora (`data.json`) | 20 | no | no — hash only |
| **Total hashed** | **64** | 22 retained, 42 not | |

Every artifact was hashed at run time, before pruning, into each generation's
`artifact_record.json`; the unretained set is enumerated in
`measurements/artifact_retention.json` with its SHA-256 and recorded path. So
the *provenance chain is complete* — every artifact is named, hashed, and
accounted for — while 42 of 64 hashes are **permanently unverifiable** because
the Kaggle container was reclaimed at session end.

This is a genuine weakening of the evidence chain, not a technicality. What it
does **not** weaken: the scientific measurements themselves. Every value used in
§4 comes from an `eval_results.json` that is retained and in git.

## 7. Scientific consequence

- ☑ **Matched within the frozen tolerance**, with limitations. All four frozen
  ordering claims hold on recomputation, and both arms sit inside the 5%
  engineering band against the published values. The pipeline reproduces a known
  result, so primary contrasts may be interpreted normally **once they exist**.
- The overall classification stays **`valid_with_limitation`**, not `valid`,
  because of §5.1 (post-hoc numeric comparison) and §5.3 / §6 (unverifiable
  artifact hashes). Recording it as a clean pass would overstate it.

No positive-control evidence is mixed with primary-chain results: no primary
chain exists. The consequence for trust in the pipeline is positive — the
recursive-degradation effect the project studies is reproduced here at the
expected magnitude and ordering.
