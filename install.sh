#!/usr/bin/env bash
set -euo pipefail

# install.sh — Install the `ddd` skill for Claude Code / Codex / Gemini.
#
# Usage:
#   ./install.sh                 # install to every supported CLI (default)
#   ./install.sh --claude        # install only for Claude Code
#   ./install.sh --codex         # install only for Codex CLI
#   ./install.sh --gemini        # install only for Gemini CLI
#   ./install.sh --uninstall     # remove the skill from every detected CLI
#   ./install.sh --prefix DIR    # override HOME (for testing)

SKILL_NAME="ddd"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${HOME}"

want_claude=0
want_codex=0
want_gemini=0
uninstall=0
explicit=0

while [ $# -gt 0 ]; do
  case "$1" in
    --claude) want_claude=1; explicit=1 ;;
    --codex) want_codex=1; explicit=1 ;;
    --gemini) want_gemini=1; explicit=1 ;;
    --all) want_claude=1; want_codex=1; want_gemini=1; explicit=1 ;;
    --uninstall) uninstall=1 ;;
    --prefix) shift; PREFIX="$1" ;;
    -h|--help)
      sed -n '3,14p' "$0"
      exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ "$explicit" -eq 0 ]; then
  want_claude=1
  want_codex=1
  want_gemini=1
fi

copy_skill() {
  local target="$1"
  mkdir -p "$target/references"
  cp "$SCRIPT_DIR/SKILL.md" "$target/SKILL.md"
  cp "$SCRIPT_DIR/references/"*.md "$target/references/"
  echo "  installed -> $target"
}

remove_skill() {
  local target="$1"
  if [ -d "$target" ]; then
    rm -rf "$target"
    echo "  removed   -> $target"
  fi
}

process_cli() {
  local label="$1"
  local base="$2"
  local target="$base/skills/$SKILL_NAME"
  echo "[$label]"
  if [ "$uninstall" -eq 1 ]; then
    remove_skill "$target"
  else
    copy_skill "$target"
  fi
}

[ "$want_claude" -eq 1 ] && process_cli "Claude Code" "$PREFIX/.claude"
[ "$want_codex" -eq 1 ] && process_cli "Codex CLI" "$PREFIX/.codex"
[ "$want_gemini" -eq 1 ] && process_cli "Gemini CLI" "$PREFIX/.gemini"

if [ "$uninstall" -eq 1 ]; then
  echo "done: uninstall complete"
else
  echo "done: installed skill '$SKILL_NAME'"
  echo ""
  echo "Activate with:"
  echo "  Claude Code: /$SKILL_NAME"
  echo "  Codex CLI:   /$SKILL_NAME   (add to AGENTS.md if needed)"
  echo "  Gemini CLI:  /$SKILL_NAME   (or via activate_skill)"
fi
