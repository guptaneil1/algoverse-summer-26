# Claude Setup Package — The Human Data Budget

Drop-in configuration so Claude works accurately on this repo, locally and in GitHub.

## Install

```bash
# from the repo root
cp -r /path/to/claude-setup/. .
bash scripts/setup_claude.sh
```

Then read **SETUP.md**. Nothing here overwrites existing repo files.

## Contents

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project memory — loads in every session. The highest-leverage file here. |
| `PROMPTS.md` | Copy-paste prompt templates for implement / debug / verify / research / write / review / analyze. |
| `SETUP.md` | Local machine and GitHub setup, step by step. |
| `META_PROMPTING.md` | Why these are shaped this way; how to write your own. |
| `.claude/settings.json` | Permissions: test commands run silently, frozen artifacts are read-only, destructive commands blocked. |
| `.claude/commands/*.md` | Eight slash commands: `/metaprompt` `/harden` `/crystallize` `/trace` `/validity` `/implement` `/review` `/status-truth` |
| `.claude/agents/*.md` | Three subagents with clean context: `novelty-adversary` `evidence-auditor` `stats-referee` |
| `.github/workflows/claude.yml` | `@claude` on issues and PRs, carrying the protocol prompt. |
| `.github/workflows/claude-review.yml` | Automatic protocol-gated PR review. |
| `.github/ISSUE_TEMPLATE/claude_task.yml` | Spec-grade task form for handing Claude work on GitHub. |
| `scripts/setup_claude.sh` | Idempotent local setup and health check. |

## First three things to run

```
bash scripts/setup_claude.sh
claude
/status-truth
```

