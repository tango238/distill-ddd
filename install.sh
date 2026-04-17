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

copy_body() {
  local target="$1"
  mkdir -p "$target/references"
  cp "$SCRIPT_DIR/SKILL.md" "$target/SKILL.md"
  cp "$SCRIPT_DIR/references/"*.md "$target/references/"
}

remove_path() {
  local p="$1"
  if [ -e "$p" ]; then
    rm -rf "$p"
    echo "  removed   -> $p"
  fi
}

write_codex_entry() {
  local body="$1"; local entry="$2"
  mkdir -p "$(dirname "$entry")"
  cat > "$entry" <<EOF
# /ddd — Interactive Domain-Driven Design

Follow the skill defined at \`$body/SKILL.md\`.

When invoked:
1. Read \`$body/SKILL.md\` for phase structure and interaction rules.
2. For a specific phase, also read \`$body/references/phase-<name>.md\`.
3. Save artifacts to \`docs/domain/\` in the current project.

Arguments: \$ARGUMENTS
EOF
}

write_gemini_entry() {
  local body="$1"; local entry="$2"
  mkdir -p "$(dirname "$entry")"
  cat > "$entry" <<EOF
description = "Interactive Domain-Driven Design modeling facilitator (DDD Distilled based)"
prompt = """
Follow the skill defined at $body/SKILL.md.

When invoked:
1. Read $body/SKILL.md for phase structure and interaction rules.
2. For a specific phase, also read $body/references/phase-<name>.md.
3. Save artifacts to docs/domain/ in the current project.

Arguments: {{args}}
"""
EOF
}

install_claude() {
  local body="$PREFIX/.claude/skills/$SKILL_NAME"
  echo "[Claude Code]"
  copy_body "$body"
  echo "  installed -> $body"
}

install_codex() {
  local body="$PREFIX/.codex/skills/$SKILL_NAME"
  local entry="$PREFIX/.codex/prompts/$SKILL_NAME.md"
  echo "[Codex CLI]"
  copy_body "$body"
  write_codex_entry "$body" "$entry"
  echo "  installed -> $body"
  echo "  entry     -> $entry"
}

install_gemini() {
  local body="$PREFIX/.gemini/skills/$SKILL_NAME"
  local entry="$PREFIX/.gemini/commands/$SKILL_NAME.toml"
  echo "[Gemini CLI]"
  copy_body "$body"
  write_gemini_entry "$body" "$entry"
  echo "  installed -> $body"
  echo "  entry     -> $entry"
}

uninstall_claude() {
  echo "[Claude Code]"
  remove_path "$PREFIX/.claude/skills/$SKILL_NAME"
}

uninstall_codex() {
  echo "[Codex CLI]"
  remove_path "$PREFIX/.codex/skills/$SKILL_NAME"
  remove_path "$PREFIX/.codex/prompts/$SKILL_NAME.md"
}

uninstall_gemini() {
  echo "[Gemini CLI]"
  remove_path "$PREFIX/.gemini/skills/$SKILL_NAME"
  remove_path "$PREFIX/.gemini/commands/$SKILL_NAME.toml"
}

if [ "$uninstall" -eq 1 ]; then
  [ "$want_claude" -eq 1 ] && uninstall_claude
  [ "$want_codex" -eq 1 ] && uninstall_codex
  [ "$want_gemini" -eq 1 ] && uninstall_gemini
  echo "done: uninstall complete"
else
  [ "$want_claude" -eq 1 ] && install_claude
  [ "$want_codex" -eq 1 ] && install_codex
  [ "$want_gemini" -eq 1 ] && install_gemini
  echo "done: installed skill '$SKILL_NAME'"
  echo ""
  echo "Invoke with /$SKILL_NAME in your CLI."
fi
