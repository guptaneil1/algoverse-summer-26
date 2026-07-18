#!/usr/bin/env bash
set -euo pipefail

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Refusing to build submission from a dirty working tree."
  exit 2
fi

python scripts/audit_repository.py --strict-structure
ruff check .
pytest -q

mkdir -p dist
git archive --format=zip --output=dist/human-data-budget-submission.zip HEAD
sha256sum dist/human-data-budget-submission.zip > dist/human-data-budget-submission.zip.sha256
echo "Built dist/human-data-budget-submission.zip"
