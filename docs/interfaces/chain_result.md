# Chain Result Contract

One chain-result artifact represents one complete independently seeded recursive chain. It contains:

- run identity, policy, seed, budget, and horizon;
- validity classification and objective reason;
- generation-wise metrics;
- final consumed human and total token counts;
- manifest and artifact hashes;
- failure/limitation references.

Analysis treats each chain result as one experimental unit. Generations remain repeated observations. The JSON Schema in `schemas/chain_result.schema.json` is authoritative.
