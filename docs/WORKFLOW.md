# GitHub Collaboration Workflow

## 1. Branch model

`main` is authoritative and protected. Each week has one temporary integration branch. Four personal branches start from that same integration snapshot and target it through draft pull requests.

Branches are parallel histories, not folders inside `main`.

### Week 1

```text
integration/week-1-jul18-jul24
week-1/ronit-research-context
week-1/khantushig-recursive-runner
week-1/neil-data-evaluation
week-1/aarav-policies-analysis
```

### Week 2

```text
integration/week-2-jul25-jul31
week-2/ronit-paper-novelty
week-2/khantushig-positive-control
week-2/neil-frozen-data-metrics
week-2/aarav-method-preregistration
```

### Week 3

```text
integration/week-3-aug01-aug07
week-3/ronit-paper-review
week-3/khantushig-reference-runs
week-3/neil-validity-audit
week-3/aarav-policy-runs
```

### Week 4

```text
integration/week-4-aug08-aug14
week-4/ronit-final-submission
week-4/khantushig-reproduction-release
week-4/neil-validity-certificate
week-4/aarav-final-analysis
```

After creating the GitHub repository and cloning it locally, run:

```bash
bash scripts/bootstrap_branches.sh
```

The script creates and pushes integration and personal branches. A ZIP upload cannot preserve or create remote branches.

## 2. General shared work

Do not maintain a long-lived `general` branch. Shared changes use short branches created from `main`, such as:

```text
shared/project-context
shared/interface-contracts
shared/readme-clarity
shared/submission-requirements
fix/emergency-setup
```

They open PRs directly to `main`, pass CI, and are deleted after merge.

## 3. Start of week

The integrator creates the weekly integration branch from current `main`. Every teammate creates their named branch from that integration branch, pushes it, and opens a draft PR targeting the integration branch on day one.

Never base a weekly branch on another person's branch.

## 4. During the week

- Push visible progress at least once per active workday.
- Keep the draft PR checklist current.
- Work only in owned paths unless an interface-change issue is approved.
- Use fixtures for components owned by other people.
- Never merge another person's current branch into yours.
- Record scientific failures in `FAILURE_LOG.md`; do not relabel them as bugs without defect evidence.
- Put scientific settings in configs, not hidden defaults.

## 5. End of week

Each member runs:

```bash
ruff check .
pytest
python -m human_data_budget.runner.chain --config configs/experiment/toy_cpu.json
```

Personal PRs target the weekly integration branch. After available deliverables merge, the integration branch runs all CI and opens one PR to `main`. The integration result is tagged. Missing deliverables retain the prior mock and become explicitly scoped next-week issues; the week does not remain indefinitely open.

## 6. Pull request titles

```text
[W1][Ronit] Research context and paper foundation
[W1][Khantushig] Recursive runner and compute benchmark
[W1][Neil] Data provenance and evaluation contracts
[W1][Aarav] Policies, simulation, and analysis contracts
```

## 7. Merge policy

- Protect `main` against direct/force pushes and deletion.
- Require PRs, passing checks, and resolved conversations.
- Use squash merge and automatically delete merged branches.
- Require an affected owner review for schema, protocol, primary metric, exclusion, or cross-owned-directory changes.
- Ordinary changes confined to an owner's directory may merge after CI without blocking on another teammate.

## 8. Commit messages

Use:

```text
type(scope): concise outcome
```

Types: `feat`, `fix`, `test`, `docs`, `research`, `experiment`, `analysis`, `paper`, `chore`.

Examples:

```text
feat(runner): add resumable chain manifest
test(data): reject prompt and final-test overlap
research(claims): add closest-work threat matrix
analysis(auc): aggregate regret at chain level
```

## 9. Visibility

The GitHub Project board is the live coordination surface; draft PRs are the live code surface; `docs/STATUS.md` is the frozen truthful status. Do not make private chat the only location of a decision, blocker, exclusion, or scientific change.

## 10. Branch protection checks

Required on `main`:

```text
lint
unit-tests
contract-smoke
artifact-audit
```

Heavy GPU experiments are launched manually from frozen trusted commits, not from untrusted PR workflows.
