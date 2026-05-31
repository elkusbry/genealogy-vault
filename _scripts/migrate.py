#!/usr/bin/env python3
"""Run schema migrations against a target vault.

Reads <vault>/.genealogy-vault-version (the version stamped by install.sh),
compares it to the current VERSION file at the repo root, and runs every
migration script under _scripts/migrations/ whose date stamp falls in the
upgrade range.

Usage:
    python3 _scripts/migrate.py [/path/to/vault]

If no vault path is given, defaults to the current working directory.

Each migration script:
- Is named YYYY-MM-DD-<slug>.py
- Defines a `migrate(vault: Path) -> int` function returning files modified
- Is idempotent — re-running on an already-migrated vault is a no-op

See _scripts/migrations/README.md for details.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
VERSION_FILE = REPO_ROOT / "VERSION"
STAMP_FILE_NAME = ".genealogy-vault-version"

MIGRATION_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.py$")


def read_version(path: Path) -> str:
    return path.read_text().strip()


def list_migrations() -> list[tuple[str, Path]]:
    """Return [(date-stamp, path)] for every valid migration script, sorted."""
    found = []
    for p in sorted(MIGRATIONS_DIR.glob("*.py")):
        m = MIGRATION_NAME_RE.match(p.name)
        if m:
            found.append((m.group(1), p))
    return found


def load_migrate_callable(path: Path):
    """Dynamic-import a migration module and return its `migrate` function."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "migrate"):
        raise RuntimeError(f"{path} is missing a migrate(vault) function")
    return mod.migrate


def main() -> int:
    vault = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not vault.is_dir():
        print(f"error: vault path {vault} is not a directory", file=sys.stderr)
        return 1

    stamp_file = vault / STAMP_FILE_NAME
    if not stamp_file.exists():
        print(
            f"note: no {STAMP_FILE_NAME} found in {vault} — "
            f"running all available migrations (treating vault as pre-history).",
            file=sys.stderr,
        )
        installed = "0000-00-00"
    else:
        # Stamp file format: "X.Y.Z\n<installed-date>" — we read the date if
        # present, fall back to a date-less version line.
        stamp_lines = stamp_file.read_text().strip().splitlines()
        installed = stamp_lines[1] if len(stamp_lines) > 1 else "0000-00-00"

    if not VERSION_FILE.exists():
        print(f"error: missing {VERSION_FILE}", file=sys.stderr)
        return 1
    current = read_version(VERSION_FILE)

    migrations = list_migrations()
    pending = [(d, p) for (d, p) in migrations if d > installed]

    if not pending:
        print(f"vault is up to date (installed: {installed}, current: {current})")
        return 0

    print(f"Vault: {vault}")
    print(f"Installed marker: {installed}")
    print(f"Current toolkit version: {current}")
    print(f"Pending migrations: {len(pending)}")
    print()

    total_files = 0
    for date_stamp, path in pending:
        print(f"=== {path.name} ===")
        try:
            fn = load_migrate_callable(path)
            n = fn(vault)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"  modified {n} files")
        total_files += n

    # Update the stamp to today + current version
    today = pending[-1][0]  # the latest migration's date stamp
    stamp_file.write_text(f"{current}\n{today}\n")
    print()
    print(f"Done. Total files modified: {total_files}")
    print(f"Stamp updated: {current} @ {today}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
