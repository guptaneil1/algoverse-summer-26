# Upload and GitHub Setup

## What a ZIP can and cannot do

The archive contains all repository files, workflows, templates, scripts, and branch names. Git branches are Git history, not files, so they cannot be created merely by uploading the ZIP. Create the repository first, push `main`, and then run the included branch bootstrap script each week.

## Recommended upload

1. Create an empty GitHub repository without auto-generating a README/license.
2. Unzip this package locally.
3. In the unzipped repository directory run:

```bash
git init
git branch -M main
git add .
git commit -m "chore(repo): initialize August 15 research workflow"
git remote add origin https://github.com/YOUR_OWNER/YOUR_REPOSITORY.git
git push -u origin main
```

4. Replace all four placeholder handles in `.github/CODEOWNERS`.
5. Replace `guptaneil1/algoverse-summer-26` in `.github/ISSUE_TEMPLATE/config.yml`.
6. Add all four collaborators with write access.
7. Run `bash scripts/setup_labels.sh` if the GitHub CLI is installed/authenticated.
8. Create Week 1 branches:

```bash
bash scripts/bootstrap_branches.sh 1
```

9. Each member opens their named branch and a draft PR into the Week 1 integration branch.

## Repository settings

### General

- Default branch: `main`
- Enable Issues and Projects.
- Enable squash merging only.
- Enable automatic deletion of head branches.
- Disable force pushes and branch deletion on `main`.

### Main ruleset

Target `main` and require:

- pull request before merging;
- all conversations resolved;
- required status checks: `lint`, `unit-tests`, `contract-smoke`, `artifact-audit`;
- linear history;
- branch current before merge;
- no bypass except a genuine emergency administrator action that is documented.

Do not enable required CODEOWNERS review until the placeholder handles have been replaced. For this four-person deadline, require an affected owner review only for schemas, protocols, primary metrics/exclusions, and cross-owned paths.

### Security

- Enable secret scanning and push protection when available.
- Store model/tracking tokens in repository or environment secrets.
- Never expose secrets to untrusted fork PRs or self-hosted GPU execution.
- Keep workflow token permissions read-only by default.

## Project board

Create a project named `August 15 Human Data Budget Submission` with columns/views for:

```text
Backlog
Ready
In progress
PR open
CI blocked
Experiment queued
Experiment running
Artifact validation
Done
Invalidated
```

Create milestones:

- Week 1 — July 24
- Week 2 — July 31
- Week 3 Results Freeze — August 7
- Week 4 Release Candidate — August 14
- Final Submission — August 15

## First-day verification

From a clean clone:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-lock.txt
python -m pip install -e . --no-deps
ruff check .
pytest
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
python scripts/audit_repository.py --strict-structure
```

The GitHub Actions checks should reproduce these validations.
