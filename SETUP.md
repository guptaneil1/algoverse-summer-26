# SETUP.md — Local Machine and GitHub

Two halves. The local half is where you'll do real work; the GitHub half is for handing
Claude set tasks and getting automatic PR review. Do the local half first — the GitHub
workflows read the same `CLAUDE.md`, so if that file isn't right, both halves are wrong.

---

## Part 1 — Your computer

### 1. Get the repo locally

If you've only been working on github.com so far, this is the step that changes your
life. Web editing means every session starts from nothing; a local clone means Claude
can run your tests.

```bash
git clone https://github.com/<org>/algoverse-summer-26.git
cd algoverse-summer-26
```

### 2. Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
# or: npm install -g @anthropic-ai/claude-code
```

On Windows, install WSL first and run the same command inside it. Verify with
`claude --version`.

### 3. Drop in the setup files

From the `claude-setup/` package, copy into the repo root:

```
CLAUDE.md                    → repo root
.claude/                     → repo root (settings.json, commands/, agents/)
.github/workflows/           → merge with existing .github/workflows/
.github/ISSUE_TEMPLATE/      → merge with existing templates
scripts/setup_claude.sh      → scripts/
PROMPTS.md, META_PROMPTING.md, SETUP.md → docs/ or repo root, your call
```

Nothing here overwrites your existing `.github` files — the workflow and template names
are new.

### 4. Run the setup script

```bash
bash scripts/setup_claude.sh
```

It checks you're at the repo root, confirms Claude Code is installed, verifies the
config files landed, adds `.claude/settings.local.json` to `.gitignore`, and runs your
tests. Idempotent — re-run it whenever.

### 5. Python environment

```bash
python -m venv .venv
source .venv/bin/activate     # Windows WSL: same
make setup
make test
```

### 6. Start a session

```bash
claude
```

Then inside:

| Command | What it does |
|---|---|
| `/memory` | Confirm `CLAUDE.md` loaded |
| `/permissions` | See what Claude can run without asking |
| `/status-truth` | Honest baseline — run this first |
| `/metaprompt <task>` | Compile a rough task into a spec |
| `/plan` | Plan mode before anything touching `runner/`, `schemas/`, `paper/` |
| `/context` | See what's filling the window |
| `/clear` | Between unrelated tasks — free, and fixes most quality drift |

### 7. Commit it

```bash
git add CLAUDE.md .claude .github scripts/setup_claude.sh PROMPTS.md META_PROMPTING.md SETUP.md
git commit -m "Add Claude Code project memory, commands, agents, and CI integration"
git push
```

Commit `.claude/` deliberately. It's team infrastructure — when Neil improves
`/validity`, Aarav gets the improvement on his next pull. That accrual is the whole
point; a prompt library living in four people's shell histories is not a library.

`.claude/settings.local.json` stays gitignored for personal overrides.

---

## Part 2 — GitHub

### Easy path

Inside a local `claude` session:

```
/install-github-app
```

It walks you through installing the GitHub App and setting the secret. Requires repo
admin.

### Manual path

1. Install the Claude GitHub App at `github.com/apps/claude` — **on the repository**,
   not just the org.
2. Repo → Settings → Secrets and variables → Actions → New repository secret.
   Name it exactly `ANTHROPIC_API_KEY` (case-sensitive). Value from
   `console.anthropic.com`.
   Pro/Max alternative: run `claude setup-token` locally and store the result as
   `CLAUDE_CODE_OAUTH_TOKEN`, then change the input name in both workflows.
3. Push the two workflow files. Done.

### What you get

**`claude.yml`** — comment `@claude` on any issue or PR and it runs, carrying the full
protocol prompt: no invented numbers, `docs/STATUS.md` outranks code, banned-word list,
stop rather than reinterpret a request that conflicts with `PROTOCOL.md`.

**`claude-review.yml`** — every PR gets an automatic review, gated in order: validity →
claims → freeze compliance → contracts → ownership → engineering. It stops at the first
gate failure, and it will not approve just because tests pass.

Both are capped (`--max-turns`) and `claude-review.yml` skips fork PRs, which can't read
secrets anyway.

### Handing Claude a set task

Open a new issue with the **Claude task** template. Every field on that form exists
because leaving it blank is a documented way for the task to go sideways — especially
*Out of scope* and *How this task usually goes wrong*, which do more work than the
objective does. Fill it, then comment `@claude` to start the run.

The template is the same structure as `/metaprompt` output, so a well-filled issue and
a well-compiled local prompt are the same artifact reached two different ways.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `@claude` does nothing | App installed on the org but not this repo; or the secret is org-level and not shared; or the comment says `/claude` |
| Workflow fails on auth | Secret name isn't exactly `ANTHROPIC_API_KEY` |
| Fork PR review skipped | Working as intended — forks can't read secrets |
| `Resource not accessible by integration` | Missing a `permissions:` scope in the job |
| Claude ignores `CLAUDE.md` | Not at repo root, or session started from a subdirectory — check `/memory` |
| Quality drops mid-session | Context full of unrelated work. `/context`, then `/clear` |

---

## The order that matters

1. `CLAUDE.md` — loads every session, so it outweighs everything else here.
2. `.claude/commands/` — reusable procedures, shared via git.
3. `PROMPTS.md` — what you type when no command fits.
4. GitHub workflows — same rules, applied where you aren't watching.

Most people invest in reverse order and wonder why every session starts from zero.
