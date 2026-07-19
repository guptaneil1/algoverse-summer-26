#!/usr/bin/env bash
set -euo pipefail

week="${1:-}"
if [[ ! "$week" =~ ^[1-4]$ ]]; then
  echo "Usage: bash scripts/bootstrap_branches.sh WEEK_NUMBER"
  echo "Run at the beginning of each week after that week's base is merged into main."
  exit 2
fi

case "$week" in
  1)
    integration="integration/week-1-jul18-jul24"
    branches=(
      "week-1/ronit-research-context"
      "week-1/khantushig-recursive-runner"
      "week-1/neil-data-evaluation"
      "week-1/aarav-policies-analysis"
    )
    ;;
  2)
    integration="integration/week-2-jul25-jul31"
    branches=(
      "week-2/ronit-paper-novelty"
      "week-2/khantushig-positive-control"
      "week-2/neil-frozen-data-metrics"
      "week-2/aarav-method-preregistration"
    )
    ;;
  3)
    integration="integration/week-3-aug01-aug07"
    branches=(
      "week-3/ronit-paper-review"
      "week-3/khantushig-reference-runs"
      "week-3/neil-validity-audit"
      "week-3/aarav-policy-runs"
    )
    ;;
  4)
    integration="integration/week-4-aug08-aug14"
    branches=(
      "week-4/ronit-final-submission"
      "week-4/khantushig-reproduction-release"
      "week-4/neil-validity-certificate"
      "week-4/aarav-final-analysis"
    )
    ;;
esac

git fetch origin
git switch main
git pull --ff-only origin main

if git show-ref --verify --quiet "refs/remotes/origin/$integration"; then
  echo "Remote integration branch already exists: $integration"
  exit 1
fi

git switch -c "$integration"
git push -u origin "$integration"

for branch in "${branches[@]}"; do
  git switch "$integration"
  git switch -c "$branch"
  git push -u origin "$branch"
done

git switch "$integration"
echo "Created integration branch and four personal branches for Week $week."
echo "Each member should now open a draft PR from their branch into $integration."
