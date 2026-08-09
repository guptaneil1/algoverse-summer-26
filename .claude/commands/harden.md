---
description: Adversarially critique and rewrite a prompt before it is used
---

Prompt to harden: $ARGUMENTS

Do not execute the prompt. Attack it, then repair it.

## 1. Failure simulation

Imagine three different competent models each running this prompt independently.
Describe the three most likely divergent outputs. Where the prompt is ambiguous
enough to produce materially different work, that ambiguity is the defect.

## 2. Defect list

Score each on a 1-5 severity and give the fix:

- **Underspecified success** — could a wrong answer pass as done?
- **Missing ground truth** — does it let the model reason from memory about this repo,
  the literature, or a metric, instead of reading a file?
- **Invented-value surface** — is there any slot the model could fill with a plausible
  number, hash, citation, or runtime rather than a measured one?
- **Scope creep** — does it invite edits outside the intended file set or workstream?
- **Protocol collision** — could a compliant answer violate the no-result rule, budget
  matching, test-partition isolation, preregistration, or the freeze?
- **Claim inflation** — does it invite "first / optimal / prevents collapse / novel"
  without the required qualifiers?
- **Unverifiable completion** — does the definition of done rest on judgment rather
  than a command that exits 0?

## 3. Rewrite

Output the hardened prompt in a fenced block. Preserve the intent exactly; change only
precision, grounding, and checkability. Then show a short diff summary: what you
added, removed, and tightened, and why each change closes a specific defect above.

## 4. Residual risk

The one thing the hardened prompt still cannot prevent. Say it plainly.
