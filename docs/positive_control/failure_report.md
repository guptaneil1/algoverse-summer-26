# Positive control: reproduction blocked — evidence package

**Date:** 2026-08-03
**Branch:** `week-2/khantushig-positive-control`
**Stage:** A (published positive control)
**Classification:** `infrastructure_failure` — see `FAILURE_LOG.md` entries `PC-2026-08-03-A`
and `PC-2026-08-03-B`.

## 1. What this document claims, and what it does not

**Claim:** the positive-control reproduction was not executed, because the environment
available for Week 2 has no accelerator and no network access to the model, dataset, or
paper.

**Not claimed:** that the published result failed to reproduce. Nothing was run, so
nothing failed scientifically. `PROTOCOL.md` §2 acceptance criteria are neither met nor
violated — they are untested.

This distinction is the whole point of the document. A blocked run and a failed
reproduction are different findings with different consequences, and collapsing them in
either direction would be a false report. `docs/positive_control/report.md` does not exist
and must not be created until a run actually completes.

## 2. Evidence for the block

### 2.1 No accelerator

`positive_control_adapter.capture_environment()`, run in the Week 2 environment on
2026-08-03:

```json
{
  "python": "3.11.15",
  "platform": "Linux-6.18.5-x86_64-with-glibc2.39",
  "processor": "x86_64",
  "torch": "not_installed",
  "transformers": "not_installed",
  "datasets": "not_installed",
  "accelerator": "none_detected"
}
```

`nvidia-smi` is not present on the host. The machine reports 4 vCPUs and 15 GiB RAM.
Upstream's `config/config.yaml` sets `cuda_device: 0` and `torch_dtype: bfloat16`; the
pipeline expects a CUDA device.

### 2.2 No access to the required assets

Outbound HTTPS is filtered by the environment's network policy. Both hosts needed for
Stage A are denied at the proxy with `403` on `CONNECT`:

| Host | Needed for | Result |
|---|---|---|
| `huggingface.co` | GPT-2 weights/tokenizer, WikiText-2, the ModernBERT detector, and revision SHAs | `CONNECT tunnel failed, response 403` |
| `aclanthology.org` | The published expected values for the comparison | `CONNECT tunnel failed, response 403` |

`github.com` **is** reachable, which is why the upstream repository could be pinned and
read. Every frozen setting in `PROTOCOL.md` was taken from the upstream working tree at
`feb8511479a2e2dc868e1caf3f63cb99f1fcc746`, not guessed.

### 2.3 Consequence for the expected column

Because `aclanthology.org` is unreachable, the numeric expected values in
`docs/positive_control/expected_vs_observed.md` §2.2 are recorded as **open**, not filled
in. No published value was invented, estimated, or reconstructed from memory. The
qualitative expected ordering — which is the primary criterion — *is* frozen, because it
follows from the paper's title claim and upstream's arm definitions, both of which were
readable.

## 3. Unblocking: exactly what is needed

1. **An accelerator host** with CUDA and network access to `huggingface.co`. One T4 is
   sufficient for GPT-2 124M on WikiText-2; two GPUs let the arms run concurrently.
2. **Resolve the deferred identifiers** on that host — the GPT-2 and detector revision
   SHAs, the WikiText-2 revision, and the prepared `train.json` hash — and commit them
   into both arm configs. The adapter refuses to run until this is done.
3. **Extract the published expected values** into `expected_vs_observed.md` §2.2 with
   exact figure/table citations, and commit that **before** launching.
4. **Run the official smoke test first** (`python main.py smoke_test=true
   wandb_disabled=true data_selection=no-selection`) and record its measured wall time,
   accelerator-hours, peak memory, and storage. `COMPUTE.md` requires a measured
   one-generation basis before the full forecast counts as a forecast.
5. **Run both arms** through `scripts/reproduce_positive_control.sh`.
6. **Complete `expected_vs_observed.md`**, then write `report.md` on a clean reproduction
   or replace this document's classification on a scientific failure. Preserve this
   document either way — `FAILURE_LOG.md` is append-only.

## 4. Effect on downstream stages

`PROTOCOL.md` §4 states that Stage B stays blocked until Stage A and the invariant tests
pass. Stage A has not passed. **Stage B remains blocked**, and no primary-outcome claim
may be made on the basis of anything in this branch.
