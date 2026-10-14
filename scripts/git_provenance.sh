#!/usr/bin/env bash
# Print the Git provenance lines of the current worktree (read-only Git only).
# Called by scripts/run_simulation.sh; usable on its own.
#
#   git_tracked_modified        staged or unstaged changes to tracked files
#   git_untracked_tool_state    .serena/ only: development-tool state, not importable and not read by run.py
#   git_untracked_unclassified  every other untracked, non-ignored file, listed individually; any of them
#                               may influence execution and none is assumed harmless
#   git_ignored_python          ignored *.py / *.pth files outside .venv/ (could shadow modules: the repo
#                               root is on sys.path for `python run.py`)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

list() { if [ -n "$1" ]; then echo "$1" | tr '\n' ' ' | sed 's/ $//'; else echo none; fi; }

UNTRACKED="$(git ls-files --others --exclude-standard 2>/dev/null)"
TOOL="$(printf '%s\n' "$UNTRACKED" | grep -E '^\.serena/')"
OTHER="$(printf '%s\n' "$UNTRACKED" | grep -vE '^\.serena/' | grep -v '^$')"
IGNORED_PY="$(git ls-files --others --ignored --exclude-standard -- '*.py' '*.pth' ':(exclude).venv' 2>/dev/null)"

echo "git_tracked_modified: $([ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ] && echo yes || echo no)"
if [ -n "$TOOL" ]; then
  echo "git_untracked_tool_state: .serena/ ($(printf '%s\n' "$TOOL" | wc -l) files; development-tool state)"
else
  echo "git_untracked_tool_state: none"
fi
echo "git_untracked_unclassified: $(list "$OTHER")$([ -n "$OTHER" ] && echo ' (potentially execution-relevant; not assumed harmless)')"
echo "git_ignored_python: $(list "$IGNORED_PY")"
