#!/usr/bin/env bash
# Launch one recursive chain from an explicit frozen config.
#
# No hidden scientific defaults: the config path is required, must exist, and
# must not still be awaiting the results freeze. Failing loudly here is cheaper
# than discovering a wrong setting after a full chain has burned compute.
set -euo pipefail

die() { printf 'run_chain: %s\n' "$*" >&2; exit 1; }

[ "$#" -ge 1 ] || die "usage: scripts/run_chain.sh <config.json>
refusing to guess a config; every scientific setting must be explicit."

config="$1"
shift

[ -f "$config" ] || die "config not found: $config"

python - "$config" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    config = json.loads(open(path, encoding="utf-8").read())
except json.JSONDecodeError as error:
    sys.exit(f"run_chain: config is not valid JSON: {path}\n{error}")

status = config.get("_freeze_status")
if status and status != "FROZEN":
    sys.exit(
        f"run_chain: refusing to launch {path}\n"
        f"  _freeze_status is {status!r}, not 'FROZEN'.\n"
        "  Its scientific values have not been set from a results freeze.\n"
        "  Fill every field listed under _required_from_freeze, set\n"
        "  _freeze_status to 'FROZEN', and record which freeze supplied them."
    )

missing = [key for key, value in config.items() if not key.startswith("_") and value is None]
if missing:
    sys.exit(f"run_chain: config has unset values: {sorted(missing)}")
PY

exec python -m human_data_budget.runner.chain --config "$config" "$@"
