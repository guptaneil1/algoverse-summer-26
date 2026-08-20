# Certificate evidence pack — `primary_pilot_v2_2026-08-20`

> ## THIS IS NOT A CERTIFICATE
>
> No certificate has been issued for this run. `docs/VALIDITY_CERTIFICATE_TEMPLATE.md`
> requires that the certifier **did not produce the run**, and this document was assembled
> by the same session that ran the analysis. Signing it here would make it worth no more
> than an uncertified run, which is the template's own stated position.
>
> **What this is:** every machine-checkable fact a certifier would otherwise have to gather
> by hand, pre-gathered with the command that produces each one, so the certifier spends
> their time on judgement rather than on transcription. Each row below can be reproduced
> independently. **A certifier should re-run the commands rather than trust the values.**

**Prepared:** 2026-08-20 · **Prepared by:** analysis session (also the run operator — hence
the banner) · **Awaiting:** a certifier who did not operate the run

---

## Header, for transcription into the real certificate

| Field | Value |
|---|---|
| Run ID | `primary_pilot_v2_2026-08-19` (config `run_id`; executed to completion 2026-08-20) |
| Artifact location | `results/runs/primary_pilot_v2_2026-08-20/` (65 files tracked); 25 `run_manifest.json` untracked, hashed in `ARTIFACT_HASHES.json` |
| Certifying member | **UNFILLED — must not be the run operator** |
| Run operator | analysis session, 2026-08-19/20 |
| Certificate date | **UNFILLED** |
| Code commit | `088b7ff` (the commit every phase ran under; recorded in the ledger) |
| Protocol version | `PROTOCOL.md` at `088b7ff` |
| Classification | machine verdict is `valid_with_limitation` for all 25 chains — see §1. **The classification of the headline result is the certifier's call, not the validator's** |

## 1. Automated verdict

```bash
python scripts/validate_run.py results/runs/primary_pilot_v2_2026-08-20/pilot/*/seed*/ \
  --report /tmp/validation.json
echo "EXIT=$?"
```

| Check | Result |
|---|---|
| Exit code | **1** = `valid_with_limitation`. Mapping is `0 valid / 1 limited / 2 invalid / 3 usage` (F-024, and F-024a for the template row that stated this backwards until 2026-08-20) |
| Per-chain classification | **25 `valid_with_limitation`, 0 `invalid`** |
| Blocking failures | **none** |
| Schema failures | **0** across all 25 |
| Limitations | `LIMIT_NEAR_DUPLICATE_NOT_CHECKED` (25/25), `LIMIT_TOKEN_LEDGER_NOT_RECOMPUTABLE` (25/25) |

The committed `pilot/validation.json` is the report this run produced; a certifier
regenerating it should get the same classifications.

**Read the per-chain report, not the exit code.** F-021 happened because an aggregate exit
code was read as a per-chain classification and ten invalid chains went unnoticed. The
counts above come from the per-chain array.

## 2. Checks the validator passed, per chain

20 checks pass on every chain. Grouped:

- **Artifacts** — `chain_result.json`, `run_manifest.json` present
- **Budget** — `budget_human_matches_plan`, `budget_total_matches_plan`, `budget_non_negative`
- **Protocol** — horizon respected, policy matches, seed matches, status terminal
- **Evaluation** — metrics present, NLL finite, tail retention in range
- **Provenance** — scanned; commit clean; environment recorded
- **Separation** — five pairwise-disjoint partition checks, including
  `rescue_candidates|final_human_test` and `generation_prompts|final_human_test`

Three checks fail on every chain and are the two recorded limitations:
`separation_near_duplicate_coverage`, `separation_near_duplicate_scanned`,
`token_ledger_recomputed`.

**What those two limitations mean, stated plainly** because §3 and §4 of the template are
blocking sections and a certifier must not tick them from this pack:

- **Near-duplicate**: 28,351 examples carry no text in the manifest, so they could not be
  compared. Exact-hash disjointness *is* verified and passes. Near-duplicate overlap above
  the frozen threshold is **unverified, not verified-absent**. §3 of the template asks for
  near-duplicate separation and the honest answer is "not checked".
- **Token ledger**: no realised batch records were retained, so the declared ledger was
  compared against the frozen budget rather than recomputed from consumed batches. §4 asks
  for counts derived from tokenized batches actually consumed; the honest answer is that
  they were declared and checked for consistency, not recomputed.

## 3. Budget conditions — the run's headline property

```bash
python scripts/run_pilot.py --config configs/experiment/primary_pilot_v2.json \
  --output-dir results/runs/primary_pilot_v2_2026-08-20/pilot --check-only
```

| Axis | Realised | Permitted | Verdict |
|---|---|---|---|
| Lifetime human-origin tokens, spending arms | 749,709 – 749,995 against a 750,000 ceiling, **0.0381%** spread | 0.2000% | pass |
| Total optimizer tokens, all arms | **16,678,912 identically**, 0.0000% spread | 0.2000% | pass |
| Control arm | exactly 0 human tokens, 5 chains | exact | pass |

Independently recomputed by `budget_axes` in `scripts/generate_pilot_outputs.py`, which
reproduces the guard's figures and also reproduces the *failing* figures of the superseded
run (10.1070% and 2.2564%, matching F-020 and F-021).

## 4. Independent recomputation (template §6)

```bash
python scripts/reproduce_pilot_table.py --run-dir results/runs/primary_pilot_v2_2026-08-20
```

Recomputes every published per-arm value from `chain_result.json` with arithmetic written
independently of the generator — it deliberately shares no code with it. **Exit 0, every
published value reproduced.** It also passes for the superseded 2026-08-18 grid.

Byte-identical regeneration is verified: re-running `generate_pilot_outputs.py` leaves
`pilot_macros.tex`, `primary_results.tex` and `pilot_nll_by_generation.png` unchanged by
MD5.

**Still owed by the certifier:** the template asks for the primary NLL and tail metrics to
be recomputed *from the frozen raw outputs* with the certifier's own invocation. The script
above recomputes from `chain_result.json`, which is one level downstream of the raw
evaluator outputs. That gap is real and this pack does not close it.

## 5. Artifact integrity

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("results/runs/primary_pilot_v2_2026-08-20")
ledger = json.loads((root / "ARTIFACT_HASHES.json").read_text())["files"]
bad = [r for r, w in ledger.items()
       if (root / r).is_file()
       and hashlib.sha256((root / r).read_bytes()).hexdigest() != w["sha256"]]
print(f"{len(ledger)} in ledger, {len(bad)} mismatched")
PY
```

101 files hashed. Expect 0 mismatched; a fresh clone reports the 25 manifests and the logs
as *missing*, never as mismatched.

## 6. Scope limitations that apply (template §7)

- [x] **Run resumed after an infrastructure failure** — twice. F-025 and F-026. Eight of the
      25 chains were produced by the launch F-026 killed. Both defects stopped chains from
      *starting*; neither corrupted a chain that finished, and every retained chain ran its
      full horizon. A certifier should satisfy themselves of that claim rather than accept it
      — `generations_completed` is 10 on all 25 and the metric arrays have 10 entries each.
- [x] **Other:** the grid was executed in four seed-block phases rather than one launch
      (`DECISIONS.md` P-012). Phase order was set by how far each chain got before F-025,
      i.e. by shard scheduling and wall-clock, and no chain was ordered, kept or dropped on
      account of anything it measured.
- [ ] Chain incomplete — no; 10/10 generations on all 25
- [ ] Fixture-stage artifact — no
- [ ] Working tree dirty at run time — no; `commit_clean` passes on all 25
- [ ] Excluded under a frozen exclusion rule — none excluded; `aggregate.json` records 25
      included, 0 excluded

## 7. Consequence for claims (template §9)

| Claim | Effect of this run |
|---|---|
| C-002 | **Tested and not supported.** Both preconditions of the falsification clause are met and the interval lies wholly inside the practically-equivalent region. Not evidence that joint is worse. Four of seven required comparators ran; 5–7 unimplemented |
| C-003 | **No effect.** No monitoring-omission intervention ran. C-003 remains untested |

## 8. What the certifier still has to do

Nothing in this pack substitutes for these.

1. **Verify independence** — confirm you did not operate the run, and say so in §10.
2. **Blocking §3, data separation** — decide whether unverified near-duplicate separation is
   acceptable for a `valid_with_limitation` classification, or whether it blocks. The
   validator treats it as a limitation; that is the validator's rule, not your judgement.
3. **Blocking §4, token accounting** — same decision for the unrecomputed ledger.
4. **Recompute a metric from raw outputs**, not from `chain_result.json`, and record both
   numbers even if they agree.
5. **Classify the headline result** and write the §8 rationale in your own words.
6. **Sign §10**, or decline and say why.

A certificate that ticks §3 and §4 from this document has not been independently issued.
Both are blocking sections and both carry a known unverified property.
