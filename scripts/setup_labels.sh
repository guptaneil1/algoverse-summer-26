#!/usr/bin/env bash
set -euo pipefail

command -v gh >/dev/null || { echo "Install and authenticate the GitHub CLI first."; exit 2; }

create_label() {
  gh label create "$1" --color "$2" --description "$3" --force
}

create_label "owner:ronit" "5319E7" "Owned by Ronit"
create_label "owner:khantushig" "1D76DB" "Owned by Khantushig"
create_label "owner:neil" "0E8A16" "Owned by Neil"
create_label "owner:aarav" "FBCA04" "Owned by Aarav"
create_label "week:1" "D4C5F9" "July 18–24"
create_label "week:2" "D4C5F9" "July 25–31"
create_label "week:3" "D4C5F9" "August 1–7"
create_label "week:4" "D4C5F9" "August 8–14"
create_label "deadline:aug15" "B60205" "Required for August 15 submission"
create_label "area:research" "C2E0C6" "Literature, novelty, or claims"
create_label "area:paper" "C2E0C6" "Manuscript or presentation"
create_label "area:training" "0052CC" "Training or generation"
create_label "area:data" "0052CC" "Data, provenance, or token accounting"
create_label "area:evaluation" "0052CC" "Evaluation or validity"
create_label "area:policy" "0052CC" "Allocation policy"
create_label "area:analysis" "0052CC" "Statistics, tables, or figures"
create_label "area:experiment" "0052CC" "Experiment run or family"
create_label "area:infrastructure" "6F42C1" "Repository or CI infrastructure"
create_label "status:ready" "0E8A16" "Ready to begin"
create_label "status:in-progress" "FBCA04" "Currently in progress"
create_label "status:blocked" "B60205" "Blocked with documented reason"
create_label "status:review" "1D76DB" "Ready for review"
create_label "status:complete" "0E8A16" "Acceptance criteria met"
create_label "status:invalidated" "000000" "Invalidated artifact or task"
create_label "claim:hypothesis" "FEF2C0" "Untested scientific hypothesis"
create_label "claim:result" "0E8A16" "Supported by linked run artifacts"
create_label "claim:unknown" "EDEDED" "Unresolved and unsafe as fact"
create_label "protocol:frozen" "5319E7" "Frozen protocol or configuration"
create_label "result:primary" "0E8A16" "Governed by frozen primary plan"
create_label "result:exploratory" "FBCA04" "Exploratory or post-freeze result"
create_label "result:invalid" "B60205" "Invalid under objective rules"

echo "Project labels created or updated."
