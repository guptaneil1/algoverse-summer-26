#!/usr/bin/env bash
# Set up Claude Code for this repository on a local machine.
# Idempotent: safe to re-run.
set -euo pipefail

say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32mok\033[0m   %s\n' "$*"; }
warn() { printf '  \033[33mwarn\033[0m %s\n' "$*"; }
die()  { printf '  \033[31mfail\033[0m %s\n' "$*"; exit 1; }

say "1. Repository root"
[ -f PROTOCOL.md ] && [ -d src/human_data_budget ] \
  || die "Run this from the repository root (PROTOCOL.md and src/human_data_budget must exist)."
ok "$(pwd)"

say "2. Claude Code"
if command -v claude >/dev/null 2>&1; then
  ok "installed: $(claude --version 2>/dev/null || echo 'version unknown')"
else
  warn "not found. Install it, then re-run this script:"
  echo "     macOS/Linux:  curl -fsSL https://claude.ai/install.sh | bash"
  echo "     or via npm:   npm install -g @anthropic-ai/claude-code"
  echo "     Windows:      use WSL, then the same command"
fi

say "3. Project files"
for f in CLAUDE.md .claude/settings.json; do
  [ -f "$f" ] && ok "$f" || warn "$f missing — copy it from the setup package"
done
for d in .claude/commands .claude/agents; do
  if [ -d "$d" ]; then ok "$d ($(ls -1 "$d" 2>/dev/null | wc -l | tr -d ' ') files)"
  else warn "$d missing"; fi
done

say "4. Personal overrides ignored by git"
touch .claude/settings.local.json
if ! grep -q '^\.claude/settings\.local\.json$' .gitignore 2>/dev/null; then
  printf '\n# Claude Code personal overrides\n.claude/settings.local.json\n' >> .gitignore
  ok "added .claude/settings.local.json to .gitignore"
else
  ok "already ignored"
fi

say "5. Python environment"
if [ -d .venv ]; then
  ok ".venv exists"
else
  warn "no .venv — create it with:"
  echo "     python -m venv .venv && source .venv/bin/activate && make setup"
fi

say "6. Repository health"
if [ -d .venv ] && [ -x .venv/bin/python ]; then
  .venv/bin/python -m pytest -q 2>&1 | tail -3 || warn "tests did not pass — fix before using Claude on this repo"
else
  warn "skipped (activate .venv and run 'make test')"
fi

say "Next"
cat <<'TXT'
  claude                 start a session in this directory
  /memory                confirm CLAUDE.md loaded
  /status-truth          honest baseline of what the repo can prove
  /metaprompt <task>     compile a rough task into a spec before working
  /permissions           review what Claude may run without asking

  Optional, for GitHub: run /install-github-app inside claude to wire up
  the @claude workflows, or add ANTHROPIC_API_KEY under
  Settings -> Secrets and variables -> Actions.
TXT
