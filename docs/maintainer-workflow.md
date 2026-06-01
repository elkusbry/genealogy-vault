# Maintainer workflow

How to make changes to the genealogy-vault toolkit (scripts, taggers,
skill content) and have them flow correctly to your own vault AND to
downstream users.

This page is the answer to: *"I improved `build_photo_tagger.py` in my
personal vault — how do I get that change into the public repo?"*

## The relationship between repos

Two distinct repos live on your machine:

```
┌──────────────────────────────────────────────────────────────┐
│  THE TOOLKIT (public, source of truth for tooling)           │
│  ~/Repo/genealogy-vault                                       │
│  • skill/, _scripts/, _tools/, templates/                    │
│  • install.sh, migrate.py                                    │
│  • demo/ (Riverstones)                                       │
│  • Versioned, tagged, released                               │
└──────────────────────────────────────────────────────────────┘
                            │  install.sh / git pull
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  YOUR PERSONAL VAULT (private)                                │
│  ~/Repo/genealogy                                             │
│  • people/, sources/, media/ (real data, never touched)      │
│  • _inbox/ (your drop zone)                                  │
│  • skill/, _scripts/, _tools/, templates/                    │
│    ← these are COPIES installed by install.sh                │
└──────────────────────────────────────────────────────────────┘
```

**The rule:** tooling files in your personal vault are downstream copies.
Edit them upstream (in the toolkit), then re-install.

## The supported dev loop

When you want to improve a tool:

1. **Edit in the toolkit repo.** Open `~/Repo/genealogy-vault` and modify
   `_scripts/taggers/build_photo_tagger.py` (or whatever).
2. **Test in the toolkit.** The toolkit IS itself a working vault — it
   has `demo/` (the Riverstones) and the install script can build the
   taggers against it. Use the symlink trick:
   ```sh
   cd ~/Repo/genealogy-vault
   ln -sf demo/people people
   ln -sf demo/sources sources
   ln -sf demo/media media
   python3 _scripts/taggers/build_photo_tagger.py
   open _tools/photo-tagger.html  # eyeball the result
   rm -f people sources media
   ```
   (Or run the full CI checks: `python3 _scripts/validate_skill.py`,
   `ruff check _scripts/`, `shellcheck install.sh`.)
3. **Commit upstream.** Standard git flow in the toolkit repo.
4. **Re-install into your personal vault.**
   ```sh
   ~/Repo/genealogy-vault/install.sh ~/Repo/genealogy
   ```
   This overwrites `~/Repo/genealogy/_scripts/`, `_tools/`, `skill/`,
   `.claude/skills/genealogy/`. Your `people/`, `sources/`, `media/`,
   `_inbox/`, and `MOC.md` are untouched.
5. **Release** (when it's a meaningful improvement, not every commit):
   - Bump `VERSION` per semver
   - Add a `CHANGELOG.md` entry
   - Tag: `git tag -a v0.4.0 -m "Release v0.4.0" && git push --tags`
   - Cut a GitHub release pointing at the tag
   - Downstream users `git pull && ./install.sh /their/vault`

## What if your personal vault has drifted?

Maybe you edited a script *in your personal vault* before this workflow
was documented, and now those changes don't exist upstream. The drift-
check script surfaces these:

```sh
~/Repo/genealogy-vault/_scripts/drift_check.sh ~/Repo/genealogy
```

It diffs every file the toolkit owns against your personal vault's copy
and prints what's different. For each drifted file, you decide:

- **The personal copy has improvements** → copy back to the toolkit,
  commit, push, then re-install.
- **The personal copy is stale** → re-install will overwrite it; nothing
  to do.

Run drift-check before every install if you're worried about losing
local changes.

## What lives where — the canonical list

These directories in your personal vault are **owned by the toolkit**.
Never edit them in your personal vault; always edit in the toolkit and
re-install:

| Path | Owned by |
|---|---|
| `skill/SKILL.md` | toolkit |
| `skill/workflows/` | toolkit |
| `skill/schemas/` | toolkit |
| `skill/family-context.md.template` | toolkit |
| `_scripts/scan-pipeline/` | toolkit |
| `_scripts/taggers/` | toolkit |
| `_scripts/migrate.py` | toolkit |
| `_scripts/migrations/` | toolkit |
| `_scripts/validate_skill.py` | toolkit |
| `templates/person.md`, `document.md`, `media.md` | toolkit |
| `.claude/skills/genealogy/SKILL.md` | toolkit |
| `CLAUDE.md`, `AGENTS.md` | toolkit (sideloaded on conflict) |

These are **yours**, never touched by the toolkit:

| Path | Owned by |
|---|---|
| `skill/family-context.md` | you (filled from `.template` on first use) |
| `people/`, `sources/`, `media/`, `_inbox/` | you |
| `MOC.md`, `OPEN-QUESTIONS.md` | you |
| `_tools/document-tagger.html`, `photo-tagger.html` | you (built artifacts) |
| `.obsidian/` | you |
| `.git/` | you |

## What about Bryan's existing personal vault?

If you (or anyone) had a personal vault with tooling that predates this
public repo, you have a one-time choice to make:

- **Option A (recommended): migrate to the install-from-toolkit model.**
  Treat the toolkit as upstream. Run `drift_check.sh` to surface
  divergences, port anything you want to keep up to the toolkit, then
  run `install.sh` to overwrite your local copies with upstream
  versions. From then on, your dev loop is steps 1–5 above.
- **Option B: keep them independent forever.** Your personal vault's
  scripts will diverge over time from the public toolkit. Fine for
  one-person projects, painful if you ever want to share an
  improvement. Not recommended.

## Pull requests from outside contributors

If a stranger submits a PR improving `build_photo_tagger.py`:

1. The PR lands in the toolkit repo (`~/Repo/genealogy-vault`).
2. CI runs (`validate_skill.py`, `ruff`, `shellcheck`, install smoke,
   tagger build, fixture validation).
3. You review, merge.
4. Re-install into your personal vault to get the change yourself.
5. Tag a release for downstream users.

The contributor doesn't need to know anything about your personal
vault. The contract is the toolkit; the toolkit's CI gates that
contract.

## Common gotchas

- **"I edited a tagger script in my personal vault and now the next
  install will wipe it."** Run `drift_check.sh` first. Port the change
  upstream before re-installing.
- **"I want a feature that's family-specific to me."** Add it to
  `skill/family-context.md` (the user-filled, untracked one). Don't
  put family-specific code in the toolkit.
- **"My personal vault's `_inbox/` is full of scans I don't want
  installed elsewhere."** The toolkit's `_inbox/` is gitignored and
  empty in the public repo. The installer creates `_inbox/` in target
  vaults but never copies content into it.
- **"What's the rule for editing CLAUDE.md or AGENTS.md?"** Edit in the
  toolkit; the installer sideloads to `*.from-genealogy-vault` if the
  target file has been customized. Merge by hand if you've added your
  own per-project agent context.
