#!/usr/bin/env bash
set -euo pipefail

config="${1:-configs/experiment/toy_cpu.json}"
python -m human_data_budget.runner.chain --config "$config"
