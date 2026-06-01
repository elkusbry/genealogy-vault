#!/usr/bin/env bash
# drift_check.sh — compare this toolkit's tooling files against a target
# vault's copies, and report what's different. Helps maintainers see
# whether their personal vault has local edits that should be ported
# back upstream before re-running install.sh.
#
# Usage:
#   ./drift_check.sh /path/to/your/vault
#
# Exits 0 even when drift is found — the goal is to surface, not to fail.

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 /path/to/your/vault" >&2
    exit 2
fi

VAULT="$1"
REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

if [[ ! -d "$VAULT" ]]; then
    echo "error: vault does not exist: $VAULT" >&2
    exit 1
fi

echo "drift check"
echo "  toolkit: $REPO_ROOT"
echo "  vault:   $VAULT"
echo

# Directories the toolkit owns (canonical list in docs/maintainer-workflow.md)
OWNED_DIRS=(
    "skill"
    "_scripts/scan-pipeline"
    "_scripts/taggers"
    "_scripts/migrations"
    "templates"
    ".claude/skills/genealogy"
)
OWNED_FILES=(
    "_scripts/migrate.py"
    "_scripts/validate_skill.py"
    "_scripts/drift_check.sh"
    "install.sh"
    "CLAUDE.md"
    "AGENTS.md"
)

# Paths to ignore when reporting "only in vault" — these are working
# files, OS noise, or local-only directories that legitimately don't
# belong in the public toolkit.
IGNORE_PATTERNS=(
    '.DS_Store'
    '/__pycache__/'
    '.pyc'
    '/.ocr-cache/'
    '/logs/'
    '/archive/'       # one-off migration scripts kept locally
    '/.in_use/'
)

is_ignored() {
    local path="$1"
    for pat in "${IGNORE_PATTERNS[@]}"; do
        if [[ "$path" == *"$pat"* ]]; then
            return 0
        fi
    done
    return 1
}

total_drifted=0
total_missing_in_vault=0
total_only_in_vault=0
total_ignored=0

check_file() {
    local rel="$1"
    local src="$REPO_ROOT/$rel"
    local dst="$VAULT/$rel"
    if [[ ! -e "$dst" ]]; then
        echo "  - MISSING in vault: $rel"
        total_missing_in_vault=$((total_missing_in_vault + 1))
        return
    fi
    if ! diff -q "$src" "$dst" >/dev/null 2>&1; then
        echo "  ≠ DRIFTED: $rel"
        total_drifted=$((total_drifted + 1))
    fi
}

check_dir() {
    local rel="$1"
    local src="$REPO_ROOT/$rel"
    local dst="$VAULT/$rel"
    if [[ ! -d "$src" ]]; then
        echo "  (toolkit has no $rel — skipping)"
        return
    fi
    # Files present in toolkit
    while IFS= read -r -d '' src_file; do
        local sub="${src_file#"$src"/}"
        check_file "$rel/$sub"
    done < <(find "$src" -type f -print0)
    # Files present in vault but not in toolkit (likely the user's old additions)
    if [[ -d "$dst" ]]; then
        while IFS= read -r -d '' dst_file; do
            local sub="${dst_file#"$dst"/}"
            if [[ ! -e "$src/$sub" ]]; then
                if is_ignored "$rel/$sub"; then
                    total_ignored=$((total_ignored + 1))
                    continue
                fi
                echo "  + ONLY in vault (not in toolkit): $rel/$sub"
                total_only_in_vault=$((total_only_in_vault + 1))
            fi
        done < <(find "$dst" -type f -print0)
    fi
}

echo "== files =="
for f in "${OWNED_FILES[@]}"; do
    check_file "$f"
done

echo
echo "== directories =="
for d in "${OWNED_DIRS[@]}"; do
    echo "-- $d --"
    check_dir "$d"
done

echo
echo "Summary:"
echo "  drifted (differ between toolkit and vault): $total_drifted"
echo "  missing in vault (toolkit has, vault does not): $total_missing_in_vault"
echo "  only in vault (vault-local additions): $total_only_in_vault"
echo "  ignored (noise/logs/cache filtered): $total_ignored"
echo
if [[ $total_drifted -gt 0 ]]; then
    echo "→ Drifted files: diff manually to decide whether to port upstream:"
    echo "    diff -u $REPO_ROOT/<path> $VAULT/<path>"
fi
if [[ $total_only_in_vault -gt 0 ]]; then
    echo "→ Vault-local additions: if they're general-purpose tooling, copy"
    echo "  them into the toolkit. If they're family-specific, leave them in"
    echo "  your vault."
fi
