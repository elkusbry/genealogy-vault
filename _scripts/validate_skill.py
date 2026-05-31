#!/usr/bin/env python3
"""Validate that the canonical skill is internally consistent.

Checks:
- skill/SKILL.md exists and parses cleanly.
- Every workflow file referenced from SKILL.md exists.
- Every schema file referenced from SKILL.md exists.
- Both skill wrappers (`.claude/skills/genealogy/SKILL.md` and
  `skills/genealogy/SKILL.md`) exist and have YAML frontmatter with
  `name` and `description`.
- The plugin manifest at `.claude-plugin/plugin.json` parses and has
  required fields.
- All `_scripts/*` paths mentioned in the skill resolve to real files.
- All `templates/*` paths mentioned in the skill resolve to real files.

Exits 0 on success, 1 on any failure. Used by CI and as a pre-commit
hook.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def read(path: Path) -> str | None:
    if not path.exists():
        err(f"missing: {path.relative_to(REPO)}")
        return None
    return path.read_text()


def check_frontmatter(path: Path, required_keys: set[str]) -> dict | None:
    text = read(path)
    if text is None:
        return None
    if not text.startswith("---\n"):
        err(f"{path.relative_to(REPO)}: no frontmatter")
        return None
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        err(f"{path.relative_to(REPO)}: malformed frontmatter")
        return None
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        err("PyYAML not installed — run `pip install pyyaml`")
        return None
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        err(f"{path.relative_to(REPO)}: YAML error: {e}")
        return None
    missing = required_keys - fm.keys()
    if missing:
        err(f"{path.relative_to(REPO)}: missing keys: {sorted(missing)}")
    return fm


def check_canonical_skill() -> None:
    skill_md = REPO / "skill" / "SKILL.md"
    text = read(skill_md)
    if text is None:
        return

    # Find every workflow/schema reference (both bare `workflows/foo.md` and
    # `skill/workflows/foo.md` forms).
    workflow_refs = set(re.findall(r"`(?:skill/)?workflows/([\w./-]+\.md)`", text))
    schema_refs = set(re.findall(r"`(?:skill/)?schemas/([\w./-]+\.md)`", text))

    for wf in workflow_refs:
        p = REPO / "skill" / "workflows" / wf
        if not p.exists():
            err(f"skill/SKILL.md references missing workflow: workflows/{wf}")

    for sc in schema_refs:
        p = REPO / "skill" / "schemas" / sc
        if not p.exists():
            err(f"skill/SKILL.md references missing schema: schemas/{sc}")

    # Check every workflows/*.md and schemas/*.md is referenced (no orphans)
    actual_workflows = {p.name for p in (REPO / "skill" / "workflows").glob("*.md")}
    actual_schemas = {p.name for p in (REPO / "skill" / "schemas").glob("*.md")}
    orphan_workflows = actual_workflows - workflow_refs
    orphan_schemas = actual_schemas - schema_refs
    for o in orphan_workflows:
        warn(f"workflows/{o} exists but isn't referenced from SKILL.md")
    for o in orphan_schemas:
        warn(f"schemas/{o} exists but isn't referenced from SKILL.md")

    # Check every `_scripts/...` and `templates/...` path in SKILL.md exists
    script_refs = set(re.findall(r"`(_scripts/[\w./-]+)`", text))
    template_refs = set(re.findall(r"`(templates/[\w./-]+)`", text))

    for r in script_refs:
        p = REPO / r
        if not p.exists():
            err(f"skill/SKILL.md references missing: {r}")
    for r in template_refs:
        p = REPO / r
        if not p.exists():
            err(f"skill/SKILL.md references missing: {r}")


def check_wrappers() -> None:
    for wrapper in [
        REPO / ".claude" / "skills" / "genealogy" / "SKILL.md",
        REPO / "skills" / "genealogy" / "SKILL.md",
    ]:
        check_frontmatter(wrapper, {"name", "description"})


def check_plugin_manifest() -> None:
    p = REPO / ".claude-plugin" / "plugin.json"
    text = read(p)
    if text is None:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        err(f"{p.relative_to(REPO)}: JSON error: {e}")
        return
    required = {"name", "description", "version", "author"}
    missing = required - data.keys()
    if missing:
        err(f"{p.relative_to(REPO)}: missing keys: {sorted(missing)}")
    # Cross-check version with VERSION file
    version_file = REPO / "VERSION"
    if version_file.exists():
        v = version_file.read_text().strip()
        if data.get("version") != v:
            err(f"plugin.json version ({data.get('version')}) != VERSION ({v})")


def check_workflows_have_no_agent_tool_references() -> None:
    """Workflows must reference scripts by shell command, not by agent tool name."""
    forbidden_tool_names = ["the Bash tool", "the Edit tool", "the Write tool", "the Read tool"]
    for wf in (REPO / "skill" / "workflows").glob("*.md"):
        text = wf.read_text()
        for forbidden in forbidden_tool_names:
            if forbidden in text:
                err(f"{wf.relative_to(REPO)}: contains agent-specific tool reference: '{forbidden}'")


def main() -> int:
    check_canonical_skill()
    check_wrappers()
    check_plugin_manifest()
    check_workflows_have_no_agent_tool_references()

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ! {w}")
        print()

    if errors:
        print("FAIL — skill validation errors:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print("OK — skill validates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
