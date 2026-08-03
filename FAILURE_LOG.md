# Failure Log

> No experimental run has completed in this repository. Stage A was prepared but could not be
> executed; the two entries below record why, with evidence.

Failures, null results, contradictory evidence, and protocol violations must be retained. They may not be deleted because they weaken the preferred conclusion.

## Entries

| ID | Date | Stage | Run/claim | Failure | Evidence | Cause status | Resolution | Scientific consequence |
|---|---|---|---|---|---|---|---|---|
| None | — | — | — | No runs yet | — | — | — | — |
| `PC-2026-08-03-A` | 2026-08-03 | A | `positive_control_fully_synthetic_seed42`, `positive_control_human_mixed_seed42` | Neither arm could be launched: the Week 2 environment has no accelerator. | `capture_environment()` output recorded in `docs/benchmarks/khantushig_week2.md` §2 and `docs/positive_control/failure_report.md` §2.1: `accelerator: none_detected`, `torch: not_installed`, `nvidia-smi` absent, 4 vCPU / no CUDA device. Upstream `config/config.yaml` requires `cuda_device: 0`, `torch_dtype: bfloat16`. | **Infrastructure** — not implementation. No defect was found in the adapter, configs, or script; all four contract tests pass (158 passed, 1 skipped). | Rerun is permitted under the frozen rules once an accelerator host is provisioned (`PROTOCOL.md` rerun rule: infrastructure failures may be rerun unchanged). No configuration change is required or permitted as part of that rerun. | Stage A is untested, so **Stage B remains blocked** (`PROTOCOL.md` §4). No reproduction claim may be made in either direction. This is a blocked run, not a failed reproduction. |
| `PC-2026-08-03-B` | 2026-08-03 | A | Expected-value extraction for `docs/positive_control/expected_vs_observed.md` §2.2 | The published numeric expected values could not be read, so the expected column is frozen qualitatively (ordering) but not numerically. | `docs/positive_control/failure_report.md` §2.2: the environment's network policy denies `CONNECT` to `aclanthology.org` and `huggingface.co` with HTTP 403; `github.com` is reachable, which is why the upstream commit and all upstream-derived settings could be pinned. | **Infrastructure** — network policy, not a protocol or implementation defect. | Resolved by extracting the values on a host with access and committing them **before** either arm runs, so the freeze remains provable by timestamp. Recorded as an open item rather than filled with an invented number. | The primary ordering criterion is unaffected and remains frozen. The 5% engineering tolerance cannot be applied until the published values exist, so a run completed before then could reach at most `valid_with_limitation`. |

## Entry rules

For every failure, record:

- exact run or claim identifier;
- code and configuration commit;
- manifest and log location;
- whether the cause is implementation, infrastructure, protocol, or scientific;
- evidence supporting that classification;
- whether rerunning is allowed under the frozen rules;
- effect on claims and future stages.

An unfavorable treatment result is not an implementation failure without independent evidence of a defect.
