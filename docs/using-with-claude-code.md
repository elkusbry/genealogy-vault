# Using with Claude Code

The genealogy skill is registered at `.claude/skills/genealogy/SKILL.md`.
Claude Code's skill-discovery picks it up automatically when you start a
session in the vault root.

## How the skill triggers

Claude Code reads the `description:` field in the skill's YAML frontmatter
and triggers the skill when your prompt matches. Examples:

- "Process the inbox" — matches `process inbox` trigger
- "Add my grandmother Sarah" — matches `add a person` + person name
- "Translate this German letter" — matches `translate this document`
- "Tag the photos" — matches `tag photos`

When the skill is triggered, Claude reads `skill/SKILL.md`, then the
relevant workflow file under `skill/workflows/`, then performs the work.

## Recommended settings

- **Auto-edit (acceptEdits) mode** for routine work — the skill makes
  bounded edits to your vault files and you'll want to move fast.
- **Plan mode** for big bulk imports — let Claude plan how it'll process
  a 50-PDF inbox before it touches anything.

## Skill content

The Claude Code skill is a **thin wrapper**. The actual workflow content
lives at `skill/SKILL.md` and `skill/workflows/`. This is intentional —
both Claude Code and Codex point at the same source of truth.

If you want to customize the skill's triggers (e.g., add your family's
surnames), edit `skill/family-context.md` (copy from `.template`). The
skill reads it on every genealogy task.

## Common usage patterns

### "I dropped some scans"

```
User:  I dropped scans in.
Claude: [reads SKILL.md + workflows/process-inbox.md]
        [lists what's in _inbox/]
        [runs process-scans.sh in background, monitors log]
        [interprets each .txt → _inbox/*.md]
        [runs move_inbox_to_sources.py]
        [for each new source: extracts facts into people/]
        [reports summary]
```

### "Add a person"

```
User:  Add my great-aunt Edith Williams, born 1898, died 1972, sister
       of my great-grandfather John Williams (1895).
Claude: [reads workflows/add-person.md]
        [checks if Edith already exists]
        [creates people/Edith Williams (1898).md from template]
        [updates John Williams's file: appends to siblings:]
        [computes branch + generation + tags]
        [reports]
```

### "Review what's open"

```
User:  What research questions are still open?
Claude: [reads workflows/research-and-maintenance.md § Review open questions]
        [scans people/*.md for todo: arrays]
        [regenerates OPEN-QUESTIONS.md]
        [reports counts by category]
```

## Permissions

The skill needs:
- **Read** access to the whole vault.
- **Write** access to `people/`, `sources/`, `media/`, `_inbox/`,
  `OPEN-QUESTIONS.md`, `MOC.md`.
- **Bash** for running `_scripts/*` and OCR.

In Claude Code settings, you may want to add an allowlist for the
common shell commands the skill runs:

```json
"permissions": {
  "allow": [
    "Bash(_scripts/scan-pipeline/process-scans.sh*)",
    "Bash(python3 _scripts/scan-pipeline/move_inbox_to_sources.py*)",
    "Bash(python3 _scripts/taggers/*)"
  ]
}
```

See your Claude Code docs for the exact settings file path.

## Troubleshooting

- **"The skill isn't triggering."** Confirm `.claude/skills/genealogy/SKILL.md`
  exists in the vault root. Restart your Claude Code session.
- **"Claude tried to OCR a born-digital PDF."** Born-digital PDFs (with
  existing text layers) still need OCR-pipeline routing through the
  inbox flow because the skill expects every source to have a sidecar.
  This is by design.
- **"My family-context.md isn't being read."** Make sure it's at
  `skill/family-context.md` (not `family-context.md.template`).
