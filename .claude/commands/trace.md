---
description: Trace a paper-facing number back to its immutable artifacts
---

Number or claim to trace: $ARGUMENTS

Establish the full provenance chain, or prove it is broken. Do not compute the value
yourself, and do not accept a value because it appears in more than one document —
propagated errors look like corroboration.

## Chain to establish, link by link

1. **Where it appears** — every file and line where this value or claim is stated.
   Note any disagreement between occurrences immediately; that is a finding.
2. **Generating command** — the exact versioned command that produced it. Named in
   which file?
3. **Analysis code** — the script or module, at which commit.
4. **Input aggregate** — the file under `results/aggregates/`, and its content hash.
5. **Raw chain artifacts** — the chain-result files feeding that aggregate. Do they
   validate against `schemas/chain_result.schema.json`?
6. **Run manifest** — config, code commit, seeds, data manifest, environment.
   Validates against `schemas/run_manifest.schema.json`?
7. **Data manifest** — asset hashes, split assignment, provenance records.
8. **Partition safety** — confirm no final test example touched prompting, selection,
   thresholds, early stopping, or hyperparameter choice.
9. **Budget matching** — for any comparative claim, confirm the arms consumed equal
   lifetime human-origin optimizer tokens and equal total optimizer tokens.

## Verdict

One of exactly these, stated first:

- **TRACED** — every link verified; list the artifacts.
- **BROKEN AT LINK N** — name the missing or failing link and the single command or
  file that would repair it.
- **HAND-ENTERED** — the value has no generating command. This is a protocol
  violation under the no-manual-numbers rule. Say so unambiguously and name the file
  and line, without softening.

Then: whether this number is currently safe to appear in the paper, and if not, what
must happen before August 13.
