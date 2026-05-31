# Upgrading

This vault separates tooling from data, so upgrades are safe. Pick the
path that matches how you set up.

## Power-user path (you used `install.sh`)

```sh
cd ~/code/genealogy-vault       # wherever you cloned the toolkit
git pull
./install.sh /path/to/your/vault
python3 /path/to/your/vault/_scripts/migrate.py /path/to/your/vault
```

The installer is idempotent — re-running it overwrites tooling files,
skips your customized templates, sideloads any conflicting agent entry
points (`CLAUDE.md.from-genealogy-vault`).

`migrate.py` reads `<vault>/.genealogy-vault-version`, compares to the
new `VERSION`, and runs every migration in range.

## Template-clone path (you used "Use this template" on GitHub)

If you forked the repo or used the GitHub template button, the tooling
lives in your fork. To pull upstream tooling updates without conflicting
on your data:

```sh
cd /path/to/your/fork
git remote add upstream https://github.com/<orig-owner>/genealogy-vault.git
git fetch upstream
git checkout upstream/main -- skill .claude/skills _scripts _tools \
                              templates VERSION CHANGELOG.md
git commit -m "Pull upstream tooling"
python3 _scripts/migrate.py .
```

The targeted checkout pulls ONLY the tooling directories; your
`people/`, `sources/`, `media/`, `_inbox/`, and `MOC.md` are untouched.

## Reading the CHANGELOG

[`CHANGELOG.md`](../CHANGELOG.md) lists every release. Migrations are
called out under "Migration required" — if your installed version is
older than the most recent migration date, run `migrate.py` after
upgrading.

## The migration discipline

Breaking schema changes (field added, renamed, removed in
`templates/*.md`) require:

1. A migration script in `_scripts/migrations/YYYY-MM-DD-<slug>.py`
2. A `CHANGELOG.md` entry
3. A bump of `VERSION`

This means: if you update tooling and your `templates/` change, there
will always be a migration available to fix your existing data. See
[`../_scripts/migrations/README.md`](../_scripts/migrations/README.md)
for the rules.

## Rollback

The toolkit doesn't ship a rollback command, but `_scripts/migrate.py`
is idempotent and the installer is non-destructive to data. To roll
back:

1. `git checkout` an older tag on the toolkit repo.
2. Re-run `install.sh`.
3. If a forward migration ran, you may need a manual backward migration
   (which is rare and called out in CHANGELOG when it happens).

Always commit your vault before running migrations so you can `git diff`
or revert.

## Frequency

Toolkit releases follow semver:

- **Patch** (0.1.X) — script fixes, doc improvements, no schema changes.
  Safe to install any time.
- **Minor** (0.X.0) — new workflows, new optional schema fields. Run
  `migrate.py` after install.
- **Major** (X.0.0) — breaking schema changes. Read the CHANGELOG;
  migrations are required.
