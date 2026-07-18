# Policy Interface Contract

Input fields:

- recursive generation;
- remaining lifetime human-token budget;
- candidate records with stable IDs, token counts, modes, and policy-visible features;
- monitored per-mode state;
- allocation history;
- policy seed.

Output fields:

- selected stable IDs;
- optimizer presentation count for every selected ID;
- declared human-origin optimizer-token count;
- per-mode token allocation;
- optional selection scores;
- policy name/version and seed.

Rules:

- The policy never sees final-test examples, labels, or metrics.
- Declared tokens must equal recomputation from selected candidate token counts and presentations.
- Output order and random decisions are deterministic under the policy seed for the fixture condition.
- Policy code does not train or evaluate models.
- Schema changes require affected owner review.
