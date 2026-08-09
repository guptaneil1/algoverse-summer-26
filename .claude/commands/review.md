---
description: Protocol-aware review of a diff, branch, or PR
---

Under review: $ARGUMENTS

Review in this order. Stop and report as soon as a gate fails — do not spend effort on
style when validity is broken.

## Gate 1 — Scientific validity
Does this diff introduce any path by which an invalid result could look valid? Check
leakage, budget matching, token accounting, provenance, seed propagation, and whether
any test-partition data gained influence over a decision. A FAIL here blocks the PR
regardless of code quality.

## Gate 2 — Claim discipline
Does any prose in the diff — comment, docstring, README, paper, commit message —
assert something not yet supported by run artifacts? Check against `CLAIMS.md`
statuses and the banned-word list. Flag every widened claim with the narrower
statement the evidence supports.

## Gate 3 — Freeze compliance
Given the current freeze state, is this an allowed edit? After a results freeze the
allowed set is clarity, citations, formatting, packaging, and removal of unsupported
claims. Adding a seed, metric, subgroup, exclusion, budget, or method redesign is not.

## Gate 4 — Contract compliance
Schema conformance, architecture dependency direction, interface stability. If a
schema changed, was the interface doc updated in the same commit, and were downstream
consumers checked?

## Gate 5 — Ownership
Does the diff touch files owned by another workstream per CODEOWNERS? Was that
coordinated?

## Gate 6 — Engineering
Tests that would actually fail if the logic broke. Determinism. Atomic writes. Error
paths. Then, last and briefly, readability.

## Output

Verdict: **BLOCK / REQUEST CHANGES / APPROVE**, stated first, with the single most
important reason. Then findings ordered by severity, each with file:line and a
concrete fix. Separate "must fix before merge" from "worth doing later" — do not blend
them into one list, because a blended list gets triaged into inaction.
