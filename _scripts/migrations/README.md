# Schema Migrations

When the schemas in `templates/` change in a breaking way (field renamed,
type changed, key removed), a migration script lives here so existing user
vaults can upgrade cleanly.

## Discipline

A breaking schema change is **only** allowed if the same commit:

1. Adds a migration script at `_scripts/migrations/YYYY-MM-DD-<slug>.py`
2. Notes the migration in `CHANGELOG.md` under a "Migration required" header
3. Bumps `VERSION`

This is enforced by code review, not CI (yet). See `CHANGELOG.md` for the
rule statement.

## Running migrations

After re-running `install.sh` (or pulling a new version), run:

```sh
python3 _scripts/migrate.py /path/to/your/vault
```

The runner reads `<vault>/.genealogy-vault-version` (the version stamped by
`install.sh` at install time), compares it against the current `VERSION`,
and runs every migration script with a date stamp between the two. Each
script:

- Is idempotent — re-running on an already-migrated vault is a no-op.
- Operates on `<vault>/people/`, `<vault>/sources/`, and `<vault>/media/`
  only. Tooling directories (`skill/`, `_scripts/`, `_tools/`,
  `templates/`) are out of scope.
- Reports per-file what it changed.

## Writing a migration

Template:

```python
#!/usr/bin/env python3
"""Migration: <one-line description>.

Date: YYYY-MM-DD
From: X.Y.Z (last version before this change)
To:   X.Y.(Z+1)

What this migration does:
- Adds field `foo:` to every person file.
- Renames sidecar field `bar:` to `baz:`.
- (etc.)
"""
from pathlib import Path
import sys


def migrate(vault: Path) -> int:
    """Returns the number of files modified."""
    count = 0
    for path in (vault / "people").glob("*.md"):
        # ... your edit here ...
        count += 1
    return count


if __name__ == "__main__":
    vault = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    n = migrate(vault)
    print(f"Migrated {n} files")
```

The runner imports the file's `migrate(vault)` function and calls it.

## Idempotency

Every migration MUST be idempotent. The runner does not track which scripts
have run before — it just runs every script whose date stamp falls in the
upgrade range. If a user re-runs the installer, all migrations in range
run again. If your migration would corrupt data on a second run, it's
wrong.

Common idempotent patterns:

- "If field `foo:` is missing, add it." (Adding twice = no-op.)
- "If field `bar:` exists, rename to `baz:` and remove `bar:`." (Second
  run finds no `bar:` and does nothing.)
- "If sidecar's `type:` is in {old aliases}, replace with canonical."
  (Second run sees canonical and skips.)
