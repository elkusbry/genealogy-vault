#!/usr/bin/env python3
"""
Apply the JSON diff exported by _tools/photo-tagger.html.

Usage:
    python3 _scripts/apply_photo_tagger_changes.py path/to/photo-tagger-changes.json
    cat changes.json | python3 _scripts/apply_photo_tagger_changes.py -

What it does for each edit:
  1. Loads the sidecar markdown (creating one if `sidecar` is null).
  2. Reads the YAML frontmatter, updates the `related_people` (or whatever
     `tag_field` was) list: adds new wikilinks, removes deletions.
  3. Optionally writes the supplied caption into a `## Caption` section of
     the body (replacing any existing one).
  4. For every newly-added person, opens that person's people/*.md and
     ensures the photo is listed in their `photos:` YAML array — the
     bidirectional half of the tag.
  5. For every newly-removed person, drops that photo from their `photos:`
     array.

Idempotent. Safe to re-run with the same JSON.

Implementation notes:
- We do surgical line edits on the YAML rather than round-tripping with a
  YAML library, because the rest of the vault was hand-curated and we want
  to preserve formatting exactly (quoting style, comment lines, etc.).
- A change-summary is printed at the end so you can sanity-check before
  committing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Frontmatter helpers — line-surgical, preserves formatting.
# ---------------------------------------------------------------------------


def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    """Returns (frontmatter_lines, body) or (None, text) if no frontmatter."""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, text
    # find closing ---
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = lines[1:i]
            body = "".join(lines[i + 1:])
            return fm, body
    return None, text


def join_frontmatter(fm_lines: list[str], body: str) -> str:
    return "---\n" + "".join(fm_lines) + "---\n" + body


def find_yaml_list_block(fm: list[str], key: str) -> tuple[int, int] | None:
    """Return (start_idx, end_idx_exclusive) covering `key:` and its items.

    Recognizes both
        key:
          - item
          - item
    and
        key: []
    """
    key_pat = re.compile(rf"^{re.escape(key)}\s*:\s*(.*)$")
    for i, line in enumerate(fm):
        m = key_pat.match(line.rstrip("\n"))
        if not m:
            continue
        rest = m.group(1).strip()
        if rest and rest != "[]":
            # inline value — treat as a one-line block we'd need to convert.
            return (i, i + 1)
        # find end of items
        j = i + 1
        while j < len(fm) and (fm[j].startswith("  - ") or fm[j].startswith("\t- ")):
            j += 1
        return (i, j)
    return None


def parse_yaml_list_block(fm: list[str], key: str) -> list[str]:
    """Read existing list items for a key (returns [] if absent/empty)."""
    block = find_yaml_list_block(fm, key)
    if not block:
        return []
    start, end = block
    items: list[str] = []
    for line in fm[start + 1:end]:
        m = re.match(r"^\s*-\s*(.*)$", line)
        if not m:
            continue
        val = m.group(1).strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        items.append(val)
    return items


def render_yaml_list(key: str, values: list[str]) -> list[str]:
    if not values:
        return [f"{key}: []\n"]
    out = [f"{key}:\n"]
    for v in values:
        # wikilinks contain [[]] characters — YAML-safe when quoted with "..."
        # We quote everything for consistency with the rest of the vault.
        out.append(f'  - "{v}"\n')
    return out


def replace_yaml_list(fm: list[str], key: str, new_values: list[str]) -> list[str]:
    block = find_yaml_list_block(fm, key)
    new_block = render_yaml_list(key, new_values)
    if not block:
        # Insert near the end (before last line is fine — order doesn't matter)
        return fm + new_block
    start, end = block
    return fm[:start] + new_block + fm[end:]


# ---------------------------------------------------------------------------
# Sidecar / people patching
# ---------------------------------------------------------------------------


def make_new_sidecar(image_rel: str, photo_id: str) -> Path:
    """Create a minimal sidecar for an image that didn't have one.

    `image_rel` may arrive without an extension (the tagger uses sidecar
    stems as photo IDs). Resolve to the actual file on disk so the sidecar
    embed/wikilink carries the correct extension.
    """
    candidate = VAULT / image_rel
    # If the path has no extension or doesn't exist, search for a matching image.
    if candidate.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp"} or not candidate.exists():
        parent = candidate.parent if candidate.parent != Path(".") else VAULT
        if not parent.is_absolute():
            parent = VAULT / parent
        stem = candidate.stem
        found = None
        if parent.exists():
            for p in parent.iterdir():
                if p.is_file() and p.stem == stem and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                    found = p
                    break
        if found:
            candidate = found
    img = candidate
    base_stem = re.sub(r"-(front|back)$", "", img.stem)
    sidecar = img.with_name(base_stem + ".md")
    if sidecar.exists():
        return sidecar
    sidecar.write_text(
        "---\n"
        f'title: "{base_stem}"\n'
        f"type: photo\n"
        f"date: \"\"\n"
        f"related_people: []\n"
        f'source: "[[{img.name}]]"\n'
        f"tags:\n"
        f"  - media\n"
        f"  - media/photo\n"
        f"---\n\n"
        f"# {base_stem}\n\n"
        f"![[{img.name}]]\n",
        encoding="utf-8",
    )
    print(f"  created sidecar: {sidecar.relative_to(VAULT)}")
    return sidecar


def patch_sidecar(edit: dict) -> tuple[str, list[str], list[str]]:
    """Apply add/remove/caption to one sidecar. Returns (sidecar_path, final_tags, removed_tags)."""
    if edit.get("sidecar"):
        sidecar = VAULT / edit["sidecar"]
        if not sidecar.exists():
            # sidecar path got stale — fall back to creating new
            sidecar = make_new_sidecar(edit["photo"], edit.get("photo", ""))
    else:
        sidecar = make_new_sidecar(edit["photo"], edit.get("photo", ""))

    text = sidecar.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        # synthesize empty frontmatter
        fm = []

    tag_field = edit.get("tag_field") or "related_people"
    current = parse_yaml_list_block(fm, tag_field)
    final = list(current)
    for t in edit.get("remove", []):
        if t in final:
            final.remove(t)
    for t in edit.get("add", []):
        if t not in final:
            final.append(t)

    fm = replace_yaml_list(fm, tag_field, final)

    # caption handling — write to a "## Caption" section if non-empty
    caption = edit.get("caption")
    if caption:
        body = upsert_caption_section(body, caption)

    sidecar.write_text(join_frontmatter(fm, body), encoding="utf-8")
    return str(sidecar.relative_to(VAULT)), final, list(edit.get("remove", []))


CAPTION_HEAD = "## Caption"


def upsert_caption_section(body: str, caption: str) -> str:
    """Replace existing ## Caption section (until next ## or EOF) or append one."""
    pat = re.compile(r"^##\s+Caption\s*$.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
    new_section = f"{CAPTION_HEAD}\n\n{caption.strip()}\n\n"
    if pat.search(body):
        return pat.sub(new_section, body)
    # append
    sep = "" if body.endswith("\n") else "\n"
    return body + sep + "\n" + new_section


# ---------------------------------------------------------------------------
# People backlinks
# ---------------------------------------------------------------------------


def person_file_for_wikilink(wikilink: str) -> Path | None:
    """[[Firstname Lastname (YYYY)]] -> people/Firstname Lastname (YYYY).md"""
    m = re.match(r"^\[\[([^\]]+)\]\]$", wikilink.strip())
    if not m:
        return None
    name = m.group(1)
    candidate = VAULT / "people" / f"{name}.md"
    return candidate if candidate.exists() else None


def patch_person_photos(person_file: Path, photo_wikilink: str, add: bool) -> bool:
    """Ensure photo_wikilink is present/absent from person's photos: list.
    Returns True if file changed.
    """
    text = person_file.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return False
    current = parse_yaml_list_block(fm, "photos")
    changed = False
    if add and photo_wikilink not in current:
        current.append(photo_wikilink)
        changed = True
    elif not add and photo_wikilink in current:
        current.remove(photo_wikilink)
        changed = True
    if not changed:
        return False
    fm = replace_yaml_list(fm, "photos", current)
    person_file.write_text(join_frontmatter(fm, body), encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def set_date_yaml(sidecar: Path, date_str: str) -> bool:
    """Write date: "YYYY[-MM[-DD]]" to YAML. Empty string clears it."""
    if not sidecar.exists():
        return False
    text = sidecar.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return False
    fm_str = "".join(fm) if isinstance(fm, list) else fm
    pat = re.compile(r"^date\s*:.*$", re.MULTILINE)
    new_line = f'date: "{date_str}"' if date_str else 'date: ""'
    if pat.search(fm_str):
        new_fm = pat.sub(new_line, fm_str, count=1)
    else:
        if not fm_str.endswith("\n"):
            fm_str += "\n"
        new_fm = fm_str + new_line + "\n"
    new_fm_lines = new_fm.splitlines(keepends=True)
    sidecar.write_text(join_frontmatter(new_fm_lines, body), encoding="utf-8")
    print(f"  📅 {sidecar.name}: date = {date_str or '(cleared)'}")
    return True


def rotate_fraction(fx: float, fy: float, degrees: int) -> tuple[float, float]:
    """Apply rotation to a fractional marker coord. Returns (new_fx, new_fy)
    in the rotated image's natural frame."""
    d = degrees % 360
    if d == 0:    return fx, fy
    if d == 90:   return (1 - fy, fx)
    if d == 180:  return (1 - fx, 1 - fy)
    if d == 270:  return (fy, 1 - fx)
    return fx, fy


def rotate_image_file(image_path: Path, degrees: int) -> bool:
    """Rotate JPG in place by `degrees` (CW). Returns True if rotated."""
    if not degrees:
        return False
    try:
        from PIL import Image
    except ImportError:
        print(f"  ! Pillow not installed — skipping rotation of {image_path}")
        return False
    if not image_path.exists():
        print(f"  ! image not found: {image_path}")
        return False
    img = Image.open(image_path)
    # PIL rotate is CCW; UI / CSS rotate is CW — invert sign.
    rotated = img.rotate(-degrees, expand=True)
    rotated.save(image_path, quality=95)
    print(f"  ↻ rotated {image_path.relative_to(VAULT)} by {degrees}° (file baked in)")
    return True


def remap_face_tags_after_rotation(sidecar: Path, front_deg: int, back_deg: int) -> None:
    """Read face_tags from sidecar, remap by the rotation applied to each face,
    write back. No-op if no markers or no rotation."""
    if not front_deg and not back_deg:
        return
    if not sidecar.exists():
        return
    text = sidecar.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        return
    markers = read_face_tags_block(fm)
    if not markers:
        return
    for m in markers:
        face = m.get("face", "front")
        deg = front_deg if face == "front" else back_deg
        if not deg:
            continue
        fx, fy = float(m.get("x", 0)), float(m.get("y", 0))
        nx, ny = rotate_fraction(fx, fy, deg)
        m["x"], m["y"] = round(nx, 4), round(ny, 4)
    fm = write_face_tags_block(fm, markers)
    sidecar.write_text(join_frontmatter(fm, body), encoding="utf-8")
    print(f"  📍 remapped {len(markers)} marker(s) for rotation")


def upsert_face_tags(sidecar_path: Path, markers_add: list[dict],
                     markers_remove: list[int]) -> None:
    """Write face_tags YAML list to the sidecar.

    `markers_remove` are zero-based indexes into the EXISTING (pre-edit)
    face_tags list. `markers_add` is a list of {person, x, y, face} dicts.
    """
    if not markers_add and not markers_remove:
        return
    text = sidecar_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        fm = []
    existing = read_face_tags_block(fm)
    # apply removes
    kept = [m for i, m in enumerate(existing) if i not in set(markers_remove)]
    # apply adds
    for m in markers_add:
        kept.append({
            "person": m.get("person", ""),
            "x": round(float(m.get("x", 0)), 4),
            "y": round(float(m.get("y", 0)), 4),
            "face": m.get("face", "front"),
        })
    fm = write_face_tags_block(fm, kept)
    sidecar_path.write_text(join_frontmatter(fm, body), encoding="utf-8")


def read_face_tags_block(fm: list[str]) -> list[dict]:
    """Parse the face_tags: YAML list of dicts (line-by-line)."""
    out = []
    i = 0
    while i < len(fm):
        line = fm[i].rstrip("\n")
        if re.match(r"^face_tags\s*:\s*(\[\])?\s*$", line):
            i += 1
            while i < len(fm) and fm[i].startswith("  -"):
                # collect lines belonging to this dict
                entry = {}
                # first line is `  - key: value`
                m = re.match(r"^  -\s+(\w+)\s*:\s*(.*)$", fm[i].rstrip("\n"))
                if m:
                    entry[m.group(1)] = m.group(2).strip().strip('"')
                i += 1
                while i < len(fm) and fm[i].startswith("    "):
                    mm = re.match(r"^    (\w+)\s*:\s*(.*)$", fm[i].rstrip("\n"))
                    if mm:
                        entry[mm.group(1)] = mm.group(2).strip().strip('"')
                    i += 1
                # coerce numeric fields
                for k in ("x", "y"):
                    if k in entry:
                        try: entry[k] = float(entry[k])
                        except ValueError: pass
                out.append(entry)
            return out
        i += 1
    return out


def write_face_tags_block(fm: list[str], entries: list[dict]) -> list[str]:
    """Rewrite the face_tags block in-place (replace existing or append)."""
    # find existing block range
    start = None
    end = len(fm)
    for i, line in enumerate(fm):
        if re.match(r"^face_tags\s*:", line):
            start = i
            j = i + 1
            while j < len(fm) and (fm[j].startswith("  -") or fm[j].startswith("    ")):
                j += 1
            end = j
            break
    new_lines = ["face_tags:\n"] if entries else ["face_tags: []\n"]
    for e in entries:
        new_lines.append(f'  - person: "{e.get("person","")}"\n')
        new_lines.append(f'    x: {e.get("x",0)}\n')
        new_lines.append(f'    y: {e.get("y",0)}\n')
        new_lines.append(f'    face: {e.get("face","front")}\n')
    if start is None:
        return fm + new_lines
    return fm[:start] + new_lines + fm[end:]


def apply(payload: dict) -> None:
    schema = payload.get("schema", "")
    if not schema.startswith("photo-tagger/"):
        print(f"warning: unexpected schema {schema!r}", file=sys.stderr)
    edits = payload.get("edits", [])
    if not edits:
        print("(no edits in payload)")
        return
    print(f"Applying {len(edits)} edit(s)…")
    for edit in edits:
        photo = edit.get("photo", "?")
        added = edit.get("add", [])
        removed = edit.get("remove", [])
        print(f"\n• {photo}")
        sidecar, final, _ = patch_sidecar(edit)
        print(f"  sidecar: {sidecar}")
        if added or removed:
            print(f"  + add:    {added or '—'}")
            print(f"  - remove: {removed or '—'}")
        if edit.get("caption"):
            print(f"  ✎ caption updated ({len(edit['caption'])} chars)")

        # Rotation — bake into the JPG file via PIL and remap any face_tags
        # markers using the rotation transform. No YAML metadata is written.
        sidecar_obj = VAULT / sidecar
        # Detect back stub redirection (the user might be looking at a back
        # image which lives in a separate stub sidecar after a fragment merge).
        redirect_target: Path | None = None
        is_back_redirect = False
        try:
            t = sidecar_obj.read_text(encoding="utf-8")
            mm = re.search(r'^merged_into:\s*"?\[\[([^\]]+)\]\]', t, re.MULTILINE)
            if mm:
                parent_stem = mm.group(1)
                redirect_target = sidecar_obj.parent / f"{parent_stem}.md"
                is_back_redirect = True
        except FileNotFoundError:
            pass

        # Figure out which image file is the front and which is the back.
        if redirect_target and redirect_target.exists():
            target_sidecar = redirect_target
            ptext = target_sidecar.read_text(encoding="utf-8")
        else:
            target_sidecar = sidecar_obj
            ptext = target_sidecar.read_text(encoding="utf-8") if target_sidecar.exists() else ""
        src_m = re.search(r'^source\s*:\s*"?\[\[([^\]]+)\]\]', ptext, re.MULTILINE)
        srcback_m = re.search(r'^source_back\s*:\s*"?\[\[([^\]]+)\]\]', ptext, re.MULTILINE)
        front_img = target_sidecar.parent / src_m.group(1) if src_m else None
        back_img = target_sidecar.parent / srcback_m.group(1) if srcback_m else None
        # Fallback: derive image path from sidecar stem with .jpg
        if not front_img or not front_img.exists():
            cand = target_sidecar.with_suffix(".jpg")
            if cand.exists(): front_img = cand

        rot_front = int(edit["rotation"]) if edit.get("rotation") else 0
        rot_back = int(edit["rotation_back"]) if edit.get("rotation_back") else 0

        # When this edit came in via a back-stub, the payload's `rotation` is
        # actually for the back face of the parent.
        if is_back_redirect and rot_front:
            rot_back = rot_front
            rot_front = 0

        # IMPORTANT: remap existing markers FIRST (using the OLD natural frame),
        # THEN rotate the file, THEN write any newly-added markers from this
        # payload (which were captured in the OLD natural frame too, so they
        # also need remapping).
        if rot_front or rot_back:
            # Remap existing markers in YAML
            remap_face_tags_after_rotation(target_sidecar, rot_front, rot_back)
            # Rotate physical files
            if rot_front and front_img:
                rotate_image_file(front_img, rot_front)
            if rot_back and back_img:
                rotate_image_file(back_img, rot_back)

        # Date — write to YAML `date:` scalar
        if edit.get("date") is not None:
            set_date_yaml(sidecar_obj, edit["date"])

        # Markers — add to face_tags YAML. If a rotation was applied in this
        # same edit, new markers were captured in the OLD natural frame, so
        # remap them via the rotation transform before saving.
        markers_add = edit.get("markers_add", []) or []
        markers_remove = edit.get("markers_remove", []) or []
        if (rot_front or rot_back) and markers_add:
            remapped = []
            for m in markers_add:
                face = m.get("face", "front")
                deg = rot_front if face == "front" else rot_back
                if deg:
                    fx, fy = float(m.get("x", 0)), float(m.get("y", 0))
                    nx, ny = rotate_fraction(fx, fy, deg)
                    m = {**m, "x": round(nx, 4), "y": round(ny, 4)}
                remapped.append(m)
            markers_add = remapped
        if markers_add or markers_remove:
            upsert_face_tags(sidecar_obj, markers_add, markers_remove)
            print(f"  📍 markers: +{len(markers_add)} -{len(markers_remove)}")
            # Also tag the people in related_people if not already there
            for m in markers_add:
                p = m.get("person")
                if not p: continue
                if p not in final:
                    final.append(p)
                    added = added + [p] if p not in added else added

        # bidirectional photos: array
        photo_wikilink = f"[[{Path(edit['photo']).name}.jpg]]" if not edit['photo'].lower().endswith((".jpg",".jpeg",".png",".webp",".gif")) else f"[[{Path(edit['photo']).name}]]"
        all_added = list(added)
        for m in markers_add:
            if m.get("person") and m["person"] not in all_added:
                all_added.append(m["person"])
        for wl in all_added:
            person_file = person_file_for_wikilink(wl)
            if not person_file:
                print(f"  ! person not found: {wl}")
                continue
            if patch_person_photos(person_file, photo_wikilink, add=True):
                print(f"  ↳ {wl} photos:+ {photo_wikilink}")
        for wl in removed:
            person_file = person_file_for_wikilink(wl)
            if not person_file:
                continue
            if patch_person_photos(person_file, photo_wikilink, add=False):
                print(f"  ↳ {wl} photos:- {photo_wikilink}")

        # Re-write final tags into sidecar (in case markers added new people)
        if markers_add:
            text = sidecar_obj.read_text(encoding="utf-8")
            fm2, body2 = split_frontmatter(text)
            if fm2 is not None:
                tag_field = edit.get("tag_field") or "related_people"
                fm2 = replace_yaml_list(fm2, tag_field, final)
                sidecar_obj.write_text(join_frontmatter(fm2, body2), encoding="utf-8")

    print("\nDone.")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = argv[1]
    if src == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(src).read_text(encoding="utf-8")
    payload = json.loads(raw)
    apply(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
