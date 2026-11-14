#!/usr/bin/env bash
# Install the job-handoff skill for Claude Code and Codex, and put the
# `handoff` command on the PATH. The links point into this checkout, so
# `git pull` updates the installed skill.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
skill=$here/skills/job-handoff

mkdir -p "$HOME/.claude/skills" "$HOME/.agents/skills" "$HOME/.local/bin"
ln -sfn "$skill" "$HOME/.claude/skills/job-handoff"
ln -sfn "$skill" "$HOME/.agents/skills/job-handoff"
ln -sf "$skill/scripts/handoff" "$HOME/.local/bin/handoff"

echo "job-handoff installed:"
echo "  Claude Code  $HOME/.claude/skills/job-handoff"
echo "  Codex        $HOME/.agents/skills/job-handoff"
echo "  command      $HOME/.local/bin/handoff"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "Add $HOME/.local/bin to your PATH to use the handoff command." ;;
esac
