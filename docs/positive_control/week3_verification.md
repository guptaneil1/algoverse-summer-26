# Week 3 Positive-Control Verification

> **STATUS: NOT PERFORMED.**
> No positive-control verification has been run in this repository.
> `docs/STATUS.md` records the positive control as **not reproduced**. This file
> is the prepared record; nothing in it may be cited as evidence of a
> reproduction. Delete this banner only when the run below has actually
> completed.

The positive control asks one question: **does this pipeline reproduce a result
somebody else already published?** Until it does, no primary contrast can be
interpreted as evidence about allocation policy — a pipeline that cannot
reproduce a known result cannot be trusted to measure an unknown one.

---

## Blocker: the upstream commit is unpinned

The reference implementation is `github.com/GeorgeDrayson/model_collapse`. The
**exact commit** to reproduce has never been recorded — it is an unfilled TODO.

Pin it first, and record it here as a full 40-character SHA:

| Field | Value |
|---|---|
| Upstream repository | `https://github.com/GeorgeDrayson/model_collapse` |
| Exact commit | TODO(khantushig): 40-hex SHA, not a branch or tag name |
| Why this commit | TODO(khantushig): the commit the published comparison used |
| Retrieved on | TODO(khantushig) |

A branch name is not a pin — branches move. Nothing below can start until this
row holds a real SHA.

## Frozen expected comparison

What the published result claims, recorded **before** running anything so the
comparison cannot be adjusted afterwards.

| Field | Value |
|---|---|
| Published quantity | TODO(khantushig) |
| Published value | TODO(khantushig): from the paper or upstream artifact, cited |
| Tolerance | TODO(khantushig): frozen before the run, with its justification |
| Source of the tolerance | TODO(khantushig): nondeterminism budget, not a value chosen to pass |

Freezing the tolerance in advance is the whole point. A tolerance widened after
seeing a mismatch converts a failed control into a passed one.

## Exact command and assets

```bash
# TODO(khantushig): the exact command, from the pinned commit
```

| Asset | Identifier | SHA-256 |
|---|---|---|
| Model / tokenizer | TODO | TODO |
| Dataset | TODO | TODO |
| Config | TODO | TODO |
| Environment | TODO | TODO |

## Observed

| Field | Value |
|---|---|
| Observed value | TODO(khantushig) |
| Within tolerance | ☐ yes ☐ no |
| Run directory | TODO(khantushig) |
| Artifact hashes | TODO(khantushig) |
| Compute consumed | TODO(khantushig): generation / training / evaluation separately |

## Deviations

Every difference from the upstream setup — hardware, library versions, data
revision, batch size, precision. A deviation is not a failure, but an unrecorded
deviation makes a match meaningless.

- TODO(khantushig)

## Scientific consequence

Fill in exactly one:

- ☐ **Matched within the frozen tolerance.** The pipeline reproduces a known
  result. Primary contrasts may be interpreted normally.
- ☐ **Mismatched.** Record both values. Per
  `paper/outcome_contingent_language.md` template 10, a positive-control failure
  **caps every downstream claim** and must appear as the principal limitation —
  not a footnote. Do not tune the pipeline until it matches; investigate and
  record what differs.
- ☐ **Not attempted.** ← current state.

Keep positive-control mismatch evidence separate from primary-chain results,
while explaining what it means for trust in the pipeline.
