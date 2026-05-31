# Using with Codex CLI

Codex CLI auto-loads `AGENTS.md` from the current directory (and parent
directories). This vault ships an `AGENTS.md` at the root that points at
the canonical skill in `skill/SKILL.md`.

## How it works

Codex doesn't have a "skill" mechanism the way Claude Code does. Instead,
the entire `AGENTS.md` file is loaded into context at session start. The
genealogy `AGENTS.md` is intentionally short — it explains when to
trigger genealogy work and where to find the actual workflows
(`skill/SKILL.md` and `skill/workflows/`). Codex reads those as needed.

## Starting a session

```sh
cd /path/to/your/vault
codex
```

The first thing Codex does in a fresh session is read `AGENTS.md`. Ask:

> What genealogy workflows do you know how to run?

Codex should respond by listing the workflows from `skill/SKILL.md`.

## Common usage

The skill triggers identically to Claude Code — see
[`using-with-claude-code.md`](using-with-claude-code.md) § Common usage
patterns. Same workflows, same scripts.

## Differences from Claude Code

- **No skill auto-discovery via description.** Codex doesn't match on
  trigger phrases — `AGENTS.md` is always-on. The skill is more
  proactively present in Codex; you may not need to explicitly say
  "process the inbox" — Codex may notice an `_inbox/` with content
  and offer.
- **No `/skill` UI.** The skill is invoked implicitly via your prompt.
- **No plugin distribution.** Updates come via re-running `install.sh`
  or `git pull` on the toolkit clone.

## Settings to consider

If your Codex configuration has a sandboxing or permissions layer, ensure
it allows:

- Shell execution of `_scripts/scan-pipeline/*.sh` and `*.py`.
- Read/write to `people/`, `sources/`, `media/`, `_inbox/`,
  `OPEN-QUESTIONS.md`, `MOC.md`.
- Network access if you use the LLM-interpretation pipeline path (some
  Codex sandboxes block network by default).

## Multi-agent setups

If you use both Claude Code and Codex in the same vault, no conflict —
they share the same `skill/SKILL.md` and `_scripts/`. The two wrappers
(`.claude/skills/genealogy/SKILL.md` and `AGENTS.md`) are tiny and
independent.

## Troubleshooting

- **"Codex doesn't know about the vault."** Confirm `AGENTS.md` is at
  the vault root and you launched `codex` from inside the vault.
- **"Codex is reading the file but not invoking workflows."** Try a more
  explicit prompt: "Read `skill/SKILL.md` and `skill/workflows/process-inbox.md`,
  then process the inbox." Once Codex has the skill content in context,
  it'll behave the same as Claude.
