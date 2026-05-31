#!/usr/bin/env bash
# install.sh — install or update the genealogy-vault toolkit into an existing
# Obsidian vault. Idempotent: re-run safely to upgrade.
#
# Usage:
#   ./install.sh /path/to/your/vault          # install or update
#   ./install.sh --force /path/to/your/vault  # also overwrite template files
#
# Copies (always overwrites):
#   skill/                  — the canonical agent-agnostic skill
#   .claude/skills/genealogy/  — Claude Code thin wrapper
#   _scripts/               — scan pipeline, taggers, migration runner
#
# Copies (skip-if-exists unless --force):
#   templates/              — person/document/media (you may have customized)
#   AGENTS.md, CLAUDE.md    — entry points (you may have other agent context)
#
# Creates if missing (never overwrites):
#   people/, sources/, media/, _inbox/   — your data directories
#   .gitignore                            — sensible defaults
#
# Stamps:
#   <vault>/.genealogy-vault-version      — installed version + date
#
# After install, run schema migrations if you're upgrading:
#   python3 <vault>/_scripts/migrate.py <vault>

set -euo pipefail

# -----------------------------------------------------------------------------
# Arguments
# -----------------------------------------------------------------------------

FORCE=0
VAULT=""
for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        --help|-h)
            sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        -*)
            echo "error: unknown flag: $arg" >&2
            exit 2
            ;;
        *)
            if [[ -n "$VAULT" ]]; then
                echo "error: only one vault path may be given" >&2
                exit 2
            fi
            VAULT="$arg"
            ;;
    esac
done

if [[ -z "$VAULT" ]]; then
    echo "usage: $0 [--force] /path/to/your/vault" >&2
    exit 2
fi

# -----------------------------------------------------------------------------
# Resolve paths
# -----------------------------------------------------------------------------

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VAULT="$( cd "$VAULT" 2>/dev/null && pwd || echo "$VAULT" )"

if [[ ! -d "$VAULT" ]]; then
    echo "error: vault path does not exist: $VAULT" >&2
    echo "create it first (mkdir -p) and re-run." >&2
    exit 1
fi

if [[ "$REPO_ROOT" == "$VAULT" ]]; then
    echo "error: cannot install into the toolkit repo itself." >&2
    echo "       repo: $REPO_ROOT" >&2
    echo "       vault: $VAULT" >&2
    exit 1
fi

VERSION="$(cat "$REPO_ROOT/VERSION")"

echo "genealogy-vault installer"
echo "  toolkit: $REPO_ROOT (v$VERSION)"
echo "  target:  $VAULT"
echo "  mode:    $([[ $FORCE -eq 1 ]] && echo 'force overwrite (incl. templates)' || echo 'idempotent (skip existing templates)')"
echo

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

# Copy a directory's contents into target, overwriting existing files.
overwrite_dir() {
    local src="$1"
    local dst="$2"
    mkdir -p "$dst"
    cp -R "$src/." "$dst/"
    echo "  ✓ updated $dst"
}

# Copy each file in src into dst, skipping ones that already exist (unless FORCE).
skip_existing_dir() {
    local src="$1"
    local dst="$2"
    mkdir -p "$dst"
    local count_copied=0
    local count_skipped=0
    while IFS= read -r -d '' src_file; do
        local rel="${src_file#$src/}"
        local dst_file="$dst/$rel"
        mkdir -p "$( dirname "$dst_file" )"
        if [[ -e "$dst_file" && $FORCE -eq 0 ]]; then
            count_skipped=$((count_skipped + 1))
        else
            cp "$src_file" "$dst_file"
            count_copied=$((count_copied + 1))
        fi
    done < <(find "$src" -type f -print0)
    echo "  ✓ $dst (copied: $count_copied, skipped existing: $count_skipped)"
}

# Place a file at dst from src, with a special rule for root-level agent
# entry points: if the file exists, write to <dst>.from-genealogy-vault
# and tell the user to merge manually.
place_agent_file() {
    local src="$1"
    local dst="$2"
    if [[ -e "$dst" && $FORCE -eq 0 ]]; then
        local sideload="${dst}.from-genealogy-vault"
        cp "$src" "$sideload"
        echo "  ⚠ $dst exists — wrote $sideload instead; merge by hand."
    else
        cp "$src" "$dst"
        echo "  ✓ $dst"
    fi
}

# Create a data directory if it doesn't exist; never overwrite contents.
ensure_data_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        echo "  + created $dir"
    fi
}

# -----------------------------------------------------------------------------
# 1. Toolkit (always overwrites — this is what makes the installer the updater)
# -----------------------------------------------------------------------------

echo "Installing toolkit..."
overwrite_dir "$REPO_ROOT/skill" "$VAULT/skill"
overwrite_dir "$REPO_ROOT/.claude/skills/genealogy" "$VAULT/.claude/skills/genealogy"
overwrite_dir "$REPO_ROOT/_scripts" "$VAULT/_scripts"

# -----------------------------------------------------------------------------
# 2. Templates (skip existing unless --force — user may have customized)
# -----------------------------------------------------------------------------

echo
echo "Installing templates..."
skip_existing_dir "$REPO_ROOT/templates" "$VAULT/templates"

# -----------------------------------------------------------------------------
# 3. Agent entry points (skip if exists; sideload if conflict)
# -----------------------------------------------------------------------------

echo
echo "Installing agent entry points..."
place_agent_file "$REPO_ROOT/CLAUDE.md" "$VAULT/CLAUDE.md"
place_agent_file "$REPO_ROOT/AGENTS.md" "$VAULT/AGENTS.md"

# -----------------------------------------------------------------------------
# 4. Data directories (create if missing, never touch contents)
# -----------------------------------------------------------------------------

echo
echo "Ensuring data directories..."
ensure_data_dir "$VAULT/people"
ensure_data_dir "$VAULT/sources"
ensure_data_dir "$VAULT/media"
ensure_data_dir "$VAULT/_inbox"
ensure_data_dir "$VAULT/_tools"

# -----------------------------------------------------------------------------
# 5. Sensible .gitignore (skip if exists)
# -----------------------------------------------------------------------------

if [[ ! -e "$VAULT/.gitignore" ]]; then
    cp "$REPO_ROOT/.gitignore" "$VAULT/.gitignore"
    echo "  + created $VAULT/.gitignore"
fi

# -----------------------------------------------------------------------------
# 6. Stamp the version
# -----------------------------------------------------------------------------

STAMP_FILE="$VAULT/.genealogy-vault-version"
TODAY="$(date -u +%Y-%m-%d)"
{
    echo "$VERSION"
    echo "$TODAY"
} > "$STAMP_FILE"
echo
echo "Stamped: $STAMP_FILE → $VERSION @ $TODAY"

# -----------------------------------------------------------------------------
# 7. Done — post-install advice
# -----------------------------------------------------------------------------

cat <<EOF

Install complete.

Next steps:
  1. Open $VAULT in Obsidian (any vault root works).
  2. Open it in Claude Code OR Codex CLI — the skill is auto-discovered via
     .claude/skills/genealogy/ (Claude Code) or AGENTS.md (Codex).
  3. Copy skill/family-context.md.template to skill/family-context.md and
     fill in your tree root + surnames.
  4. (If upgrading) run schema migrations:
       python3 $VAULT/_scripts/migrate.py $VAULT
  5. Drop a test PDF in $VAULT/_inbox/ and say "process the inbox" to your
     agent.

EOF
