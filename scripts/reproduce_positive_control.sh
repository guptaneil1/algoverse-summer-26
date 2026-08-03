#!/usr/bin/env bash
#
# Reproduce the published positive control (Stage A) end to end.
#
# This script replaces the Week 1 starting guard. It is the single reproducible
# command sequence for both arms: it refuses to start unless the scientific state is
# frozen and every asset is present, runs the two arms against the pinned upstream
# commit, ingests the results into this repository's frozen contracts, and verifies
# every recorded hash afterwards.
#
# It is expected to FAIL LOUDLY, with a distinct exit code, whenever anything needed
# is missing. A non-zero exit here is the script working correctly, not a bug.
#
#   2   usage error
#   10  project working tree is dirty
#   11  PROTOCOL.md still contains an unresolved freeze placeholder
#   12  an arm config is missing or fails validation
#   13  upstream checkout missing or not at the pinned commit
#   14  prepared upstream dataset missing
#   15  identifiers still set to resolve_at_runtime
#   16  an upstream arm run failed
#   17  artifact hash verification failed
#   20  an arm stopped part-way with generations remaining (resume by re-running)
#
# Exit 20 is not a failure. Arms run one generation at a time via
# scripts/run_positive_control_arm.py, so a session-capped host (Kaggle: 12 h) can do
# as many generations as fit and the next run continues where this one stopped. Re-run
# the identical command until it exits 0.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR

readonly UPSTREAM_COMMIT="feb8511479a2e2dc868e1caf3f63cb99f1fcc746"
readonly UPSTREAM_REPOSITORY="https://github.com/GeorgeDrayson/model_collapse"

REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
UPSTREAM_DIR=""
CONFIG_FULLY_SYNTHETIC=""
CONFIG_HUMAN_MIXED=""
OUTPUT_ROOT=""
PRECHECK_ONLY=0
CUDA_DEVICE=0
TIME_BUDGET_SECONDS=""
PRUNE_MODELS=0
SHARE_GENERATION_ZERO=1

die() {
  local code="$1"
  shift
  printf 'positive-control: FAILED (exit %s)\n' "${code}" >&2
  printf '  %s\n' "$@" >&2
  exit "${code}"
}

usage() {
  cat >&2 <<'USAGE'
usage: reproduce_positive_control.sh
         --upstream-dir DIR
         --config-fully-synthetic FILE
         --config-human-mixed FILE
         [--output-root DIR]
         [--repo-root DIR]
         [--precheck-only]
         [--cuda-device N]
         [--time-budget-seconds N]
         [--prune-models]
         [--no-shared-generation-zero]

Both arm configs must be named explicitly. There are no defaults: a reproduction
command that silently picks a config is not a reproduction command.

Resuming: arms advance one generation at a time and record each as it completes.
Re-running this identical command continues from the first incomplete generation.
Exit 20 means "more generations remain" — run it again.

  --time-budget-seconds N   stop cleanly between generations after N seconds, so a
                            capped session ends on a recorded boundary instead of
                            being killed mid-generation
  --prune-models            delete each superseded model directory after hashing it.
                            Safe because every generation retrains from base GPT-2,
                            so a model is spent once the next generation's data
                            exists. Cuts peak storage from ~11 GB to ~1.5 GB.
  --no-shared-generation-zero
                            compute generation 0 separately per arm. By default it is
                            computed once and shared, because upstream's iteration-0
                            command is identical for both arms.
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --upstream-dir) UPSTREAM_DIR="${2:-}"; shift 2 ;;
    --config-fully-synthetic) CONFIG_FULLY_SYNTHETIC="${2:-}"; shift 2 ;;
    --config-human-mixed) CONFIG_HUMAN_MIXED="${2:-}"; shift 2 ;;
    --output-root) OUTPUT_ROOT="${2:-}"; shift 2 ;;
    --repo-root) REPO_ROOT="${2:-}"; shift 2 ;;
    --precheck-only) PRECHECK_ONLY=1; shift ;;
    --cuda-device) CUDA_DEVICE="${2:-}"; shift 2 ;;
    --time-budget-seconds) TIME_BUDGET_SECONDS="${2:-}"; shift 2 ;;
    --prune-models) PRUNE_MODELS=1; shift ;;
    --no-shared-generation-zero) SHARE_GENERATION_ZERO=0; shift ;;
    -h|--help) usage ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; usage ;;
  esac
done

[[ -n "${UPSTREAM_DIR}" ]] || usage
[[ -n "${CONFIG_FULLY_SYNTHETIC}" ]] || usage
[[ -n "${CONFIG_HUMAN_MIXED}" ]] || usage
OUTPUT_ROOT="${OUTPUT_ROOT:-${REPO_ROOT}/runs/positive_control}"

PROTOCOL_FILE="${REPO_ROOT}/PROTOCOL.md"
readonly PROTOCOL_FILE

# ---------------------------------------------------------------------------------
# 1. the scientific state must be frozen and clean before anything runs
# ---------------------------------------------------------------------------------

printf 'positive-control: checking frozen scientific state\n'

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
  die 10 "no git repository at ${REPO_ROOT}" \
         "the run manifest must record a real commit, so the project must be a git checkout"
fi

if [[ -n "$(git -C "${REPO_ROOT}" status --porcelain)" ]]; then
  die 10 "working tree at ${REPO_ROOT} is dirty" \
         "commit or stash your changes: a positive-control manifest must name an exact commit"
fi

if [[ ! -f "${PROTOCOL_FILE}" ]]; then
  die 11 "missing ${PROTOCOL_FILE}"
fi

if grep -q 'TODO(khantushig)' "${PROTOCOL_FILE}"; then
  die 11 "PROTOCOL.md still contains an unresolved TODO(khantushig) freeze placeholder" \
         "pin every frozen value first; expected behaviour cannot be declared after the fact"
fi

if ! grep -q "${UPSTREAM_COMMIT}" "${PROTOCOL_FILE}"; then
  die 11 "PROTOCOL.md does not pin upstream commit ${UPSTREAM_COMMIT}" \
         "the script and the protocol must agree on which upstream commit is authoritative"
fi

# ---------------------------------------------------------------------------------
# 2. both configs must exist and validate against the frozen contract
# ---------------------------------------------------------------------------------

for config in "${CONFIG_FULLY_SYNTHETIC}" "${CONFIG_HUMAN_MIXED}"; do
  if [[ ! -f "${config}" ]]; then
    die 12 "missing arm config: ${config}"
  fi
done

printf 'positive-control: validating arm configs\n'
if ! python -c '
import sys
from pathlib import Path

from human_data_budget.runner.positive_control_adapter import load_arm_config

for path in sys.argv[1:]:
    load_arm_config(Path(path))
' "${CONFIG_FULLY_SYNTHETIC}" "${CONFIG_HUMAN_MIXED}"; then
  die 12 "arm config validation failed (see the error above)"
fi

if ! python -c '
import sys
from pathlib import Path

from human_data_budget.runner.positive_control_adapter import (
    assert_resolved,
    load_arm_config,
)

for path in sys.argv[1:]:
    assert_resolved(load_arm_config(Path(path)))
' "${CONFIG_FULLY_SYNTHETIC}" "${CONFIG_HUMAN_MIXED}"; then
  die 15 "an arm config still carries resolve_at_runtime identifiers" \
         "resolve the model/tokenizer/dataset revisions on this host and record them first"
fi

# ---------------------------------------------------------------------------------
# 3. upstream assets must be present at the pinned commit
# ---------------------------------------------------------------------------------

if [[ ! -d "${UPSTREAM_DIR}/.git" ]]; then
  die 13 "no upstream checkout at ${UPSTREAM_DIR}" \
         "git clone ${UPSTREAM_REPOSITORY} ${UPSTREAM_DIR}" \
         "git -C ${UPSTREAM_DIR} checkout ${UPSTREAM_COMMIT}"
fi

upstream_head="$(git -C "${UPSTREAM_DIR}" rev-parse HEAD)"
if [[ "${upstream_head}" != "${UPSTREAM_COMMIT}" ]]; then
  die 13 "upstream checkout is at ${upstream_head}" \
         "expected the commit pinned in PROTOCOL.md: ${UPSTREAM_COMMIT}"
fi

for required in "${UPSTREAM_DIR}/main.py" "${UPSTREAM_DIR}/src/train.py" \
                "${UPSTREAM_DIR}/src/generate.py" "${UPSTREAM_DIR}/src/load_data.py"; do
  [[ -f "${required}" ]] || die 13 "upstream checkout is incomplete: missing ${required}"
done

for split in train test; do
  if [[ ! -f "${UPSTREAM_DIR}/data/wikitext2/${split}.json" ]]; then
    die 14 "prepared dataset missing: ${UPSTREAM_DIR}/data/wikitext2/${split}.json" \
           "run it first:  (cd ${UPSTREAM_DIR} && python src/load_data.py)"
  fi
done

printf 'positive-control: preflight passed\n'

if [[ "${PRECHECK_ONLY}" -eq 1 ]]; then
  printf 'positive-control: --precheck-only requested, stopping before execution\n'
  exit 0
fi

# ---------------------------------------------------------------------------------
# 4. run both arms under the identical frozen protocol
# ---------------------------------------------------------------------------------

mkdir -p "${OUTPUT_ROOT}"

INCOMPLETE_ARMS=()

# Upstream's main.py runs an arm as one uninterruptible job. This driver issues the
# identical src/train.py and src/generate.py commands one generation at a time and
# records each completion, so a capped session can be resumed instead of restarted.
run_arm() {
  local arm_name="$1"
  local config_path="$2"
  local work_dir="${OUTPUT_ROOT}/${arm_name}"

  mkdir -p "${work_dir}"

  local -a driver_args
  driver_args=(
    --config "${config_path}"
    --upstream-dir "${UPSTREAM_DIR}"
    --work-dir "${work_dir}"
    --cuda-device "${CUDA_DEVICE}"
  )
  [[ -n "${TIME_BUDGET_SECONDS}" ]] && driver_args+=(--time-budget-seconds "${TIME_BUDGET_SECONDS}")
  [[ "${PRUNE_MODELS}" -eq 1 ]] && driver_args+=(--prune-models)
  if [[ "${SHARE_GENERATION_ZERO}" -eq 1 && "${arm_name}" != "fully_synthetic" ]]; then
    driver_args+=(--shared-generation-zero "${OUTPUT_ROOT}/fully_synthetic/upstream")
  fi

  printf 'positive-control: running arm %s\n' "${arm_name}"

  set +e
  python "${REPO_ROOT}/scripts/run_positive_control_arm.py" "${driver_args[@]}"
  local status=$?
  set -e

  case "${status}" in
    0) ;;
    20)
      INCOMPLETE_ARMS+=("${arm_name}")
      printf 'positive-control: arm %s stopped with generations remaining\n' "${arm_name}"
      return 0
      ;;
    *)
      die 16 "arm ${arm_name} failed during upstream execution" \
             "full log: ${work_dir}/stdout_stderr.log" \
             "classify it in FAILURE_LOG.md before any rerun (PROTOCOL.md rerun rule)"
      ;;
  esac

  printf 'positive-control: ingesting arm %s into frozen contracts\n' "${arm_name}"
  python -c '
import sys
from pathlib import Path

from human_data_budget.runner.positive_control_adapter import adapt_run, load_arm_config

config_path, experiment_path, output_dir, repo_root = sys.argv[1:5]
config = load_arm_config(Path(config_path))
adapt_run(
    config,
    experiment_path=Path(experiment_path),
    output_dir=Path(output_dir),
    repo_root=Path(repo_root),
)
' "${config_path}" "${work_dir}/upstream" "${work_dir}" "${REPO_ROOT}"
}

# The fully synthetic arm runs first because, with generation-0 sharing on, the
# human-mixed arm reuses its generation 0 rather than recomputing an identical model.
run_arm "fully_synthetic" "${CONFIG_FULLY_SYNTHETIC}"
run_arm "human_mixed" "${CONFIG_HUMAN_MIXED}"

if [[ ${#INCOMPLETE_ARMS[@]} -gt 0 ]]; then
  cat >&2 <<EOF

positive-control: STOPPED EARLY, nothing is wrong.

  arms with generations remaining: ${INCOMPLETE_ARMS[*]}
  completed generations are recorded and will not be recomputed.

Run this identical command again to continue. Repeat until it exits 0.
EOF
  exit 20
fi

# ---------------------------------------------------------------------------------
# 5. every recorded hash must still verify
# ---------------------------------------------------------------------------------

printf 'positive-control: verifying recorded artifact hashes\n'
if ! python -c '
import sys
from pathlib import Path

from human_data_budget.runner.positive_control_adapter import verify_recorded_hashes

failed = False
for run_dir in sys.argv[1:]:
    for mismatch in verify_recorded_hashes(Path(run_dir)):
        print(f"{run_dir}: {mismatch}", file=sys.stderr)
        failed = True
sys.exit(1 if failed else 0)
' "${OUTPUT_ROOT}/fully_synthetic" "${OUTPUT_ROOT}/human_mixed"; then
  die 17 "artifact hash verification failed (see mismatches above)" \
         "do not report these results: a recorded artifact changed after ingest"
fi

# ---------------------------------------------------------------------------------
# 6. regenerate the observed table from saved metrics, never by hand
# ---------------------------------------------------------------------------------

printf 'positive-control: regenerating observed table from saved metrics\n'
python -c '
import json
import sys
from pathlib import Path

output_root, destination = Path(sys.argv[1]), Path(sys.argv[2])
arms = ("fully_synthetic", "human_mixed")
summaries = {
    arm: json.loads(
        (output_root / arm / "positive_control_result.json").read_text(encoding="utf-8")
    )
    for arm in arms
}

generations = sorted(
    {int(key) for summary in summaries.values() for key in summary["metric_by_generation"]}
)

lines = [
    "<!-- Generated by scripts/reproduce_positive_control.sh. Do not edit by hand. -->",
    "# Observed positive-control metrics",
    "",
    "| Generation | Fully synthetic | Human mixed |",
    "|---:|---:|---:|",
]
for generation in generations:
    row = [str(generation)]
    for arm in arms:
        value = summaries[arm]["metric_by_generation"].get(str(generation))
        row.append(f"{value:.4f}" if value is not None else "n/a")
    lines.append("| " + " | ".join(row) + " |")

lines.append("")
for arm in arms:
    ratio = summaries[arm]["degradation_ratio"]
    rendered = f"{ratio:.4f}" if ratio is not None else "unavailable"
    lines.append(f"- `{arm}` degradation ratio (final / generation 0): **{rendered}**")

synthetic_ratio = summaries["fully_synthetic"]["degradation_ratio"]
mixed_ratio = summaries["human_mixed"]["degradation_ratio"]
if synthetic_ratio is not None and mixed_ratio is not None:
    holds = synthetic_ratio > mixed_ratio > 1.0
    verdict = "HOLDS" if holds else "DOES NOT HOLD"
    lines.append("")
    lines.append(f"- Frozen expected ordering (synthetic > mixed > 1.0): **{verdict}**")
    lines.append(
        "- This states only whether the frozen ordering appeared. The validity decision "
        "belongs in expected_vs_observed.md and must apply the frozen tolerance."
    )

destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {destination}")
' "${OUTPUT_ROOT}" "${REPO_ROOT}/docs/positive_control/observed_table.md"

cat <<EOF

positive-control: both arms completed and verified.

  artifacts:      ${OUTPUT_ROOT}
  observed table: ${REPO_ROOT}/docs/positive_control/observed_table.md

Next, by hand and not by this script:
  1. Fill the observed column of docs/positive_control/expected_vs_observed.md.
  2. Apply the frozen tolerance from PROTOCOL.md and record the validity decision.
  3. Write docs/positive_control/report.md on success, or failure_report.md on failure.
     Write exactly one of them, and let the evidence decide which.
  4. Append actual compute to COMPUTE.md and any failures to FAILURE_LOG.md.
EOF
