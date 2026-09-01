#!/usr/bin/env bash
# One command to take a fresh GPU VM from nothing to a running model.
#
# Replaces Parts 5 and 6.1-6.3 of docs/CROSS_MODEL_RUNBOOK.md. Everything it does is
# what that document does by hand; this exists so that starting five machines is five
# commands rather than five hours of typing.
#
#   curl -fsSL https://raw.githubusercontent.com/guptaneil1/algoverse-summer-26/cross-model/add-model-families/scripts/bootstrap_vm.sh | bash -s -- smollm
#
# or, once the repo is cloned:
#
#   bash scripts/bootstrap_vm.sh smollm
#
# It stops at the point of launching the run, prints the exact command to start it, and
# does not start it itself: the launch belongs inside tmux, and a script that backgrounds
# a twelve-hour job makes it harder to watch, not easier.
#
# Safe to re-run. Every step checks whether it is already done.

set -euo pipefail

SHORT="${1:-}"
BRANCH="${BRANCH:-cross-model/add-model-families}"
REPO_URL="https://github.com/guptaneil1/algoverse-summer-26.git"
UPSTREAM_URL="https://github.com/GeorgeDrayson/model_collapse.git"
UPSTREAM_PIN="feb8511479a2e2dc868e1caf3f63cb99f1fcc746"

case "$SHORT" in
  smollm)    HF_ID="HuggingFaceTB/SmolLM2-135M" ;;
  pythia)    HF_ID="EleutherAI/pythia-160m" ;;
  pythia410) HF_ID="EleutherAI/pythia-410m" ;;
  pythia1b)  HF_ID="EleutherAI/pythia-1b" ;;
  qwen)      HF_ID="Qwen/Qwen2.5-0.5B" ;;
  *)
    echo "usage: bash scripts/bootstrap_vm.sh <model>" >&2
    echo "  where <model> is one of: smollm pythia pythia410 pythia1b qwen" >&2
    exit 2
    ;;
esac

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

say "Checking the graphics card"
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi not found. This VM has no GPU drivers." >&2
  echo "Delete it and rebuild using the NVIDIA GPU-Optimized image (runbook Part 3)." >&2
  exit 1
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

say "Getting the project"
cd ~
if [ ! -d ~/algoverse-summer-26 ]; then
  git clone "$REPO_URL"
fi
cd ~/algoverse-summer-26
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
pip install -q -e . --no-deps

say "Getting the training pipeline, pinned to the commit the original run used"
cd ~
if [ ! -d ~/model_collapse ]; then
  git clone "$UPSTREAM_URL"
fi
cd ~/model_collapse
git checkout -q "$UPSTREAM_PIN"
cd ~

say "Installing dependencies (several minutes)"
pip install -q -r ~/model_collapse/requirements.txt
pip install -q transformers==4.48.3 datasets==3.2.0 accelerate==1.2.1 \
    huggingface_hub jsonschema pytest pyarrow hf_transfer

say "Creating the wandb shim"
mkdir -p ~/shim
cat > ~/shim/sitecustomize.py <<'PY'
import os, sys, sysconfig
try:
    import importlib.util
    _p = os.path.join(sysconfig.get_paths()["stdlib"], "sitecustomize.py")
    if os.path.exists(_p):
        _s = importlib.util.spec_from_file_location("_d", _p)
        _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
except Exception:
    pass
if os.environ.get("STAGE_A_WANDB_SHIM") == "1":
    try:
        import wandb
        wandb.init(mode="disabled")
    except Exception as e:
        sys.stderr.write("SHIM FAILED %s\n" % e)
PY

say "Running the tests"
cd ~/algoverse-summer-26
export PYTHONPATH=src
python -m pytest -q tests/runner tests/policies

say "Building the corpora for $SHORT ($HF_ID)"
for spec in "base_train:--limit 400:${SHORT}_base" \
            "prompts:--limit 400:${SHORT}_prompts" \
            "test:--eval:${SHORT}_test"; do
  part="${spec%%:*}"; rest="${spec#*:}"; flag="${rest%%:*}"; out="${rest#*:}"
  if [ -f "data/corpora/${out}.json" ]; then
    echo "  data/corpora/${out}.json already exists, skipping"
    continue
  fi
  # shellcheck disable=SC2086
  python scripts/build_base_corpus.py --partition "$part" $flag \
      --tokenizer "$HF_ID" --upstream-dir ~/model_collapse \
      --out "data/corpora/${out}.json"
done

say "Building the manifests for $SHORT"
if [ -f "data/manifests/${SHORT}/OPTIMIZER_TOKEN_COUNTS.json" ]; then
  echo "  already built, skipping"
else
  python scripts/add_optimizer_token_counts.py \
      --tokenizer "$HF_ID" --out-dir "data/manifests/${SHORT}"
fi

say "Generating the run configuration"
python scripts/make_model_pilot.py --model "$SHORT"

cat <<EOF

================================================================================
READY.

Check the "tokenizer efficiency" number printed just above. It should be roughly
between 0.7 and 1.3. If it is not, stop and ask -- something is wrong with the
corpus, and running now would waste the GPU hours.

Pin the model revision before running. Open:
    configs/experiment/pilot_${SHORT}.json
and replace PIN_BEFORE_RUNNING with the commit hash from
    https://huggingface.co/${HF_ID}/commits/main

Then start the run inside tmux so closing your laptop does not kill it:

    tmux new -s run
    cd ~/algoverse-summer-26 && export PYTHONPATH=src
    python scripts/run_pilot.py --config configs/experiment/pilot_${SHORT}.json \\
        --upstream-dir ~/model_collapse --shim-dir ~/shim

Leave it running with Ctrl-B then D. Come back with: tmux attach -t run
================================================================================
EOF
