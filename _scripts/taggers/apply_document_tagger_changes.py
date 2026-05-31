#!/usr/bin/env python3
"""
Apply the JSON diff exported by _tools/document-tagger.html.

Usage:
    python3 _scripts/apply_document_tagger_changes.py path/to/document-tagger-changes.json
    cat changes.json | python3 _scripts/apply_document_tagger_changes.py -

For each edit:
  1. Loads the sidecar (synthesizing minimal frontmatter if absent).
  2. For each list field (related_people, places, languages, topics):
     adds new values, removes deleted values. Lists are preserved when
     present; absent fields are created.
  3. Sets `date:` if changed.
  4. For each newly-added person, appends the sidecar to that person's
     `sources:` YAML list. For each newly-removed person, drops it.

YAML helpers are imported from apply_photo_tagger_changes.py for
consistency with how the photo tagger writes to disk.

Idempotent.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(VAULT / "_scripts" / "taggers"))

from apply_photo_tagger_changes import (  # noqa: E402
    split_frontmatter,
    join_frontmatter,
    parse_yaml_list_block,
    replace_yaml_list,
    person_file_for_wikilink,
)


LIST_FIELDS = ("related_people", "places", "languages", "topics")


def upsert_scalar(fm_lines: list[str], key: str, value: str) -> list[str]:
    """Set `key: \"value\"` in the frontmatter, replacing any existing line."""
    pat = re.compile(rf"^{re.escape(key)}\s*:")
    new_line = f'{key}: "{value}"\n'
    for i, line in enumerate(fm_lines):
        if pat.match(line):
            fm_lines[i] = new_line
            return fm_lines
    return fm_lines + [new_line]


def apply_edit(edit: dict) -> dict:
    sidecar_rel = edit.get("sidecar")
    if not sidecar_rel:
        raise SystemExit(f"edit missing sidecar: {edit.get('doc')}")
    sidecar = VAULT / sidecar_rel
    if not sidecar.exists():
        raise SystemExit(f"sidecar not found: {sidecar}")

    text = sidecar.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        fm = []

    summary: dict[str, dict] = {}
    person_diff = {"added": [], "removed": []}

    # places_field — the sidecar may already use `location:` instead of `places:`
    field_remap = {"places": edit.get("places_field") or "places"}

    for field in LIST_FIELDS:
        block = edit.get(field) or {"add": [], "remove": []}
        adds = list(block.get("add") or [])
        removes = list(block.get("remove") or [])
        if not adds and not removes:
            continue
        target_key = field_remap.get(field, field)
        current = parse_yaml_list_block(fm, target_key)
        new = list(current)
        for v in removes:
            if v in new:
                new.remove(v)
        for v in adds:
            if v not in new:
                new.append(v)
        if new != current:
            fm = replace_yaml_list(fm, target_key, new)
            summary[target_key] = {"added": adds, "removed": removes, "final_count": len(new)}
        if field == "related_people":
            person_diff["added"] = adds
            person_diff["removed"] = removes

    if "date" in edit and edit["date"] is not None:
        fm = upsert_scalar(fm, "date", edit["date"])
        summary["date"] = {"set": edit["date"]}

    if "ocr_confidence" in edit:
        val = edit["ocr_confidence"]
        if val:
            fm = upsert_scalar(fm, "ocr_confidence", val)
            summary["ocr_confidence"] = {"set": val}
        else:
            # Unset: remove the line entirely if present.
            fm = [line for line in fm
                  if not re.match(r"^ocr_confidence\s*:", line)]
            summary["ocr_confidence"] = {"set": "(unset)"}

    sidecar.write_text(join_frontmatter(fm, body), encoding="utf-8")

    # Person-side backlinks
    person_changes = []
    for wikilink in person_diff["added"]:
        if patch_person_sources(wikilink, sidecar_rel, add=True):
            person_changes.append(f"+ {wikilink}")
    for wikilink in person_diff["removed"]:
        if patch_person_sources(wikilink, sidecar_rel, add=False):
            person_changes.append(f"- {wikilink}")

    return {"sidecar": sidecar_rel, "changes": summary, "people": person_changes}


def patch_person_sources(wikilink: str, sidecar_rel: str, *, add: bool) -> bool:
    """Add or remove a sidecar wikilink from a person's `sources:` list.
    Returns True if the file was actually modified."""
    person_file = person_file_for_wikilink(wikilink)
    if not person_file:
        return False
    text = person_file.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return False

    sidecar_stem = Path(sidecar_rel).stem
    sidecar_link = f"[[{sidecar_stem}]]"
    current = parse_yaml_list_block(fm, "sources")
    new = list(current)
    if add:
        if sidecar_link in new:
            return False
        new.append(sidecar_link)
    else:
        if sidecar_link not in new:
            return False
        new.remove(sidecar_link)
    fm = replace_yaml_list(fm, "sources", new)
    person_file.write_text(join_frontmatter(fm, body), encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: apply_document_tagger_changes.py <changes.json|->", file=sys.stderr)
        return 2
    arg = sys.argv[1]
    raw = sys.stdin.read() if arg == "-" else Path(arg).read_text(encoding="utf-8")
    payload = json.loads(raw)
    edits = payload.get("edits") or []
    print(f"Applying {len(edits)} edits.")
    for edit in edits:
        result = apply_edit(edit)
        if not result["changes"] and not result["people"]:
            continue
        print(f"\n{result['sidecar']}")
        for key, info in result["changes"].items():
            if "set" in info:
                print(f"  {key}: set to {info['set']!r}")
            else:
                if info["added"]:
                    print(f"  {key} +: {', '.join(info['added'])}")
                if info["removed"]:
                    print(f"  {key} -: {', '.join(info['removed'])}")
        for change in result["people"]:
            print(f"  person backlink: {change}")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
