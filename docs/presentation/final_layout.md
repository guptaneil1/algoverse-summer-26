# Final Presentation Layout

Result-independent. Every slide carrying a number sources it from a generated
file; no value is typed onto a slide. The talk must be deliverable unchanged
whether the primary result is favourable, null, harmful, uncertain, or absent —
only the outcome slide's template changes.

**Total: 12 minutes + 3 minutes questions.**

| # | Slide | Purpose | Evidence source | Speaker goal | Time |
|---|---|---|---|---|---|
| 1 | Title | Identify the work and the team | — | Name the resource-allocation framing immediately, not "model collapse" | 0:20 |
| 2 | The finite-human-data problem | Motivate scarcity | CLAIMS.md C-001, `sources.yaml` | Establish that recursive training degrades in *some* workflows and is stable in others | 1:00 |
| 3 | The question | State the exact problem | CLAIMS.md C-002 | One fixed lifetime budget: **when** to spend, and **which** modes to buy | 1:00 |
| 4 | Four policies | Define the comparison | `configs/policy/*.json` | Random, schedule-only, selection-only, joint — all at identical budgets | 1:20 |
| 5 | What makes it a fair test | Budget matching | PROTOCOL.md, `test_budget_matching.py` | Identical lifetime human-origin *and* total optimizer tokens, counted from realized batches | 1:00 |
| 6 | The chain is the unit | Pre-empt the stats question | PROTOCOL.md, `aggregate_chain_results.py` | 3 chains x 10 generations is n=3; say it before a reviewer does | 0:50 |
| 7 | Outcomes | Define measurement | `evaluation/`, PREREGISTRATION.md | Held-out human NLL and tail retention, on a partition never used for selection | 1:00 |
| 8 | Validity by construction | Show the guardrails | `validation/`, `week3_adversarial_audit.md` | Independent validator returns valid / invalid / valid_with_limitation; a bad result is still valid | 1:20 |
| 9 | **Primary result** | Report the outcome | **GENERATED** — `results/aggregates/`, table via `generate_tables.py` | Read the precommitted template for whichever outcome occurred | 1:40 |
| 10 | Monitoring-omission stress test | Show the failure boundary | PREREGISTRATION.md C-003 | Where targeted allocation should stop working, and whether it did | 1:00 |
| 11 | What we can and cannot claim | Scope discipline | CLAIMS.md, `outcome_contingent_language.md` | Say the narrow claim out loud; name what is still untested | 1:10 |
| 12 | Limitations | Pre-empt objections | `paper/sections/08_limitations.tex` | Pilot scale, one domain, one model size, seed count, validity limits | 1:00 |
| 13 | Contribution and next steps | Close honestly | CLAIMS.md C-004 | Recursive + fixed lifetime human-token budget + matched non-joint baselines | 0:40 |

## Slide 9 — the only outcome-dependent slide

The layout is fixed; the content is selected, never written on the day:

- **Placeholder before the freeze:** `RESULT_PENDING — awaiting the immutable
  chain-level aggregate.` This is what the slide says if nothing completed. It is
  an acceptable slide to present.
- **After the freeze:** insert the generated table or figure by stable filename
  and read the matching template from
  [`paper/outcome_contingent_language.md`](../../paper/outcome_contingent_language.md).
- The interval and unit (`n = <chains>`) appear on the slide itself, not only in
  the script.

## Rules for the deck

1. No figure is hand-drawn from a result. Diagrams are result-independent
   (pipeline, partitions, policy timing) or generated from a frozen aggregate.
2. Banned on any slide: *first*, *optimal*, *prevents collapse*, *solves*,
   *state of the art*, unqualified *novel*.
3. If the primary result is null or harmful, slides 9 and 13 use those templates.
   Do not re-scope the question after seeing the outcome.
4. Slide 8 is the differentiator at pilot scale. If the result is null, the
   validity infrastructure is the contribution — present it that way rather than
   apologising for the null.

## Rehearsal check

Deliver the talk three times, once each assuming a favourable, a null, and an
absent primary result. If any run requires rewriting a slide other than 9, the
deck is not yet outcome-independent.
