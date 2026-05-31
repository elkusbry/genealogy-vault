# Quickstart — Hobbyist (5 minutes)

For genealogy enthusiasts who want to try this without setting up much.

## What you'll need

- A computer (Mac, Linux, or Windows).
- [Obsidian](https://obsidian.md/) (free).
- One AI coding agent:
  - [Claude Code](https://www.anthropic.com/claude-code) (recommended for
    first time — better skill UX), OR
  - [Codex CLI](https://github.com/openai/codex) (also works).
- [git](https://git-scm.com/downloads) (probably already installed).

## Step 1 — Clone this repo

```sh
git clone https://github.com/<your-username>/genealogy-vault.git
cd genealogy-vault
```

## Step 2 — Open in Obsidian

- macOS: `open -a Obsidian .`
- Linux/Windows: Launch Obsidian → "Open folder as vault" → pick the
  `genealogy-vault` directory.

You should see the file tree on the left. Click [`demo/MOC.md`](../demo/MOC.md)
to see the Riverstone family tree.

**Spend 2 minutes clicking around.** Try:

- Click on a wikilink like `[[Heinrich Riverstone (1885)]]`.
- Open Obsidian's graph view (Ctrl/Cmd + G) and see the family network.
- Open `demo/sources/1937-letter-from-heinrich-to-klara-vienna.md` —
  notice the `translation:` companion key in the frontmatter.

## Step 3 — Open in Claude Code (or Codex)

In your terminal:

```sh
cd genealogy-vault
claude         # or: codex
```

Then ask:

> Read CLAUDE.md and tell me what this vault does.

The agent will load the skill and explain. Now try:

> Add a new person: my grandmother Sarah Cohen, born 1932 in Brooklyn,
> married to Benjamin Cohen.

The agent should ask follow-up questions (per `skill/workflows/add-person.md`),
then create `people/Sarah Cohen (1932).md` with full schema, ready for
you to fill in more.

## Step 4 — Process your first scan

If you have a scanned family document handy:

1. Drop it into `_inbox/` (the repo's `_inbox/`, not the demo's).
2. Tell the agent:
   > Process the inbox.

The OCR pipeline will run, the agent will extract entities, create a
sidecar, and update any person files it finds matches for.

> **Note:** OCR requires Tesseract and ocrmypdf installed locally. See
> [`_scripts/scan-pipeline/README.md`](../_scripts/scan-pipeline/README.md)
> for install instructions.

## Step 5 — When you're ready, swap in your own family

1. Delete the `demo/` directory.
2. Copy `skill/family-context.md.template` to `skill/family-context.md`
   and fill in your tree root and surnames.
3. Edit (or create) a `MOC.md` at the repo root to anchor your own tree.
4. Start adding people, processing scans, and tagging photos.

## Where to go next

- [Workflows reference](workflows.md) — every workflow with triggers and
  steps.
- [Using with Claude Code](using-with-claude-code.md) — skill discovery,
  permissions, tips.
- [Using with Codex](using-with-codex.md) — AGENTS.md, settings.
