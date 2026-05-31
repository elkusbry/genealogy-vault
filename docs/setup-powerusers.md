# Setup — Power Users (30 minutes)

For Obsidian users who already have a working vault and want to add this
toolkit without disrupting their setup.

## The installer

`install.sh` is idempotent: run it once to install, re-run it to upgrade.
It copies tooling into your vault; it never touches your data.

## What gets installed

| Path in your vault | Behavior |
|---|---|
| `skill/` | Overwritten — canonical skill |
| `.claude/skills/genealogy/` | Overwritten — Claude Code wrapper |
| `_scripts/` | Overwritten — pipeline, taggers, migration runner |
| `templates/person.md` etc. | Skip-if-exists (use `--force` to overwrite) |
| `CLAUDE.md`, `AGENTS.md` | Sideload as `*.from-genealogy-vault` if present |
| `people/`, `sources/`, `media/`, `_inbox/`, `_tools/` | Create if missing, never touch contents |
| `.genealogy-vault-version` | Always update (the version stamp) |
| `.gitignore` | Create if missing |

## Step 1 — Clone the toolkit somewhere safe

Pick a location OUTSIDE your vault — e.g., `~/code/genealogy-vault/`.
This is where you'll pull updates.

```sh
git clone https://github.com/<your-username>/genealogy-vault.git ~/code/genealogy-vault
```

## Step 2 — Run the installer against your vault

```sh
~/code/genealogy-vault/install.sh /path/to/your/obsidian/vault
```

The installer prints a summary of what it copied and ends with a "next
steps" section. Read it.

## Step 3 — If you had existing CLAUDE.md or AGENTS.md

The installer sideloads to `CLAUDE.md.from-genealogy-vault` and
`AGENTS.md.from-genealogy-vault` rather than overwriting. Open both and
merge the relevant sections into your existing files.

The bits you need to merge:

- Triggers (when the skill should fire).
- The pointer to `skill/SKILL.md` as the canonical manual.
- The "tooling vs data separation" rule.

## Step 4 — Customize family-context.md

```sh
cp /path/to/your/vault/skill/family-context.md.template \
   /path/to/your/vault/skill/family-context.md
```

Edit to add your tree root, branches, surnames, known discrepancies. The
agent reads this on every genealogy task.

## Step 5 — (Optional) Initialize Charted Roots integration

If you use the [Charted Roots](https://github.com/skiqh/charted-roots)
Obsidian plugin: nothing to do — the schemas already include the
optional `cr_id`, `cr_type`, `born`, `died`, etc. fields.

If you don't use it: leave those fields blank. They're harmless.

## Step 6 — Verify

In your vault, open it with Claude Code or Codex and ask:

> What genealogy workflows do you know how to run?

The agent should list workflows from `skill/SKILL.md`. If it doesn't,
check that:

- `CLAUDE.md` (or `AGENTS.md` for Codex) is at the vault root.
- The skill content is at `skill/SKILL.md` and `skill/workflows/`.
- The agent is started in the vault root directory.

## Updating later

```sh
cd ~/code/genealogy-vault
git pull
./install.sh /path/to/your/vault
python3 /path/to/your/vault/_scripts/migrate.py /path/to/your/vault
```

The `migrate.py` step runs any schema migrations introduced since your
installed version. See [`upgrading.md`](upgrading.md) for the discipline.

## Going back

If you want to remove this toolkit from your vault:

```sh
rm -rf /path/to/your/vault/skill/
rm -rf /path/to/your/vault/.claude/skills/genealogy/
rm -rf /path/to/your/vault/_scripts/
rm -rf /path/to/your/vault/_tools/
rm -f /path/to/your/vault/.genealogy-vault-version
# Restore your own CLAUDE.md / AGENTS.md from backup if you had them.
```

Your `people/`, `sources/`, `media/`, and `_inbox/` are untouched.
