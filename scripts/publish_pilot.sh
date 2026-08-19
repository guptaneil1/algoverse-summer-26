#!/usr/bin/env bash
# Publish the Stage B pilot: open the PR, and cut a release carrying the artifacts
# that are too large to track in git.
#
# Requires `gh auth login` to have been run once. Everything here is idempotent-ish:
# it refuses rather than duplicating if the PR or the tag already exists.
#
# Usage:
#   bash scripts/publish_pilot.sh [path/to/pilot_results.tar.gz]

set -euo pipefail

BRANCH="stage-a/env-freeze"
BASE="main"
TAG="pilot-2026-08-18"
TARBALL="${1:-$HOME/Downloads/pilot_results.tar.gz}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

command -v gh >/dev/null || { echo "gh not on PATH"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "run 'gh auth login' first"; exit 1; }

if [ -n "$(git status --porcelain)" ]; then
  echo "working tree is dirty; commit or stash before publishing"; exit 1
fi
if [ -n "$(git log --oneline "@{u}..HEAD" 2>/dev/null)" ]; then
  echo "branch has unpushed commits; push before publishing"; exit 1
fi

echo "== pull request =="
if gh pr view "$BRANCH" >/dev/null 2>&1; then
  echo "   already open: $(gh pr view "$BRANCH" --json url -q .url)"
else
  gh pr create \
    --base "$BASE" \
    --head "$BRANCH" \
    --title "Stage B: pilot executed, primary contrast not established, apparatus validated" \
    --body-file docs/PR_DESCRIPTION_stage-a-env-freeze.md
  echo "   opened: $(gh pr view "$BRANCH" --json url -q .url)"
fi

echo
echo "== release =="
if [ ! -f "$TARBALL" ]; then
  echo "   SKIPPED: no tarball at $TARBALL"
  echo "   pass the path as the first argument to attach it"
  exit 0
fi

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "   tag $TAG already exists; not overwriting"
else
  gh release create "$TAG" "$TARBALL" \
    --target "$BRANCH" \
    --title "Primary pilot artifacts — 2026-08-18" \
    --notes "Complete artifacts from the 25-chain primary pilot. 4x RTX 4090, 6.75 h wall on the longest shard.

Contains 25 chain_result.json, 25 run_manifest.json (the 162 MB of partition provenance not tracked in git), four shard summaries, the aggregate, and the shard logs.

Verify against the repository using ARTIFACT_HASHES.json in results/runs/primary_pilot_2026-08-18/ — expect 61/61 files verified.

Certification: 10 invalid, 15 valid_with_limitation. The primary contrast is NOT ESTABLISHED — realised human spend differed 10.1% on one arm and realised totals span 2.26% across arms, so PROTOCOL.md section 4 fails on both axes. See docs/runs/primary_pilot_2026-08-18_results.md and FAILURE_LOG.md F-020, F-021.

This archive is the only copy of the run manifests and cannot be regenerated without repeating the run."
  echo "   published: $(gh release view "$TAG" --json url -q .url)"
fi

echo
echo "done."
