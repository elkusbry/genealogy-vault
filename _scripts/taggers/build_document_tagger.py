#!/usr/bin/env python3
"""
Build _tools/document-tagger.html — standalone tri-pane viewer for tagging
non-photo documents in sources/.

Layout:
  [ doc list ] | [ main document ] | [ tabs: Translation / Notes / Metadata ]

Metadata tab edits: related_people, places, languages, topics, date.

Pairings are read from explicit YAML keys (translation:, notes:,
transcription:, content:) on the base sidecar. Run
_scripts/suggest_doc_pairings.py first to backfill.

Photo-tagger types are excluded (photo/tombstone/portrait/handwritten-fragment)
plus blank-scan, plus the sibling files themselves (-translation, -notes,
-transcription, -content).

Usage:
    python3 _scripts/build_document_tagger.py

Then open _tools/document-tagger.html in your browser.

Exported edits land as _tools/document-tagger-changes-*.json — feed them
through _scripts/apply_document_tagger_changes.py to write back to disk.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

VAULT = Path(__file__).resolve().parent.parent.parent
SOURCES = VAULT / "sources"
PEOPLE = VAULT / "people"
OUTPUT = VAULT / "_tools" / "document-tagger.html"

# Types handled by the photo tagger — skip here so the two tools don't overlap.
PHOTO_TYPES = {"photo", "tombstone", "portrait", "handwritten-fragment"}
# Other types to skip entirely (not interesting to tag).
SKIP_TYPES = {"blank-scan"}
# Synthesis / research documents — these wrap or comment on primary sources
# rather than being primary sources themselves.  They're filtered out of the
# default doc list and shown in a "Sidecars" right-pane tab on docs they
# reference.
SIDECAR_TYPES = {
    "research", "genealogy-notes", "memoir",
    "family-group-sheet", "historical-context",
}

# Sibling suffixes that mean "this .md is content-for-another-sidecar".
SIBLING_SUFFIXES = ("-translation", "-english-translation", "-notes",
                    "-transcription", "-content")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
PDF_EXTS = {".pdf"}

TOPIC_SEED = [
    "banking-finance", "immigration-travel", "vital-records", "military",
    "correspondence-personal", "religious", "business-employment",
    "property-legal", "education", "holocaust-persecution",
    "news-obituary", "research-notes",
]
LANGUAGE_SEED = [
    "Polish", "Russian", "Yiddish", "Hebrew", "German", "English",
    "Norwegian", "Lithuanian", "French", "Latin",
]


def parse_frontmatter(md_path: Path) -> tuple[dict, str]:
    """Tiny YAML-frontmatter reader (same shape as build_photo_tagger.py).

    Returns (frontmatter_dict, body_text). body_text is the markdown content
    after the closing ---. If there's no frontmatter, returns ({}, full_text).
    """
    if not md_path.exists():
        return {}, ""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm_text = text[3:end].lstrip("\n")
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]

    data: dict = {}
    current_list: list | None = None
    for raw in fm_text.splitlines():
        line = raw.rstrip()
        if not line:
            current_list = None
            continue
        if (line.startswith("  - ") or line.startswith(" - ")) and current_list is not None:
            val = line.split("- ", 1)[1].strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            current_list.append(val)
            continue
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$", line)
        if not m:
            current_list = None
            continue
        key, val = m.group(1), m.group(2).strip()
        current_list = None
        if val == "" or val == "[]":
            if val == "[]":
                data[key] = []
                current_list = None
            else:
                data[key] = []
                current_list = data[key]
        else:
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            data[key] = val
    return data, body


def strip_wikilink(s: str) -> str:
    """[[Foo.md]] -> Foo.md ; [[Foo|Bar]] -> Foo ; otherwise return as-is."""
    if not s:
        return ""
    m = re.match(r"^\[\[([^\]|]+)(?:\|[^\]]*)?\]\]$", s.strip())
    if m:
        return m.group(1).strip()
    return s.strip()


def list_field(fm: dict, key: str) -> list[str]:
    v = fm.get(key)
    if isinstance(v, list):
        return [s for s in v if isinstance(s, str)]
    if isinstance(v, str) and v:
        return [v]
    return []


def is_sibling_stem(stem: str) -> bool:
    return any(stem.endswith(suf) for suf in SIBLING_SUFFIXES)


def find_main_doc(stem: str, sidecar_body: str, content_ref: str | None) -> dict:
    """Return {kind, src, name} for the doc to show in the center pane.

    Resolution order:
      1. <stem>.pdf
      2. <stem>.jpg / .jpeg / .png / .gif / .webp
      3. content_ref (resolved file) if present
      4. sidecar markdown body (if non-empty)
      5. None
    """
    # PDF
    for ext in PDF_EXTS:
        p = SOURCES / f"{stem}{ext}"
        if p.exists():
            return {"kind": "pdf", "src": f"../sources/{quote(p.name)}", "name": p.name}
    # Image
    for ext in IMAGE_EXTS:
        p = SOURCES / f"{stem}{ext}"
        if p.exists():
            return {"kind": "image", "src": f"../sources/{quote(p.name)}", "name": p.name}
    # Explicit content file reference (from `content:` YAML)
    if content_ref:
        target = SOURCES / strip_wikilink(content_ref)
        if target.exists():
            if target.suffix.lower() in PDF_EXTS:
                return {"kind": "pdf", "src": f"../sources/{quote(target.name)}", "name": target.name}
            if target.suffix.lower() in IMAGE_EXTS:
                return {"kind": "image", "src": f"../sources/{quote(target.name)}", "name": target.name}
            if target.suffix.lower() == ".md":
                return {"kind": "markdown", "src": f"../sources/{quote(target.name)}",
                        "name": target.name,
                        "text": parse_frontmatter(target)[1] or target.read_text(encoding="utf-8", errors="replace")}
    # Sidecar body
    if sidecar_body and sidecar_body.strip():
        return {"kind": "markdown", "src": None, "name": None, "text": sidecar_body}
    return {"kind": "none", "src": None, "name": None}


def load_paired_text(ref: str | None) -> dict | None:
    """For a YAML key like translation: \"[[foo.md]]\", load the file and
    return {name, text} (markdown text, body only). Returns None if the
    file is missing or not text-renderable."""
    if not ref:
        return None
    name = strip_wikilink(ref)
    if not name:
        return None
    p = SOURCES / name
    if not p.exists():
        return None
    if p.suffix.lower() == ".md":
        _, body = parse_frontmatter(p)
        return {"name": name, "text": body or p.read_text(encoding="utf-8", errors="replace")}
    if p.suffix.lower() in PDF_EXTS:
        return {"name": name, "text": None, "src": f"../sources/{quote(name)}", "kind": "pdf"}
    if p.suffix.lower() in IMAGE_EXTS:
        return {"name": name, "text": None, "src": f"../sources/{quote(name)}", "kind": "image"}
    # Unknown — fall back to filename only
    return {"name": name, "text": "(unsupported file type — open externally)"}


_CLEANED_HEADER_RE = re.compile(r"^##\s+Cleaned\s+Text\b.*$", re.MULTILINE)
_PLACEHOLDER_LINE_RE = re.compile(r"^\s*>?\s*\[[^\]]*\]\s*$")


def cleaned_text_status(body: str) -> str:
    """Classify the '## Cleaned Text' section in a sidecar body.

    Returns one of:
      - 'has-text'    section exists with substantive content (>40 non-placeholder chars)
      - 'placeholder' section exists, content is bracketed placeholder only / whitespace
      - 'missing'     no '## Cleaned Text' section at all
    """
    if not body:
        return "missing"
    m = _CLEANED_HEADER_RE.search(body)
    if not m:
        return "missing"
    rest = body[m.end():]
    # Stop at the next ## section heading
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    section = rest[: nxt.start()] if nxt else rest

    substantive_chars = 0
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _PLACEHOLDER_LINE_RE.match(stripped):
            continue
        # Strip leading '> ' (blockquote) for fairness, then count chars
        cleaned = re.sub(r"^>\s?", "", stripped)
        # Drop residual bracketed inline content
        cleaned = re.sub(r"\[[^\]]*\]", "", cleaned).strip()
        substantive_chars += len(cleaned)
    return "has-text" if substantive_chars > 40 else "placeholder"


def extract_cleaned_text(body: str) -> str:
    """Return the body of the '## Cleaned Text...' section of a sidecar.

    Slices from just after the heading line to the next '## ' heading (or EOF).
    Returns '' if no section exists. The returned string keeps blockquote
    markers ('> ') and other markdown intact so the renderer can format it.
    """
    if not body:
        return ""
    m = _CLEANED_HEADER_RE.search(body)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    section = rest[: nxt.start()] if nxt else rest
    return section.strip("\n")


def collect_docs() -> list[dict]:
    docs: list[dict] = []
    for sidecar in sorted(SOURCES.glob("*.md")):
        stem = sidecar.stem
        if is_sibling_stem(stem):
            continue
        fm, body = parse_frontmatter(sidecar)
        doc_type = (fm.get("type") or "").strip().lower()
        if doc_type in PHOTO_TYPES or doc_type in SKIP_TYPES:
            continue

        main = find_main_doc(stem, body, fm.get("content"))
        translation = load_paired_text(fm.get("translation"))
        notes = load_paired_text(fm.get("notes"))
        transcription = load_paired_text(fm.get("transcription"))

        # If there's truly nothing to show — no main doc, no body, no
        # translation/notes — skip it; nothing to tag.
        if main["kind"] == "none" and not translation and not notes:
            continue

        doc_type_norm = doc_type
        is_synthesis = doc_type_norm in SIDECAR_TYPES
        # Capture body text for the synthesis docs — they'll be rendered in
        # the Sidecars tab of their referenced primary docs.
        body_text = body if is_synthesis else None
        # Full raw .md text so the UI can show the sidecar source in a tab.
        try:
            sidecar_raw = sidecar.read_text(encoding="utf-8", errors="replace")
        except OSError:
            sidecar_raw = ""
        # Source field can point at a primary doc (a wikilink). Some sidecars
        # have `source:` as a list of multiple primaries — take all of them.
        source_field = fm.get("source")
        source_stems: list[str] = []
        if isinstance(source_field, str) and source_field:
            stem_only = Path(strip_wikilink(source_field)).stem
            if stem_only:
                source_stems.append(stem_only)
        elif isinstance(source_field, list):
            for entry in source_field:
                if not isinstance(entry, str):
                    continue
                stem_only = Path(strip_wikilink(entry)).stem
                if stem_only:
                    source_stems.append(stem_only)

        docs.append({
            "id": stem,
            "title": fm.get("title", stem) or stem,
            "sidecar": sidecar.relative_to(VAULT).as_posix(),
            "type": fm.get("type", ""),
            "date": fm.get("date") or "",
            "main": main,
            "translation": translation,
            "notes": notes,
            "transcription": transcription,
            "related_people": list_field(fm, "related_people"),
            "places": list_field(fm, "places") or list_field(fm, "location"),
            "languages": list_field(fm, "languages"),
            "topics": list_field(fm, "topics"),
            "is_synthesis": is_synthesis,
            "body_text": body_text,
            "sidecar_raw": sidecar_raw,
            "cleaned_text_status": cleaned_text_status(body),
            "cleaned_text": "" if is_synthesis else extract_cleaned_text(body),
            "source_stems": source_stems,
            "ocr_confidence": (fm.get("ocr_confidence") or "").strip().lower(),
            # Bookkeeping for apply step
            "places_field": "places" if fm.get("places") is not None else (
                "location" if fm.get("location") is not None else "places"),
        })
    docs.sort(key=lambda d: d["title"].lower())

    # Compute back-references: for each primary doc, which synthesis docs
    # reference it (via `source:` YAML or any [[wikilink]]/![[embed]] in body).
    primary_stems = {d["id"] for d in docs if not d["is_synthesis"]}
    # also accept the stem-with-extension (e.g. "foo.pdf") since some references use that form
    # We'll match by stripping extension on lookup.
    wikilink_re = re.compile(r"!?\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]")
    backrefs: dict[str, list[str]] = {p: [] for p in primary_stems}
    for d in docs:
        if not d["is_synthesis"]:
            continue
        targets: set[str] = set()
        for s in d["source_stems"]:
            if s in primary_stems:
                targets.add(s)
        for m in wikilink_re.finditer(d["body_text"] or ""):
            ref = m.group(1).strip()
            stem = Path(ref).stem
            if stem in primary_stems and stem != d["id"]:
                targets.add(stem)
        for t in targets:
            backrefs[t].append(d["id"])

    # Attach a `referenced_by` list of synthesis IDs to each primary doc.
    for d in docs:
        if d["is_synthesis"]:
            d["referenced_by"] = []
        else:
            d["referenced_by"] = sorted(set(backrefs.get(d["id"], [])))

    # --- Related-doc computation ---------------------------------------------
    # (a) Stem-cluster: docs whose base stem (with -translation/-notes/etc.
    #     stripped from either side) matches the current doc's base stem.
    # (b) Shares-people: other docs sharing at least one related_people wikilink.
    suffix_re = re.compile(
        r"(?:-(?:english-translation|translation|notes|transcription|content|polish-original|"
        r"russian-original|english|polish|russian|german|yiddish|hebrew|jewishgen-index|"
        r"abstract|extract|highlighted|original))+$"
    )

    def base_stem(stem: str) -> str:
        b = suffix_re.sub("", stem)
        return b or stem

    by_base: dict[str, list[str]] = {}
    for d in docs:
        by_base.setdefault(base_stem(d["id"]), []).append(d["id"])

    # Inverted index: person-wikilink -> [doc_id, ...]
    person_to_docs: dict[str, list[str]] = {}
    for d in docs:
        for raw in d.get("related_people", []):
            person_to_docs.setdefault(raw.strip(), []).append(d["id"])

    paired_tab_ids: dict[str, set[str]] = {}
    for d in docs:
        excluded: set[str] = set()
        for blob_key in ("translation", "notes", "transcription"):
            blob = d.get(blob_key)
            if blob and blob.get("name"):
                excluded.add(Path(blob["name"]).stem)
        paired_tab_ids[d["id"]] = excluded

    for d in docs:
        # Cluster siblings
        cluster = []
        for other_id in by_base.get(base_stem(d["id"]), []):
            if other_id == d["id"]:
                continue
            if other_id in paired_tab_ids[d["id"]]:
                continue  # already shown in Translation/Notes/Transcription
            cluster.append(other_id)
        cluster.sort()

        # Shares-people: count co-occurrences excluding self/cluster/paired
        already_shown = set(cluster) | paired_tab_ids[d["id"]] | {d["id"]}
        already_shown |= set(d.get("referenced_by") or [])
        counts: dict[str, int] = {}
        for raw in d.get("related_people", []):
            for other_id in person_to_docs.get(raw.strip(), []):
                if other_id in already_shown:
                    continue
                counts[other_id] = counts.get(other_id, 0) + 1
        # Rank by overlap descending, take top 25
        shared = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:25]

        d["related_cluster"] = cluster
        d["related_by_people"] = [
            {"id": oid, "overlap": n} for oid, n in shared
        ]

    return docs


def collect_people() -> list[str]:
    if not PEOPLE.exists():
        return []
    return [f"[[{p.stem}]]" for p in sorted(PEOPLE.iterdir()) if p.suffix.lower() == ".md"]


def collect_people_branches() -> dict[str, str]:
    """Map person-stem -> normalized branch string. Empty / missing -> 'Unknown'."""
    out: dict[str, str] = {}
    if not PEOPLE.exists():
        return out
    branch_re = re.compile(r'^branch\s*:\s*"?([^"\n]*?)"?\s*$', re.MULTILINE)
    for p in sorted(PEOPLE.iterdir()):
        if p.suffix.lower() != ".md":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        # Only scan inside frontmatter
        if not text.startswith("---"):
            out[p.stem] = "Unknown"
            continue
        end = text.find("\n---", 3)
        if end < 0:
            out[p.stem] = "Unknown"
            continue
        m = branch_re.search(text[3:end])
        if not m:
            out[p.stem] = "Unknown"
            continue
        branch = m.group(1).strip()
        if not branch:
            branch = "Unknown"
        out[p.stem] = branch
    return out


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Document Tagger</title>
<style>
  :root {
    --bg: #0f1115;
    --panel: #181b22;
    --panel2: #20242d;
    --panel3: #262b36;
    --border: #2a2f3a;
    --text: #e8eaed;
    --muted: #9aa3b2;
    --accent: #7aa2ff;
    --accent2: #ffd479;
    --danger: #ff6b6b;
    --chip-bg: #2a3145;
    --chip-text: #cfd6ea;
    --added: #1f3a2a;
    --removed: #3a1f1f;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100%; background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13.5px;
  }
  header {
    display: flex; align-items: center; gap: 12px; padding: 9px 14px;
    background: var(--panel); border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 50;
  }
  header h1 { font-size: 14.5px; margin: 0; font-weight: 600; }
  header .meta { color: var(--muted); font-size: 12px; }
  header .spacer { flex: 1; }
  header button {
    background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 6px 10px; font-size: 12.5px; cursor: pointer;
  }
  header button:hover { border-color: var(--accent); }
  header button.primary { background: var(--accent); color: #0b1020; border-color: var(--accent); font-weight: 600; }
  header .pending-badge {
    background: var(--accent2); color: #1a1300;
    border-radius: 999px; padding: 2px 8px; font-size: 12px; font-weight: 700;
  }
  main {
    display: grid;
    grid-template-columns: 320px 1fr 420px;
    height: calc(100vh - 47px);
    min-height: 0;
  }
  /* --- Doc list column --- */
  aside.list {
    background: var(--panel); border-right: 1px solid var(--border);
    overflow-y: auto; padding: 8px;
    min-width: 0;
  }
  aside.list .search {
    width: 100%; padding: 7px 10px; margin-bottom: 8px;
    background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px;
  }
  aside.list .view-toggle {
    display: flex; margin-bottom: 8px;
    border: 1px solid var(--border); border-radius: 6px; overflow: hidden;
  }
  aside.list .view-toggle button {
    flex: 1; padding: 6px 8px; background: var(--panel2);
    color: var(--muted); border: 0; cursor: pointer;
    font-size: 11.5px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.04em;
    border-right: 1px solid var(--border);
  }
  aside.list .view-toggle button:last-child { border-right: 0; }
  aside.list .view-toggle button.on { background: var(--accent); color: #0b1020; }
  aside.list .view-toggle button .n { font-weight: 500; opacity: 0.7; margin-left: 3px; }
  aside.list .filter-row {
    display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap;
  }
  aside.list .filter-row button {
    background: var(--panel2); color: var(--muted);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 3px 9px; font-size: 11.5px; cursor: pointer;
  }
  aside.list .filter-row button.on { background: var(--accent); color: #0b1020; border-color: var(--accent); }
  aside.list .type-section {
    margin-bottom: 8px; border: 1px solid var(--border); border-radius: 6px;
    background: var(--panel2); overflow: hidden;
  }
  aside.list .type-toggle {
    width: 100%; display: flex; align-items: center; justify-content: space-between;
    background: transparent; color: var(--text); border: 0;
    padding: 6px 10px; font-size: 11.5px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
  }
  aside.list .type-toggle:hover { color: var(--accent); }
  aside.list .type-toggle .caret { color: var(--muted); font-size: 10px; }
  aside.list .type-toggle .count {
    color: var(--muted); font-weight: 500; text-transform: none; letter-spacing: 0;
    font-size: 11px;
  }
  aside.list .type-toggle .count.active { color: var(--accent2); font-weight: 700; }
  aside.list .type-chips {
    display: none; flex-wrap: wrap; gap: 4px;
    padding: 6px 8px 8px; max-height: 240px; overflow-y: auto;
    border-top: 1px solid var(--border);
  }
  aside.list .type-chips.show { display: flex; }
  aside.list .type-chips button {
    background: var(--panel3); color: var(--muted);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 2px 8px; font-size: 11px; cursor: pointer;
    display: inline-flex; gap: 4px; align-items: center;
  }
  aside.list .type-chips button:hover { color: var(--text); border-color: var(--accent); }
  aside.list .type-chips button.on { background: var(--accent); color: #0b1020; border-color: var(--accent); }
  aside.list .type-chips button .n {
    background: rgba(0,0,0,0.18); border-radius: 999px;
    padding: 0 5px; font-size: 10px;
  }
  aside.list .type-chips button.on .n { background: rgba(0,0,0,0.25); }
  aside.list .type-chips .clear {
    background: transparent; color: var(--muted); border: 1px dashed var(--border);
  }
  aside.list .type-chips .clear:hover { color: var(--danger); border-color: var(--danger); }
  .doc-row {
    padding: 8px 10px; border-radius: 6px;
    cursor: pointer; margin-bottom: 3px;
    border: 1px solid transparent;
  }
  .doc-row:hover { background: var(--panel2); }
  .doc-row.active { background: var(--panel2); border-color: var(--accent); }
  .doc-row .t { font-size: 12.5px; line-height: 1.35; word-break: break-word; }
  .doc-row .sub { color: var(--muted); font-size: 11px; margin-top: 3px; }
  .doc-row .badges { margin-top: 4px; display: flex; gap: 3px; flex-wrap: wrap; }
  .doc-row .badge {
    display: inline-block; padding: 1px 6px; border-radius: 999px;
    background: var(--chip-bg); color: var(--chip-text); font-size: 10px;
  }
  .doc-row .badge.dirty { background: var(--accent2); color: #1a1300; }
  .doc-row .badge.pair { background: #3a2f5a; color: #d8c5ff; }
  .doc-row .badge.untagged { background: #4a2a2a; color: #ffb3b3; }
  .doc-row .badge.ocr-high { background: #1e3a2a; color: #98e5b4; }
  .doc-row .badge.ocr-medium { background: #3a311e; color: #e5cf98; }
  .doc-row .badge.ocr-low { background: #3a1f1f; color: #f1a0a0; }
  .doc-row .badge.ocr-unset { background: #2a2f3a; color: var(--muted); }
  .doc-row .badge.cleaned-missing { background: #3a1f1f; color: #f1a0a0; }
  .doc-row .badge.cleaned-placeholder { background: #3a311e; color: #e5cf98; }
  .doc-row .badge.cleaned-has-text { background: #1e3a2a; color: #98e5b4; }

  /* --- Center: main document --- */
  section.doc {
    background: #0a0c11;
    display: flex; flex-direction: column;
    overflow: hidden; min-width: 0;
  }
  .doc-toolbar {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 12px; background: var(--panel);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0; font-size: 12px;
  }
  .doc-toolbar .name { color: var(--muted); word-break: break-all; }
  .doc-toolbar .spacer { flex: 1; }
  .doc-toolbar a.open-ext {
    color: var(--accent); text-decoration: none; font-size: 11.5px;
    border: 1px solid var(--border); border-radius: 4px;
    padding: 3px 8px;
  }
  .doc-toolbar a.open-ext:hover { border-color: var(--accent); }
  .doc-area {
    flex: 1; overflow: auto;
    display: flex; align-items: stretch; justify-content: stretch;
    background: #0a0c11;
  }
  .doc-area embed,
  .doc-area iframe {
    width: 100%; height: 100%; border: 0; background: white;
  }
  .doc-area img {
    max-width: 100%; max-height: 100%; object-fit: contain;
    margin: auto; display: block;
  }
  .doc-area .md-body {
    padding: 20px 28px; line-height: 1.55;
    max-width: 760px; margin: 0 auto;
    color: var(--text); font-size: 13.5px;
  }
  /* Markdown render styles — used in main doc area + right-pane tabs */
  .md h1, .md h2, .md h3, .md h4, .md h5, .md h6 {
    margin: 18px 0 8px 0; line-height: 1.3; color: var(--text);
  }
  .md h1 { font-size: 1.55em; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
  .md h2 { font-size: 1.3em; }
  .md h3 { font-size: 1.13em; color: var(--accent); }
  .md h4 { font-size: 1.0em; color: var(--accent2); }
  .md p { margin: 8px 0; }
  .md ul, .md ol { margin: 6px 0 6px 22px; padding: 0; }
  .md li { margin: 2px 0; }
  .md blockquote {
    border-left: 3px solid var(--accent); margin: 8px 0; padding: 2px 12px;
    color: var(--muted); background: rgba(122,162,255,0.05);
  }
  .md code {
    background: var(--panel3); padding: 1px 5px; border-radius: 3px;
    font-size: 0.9em; font-family: ui-monospace, Menlo, monospace;
  }
  .md pre {
    background: var(--panel3); padding: 10px 12px; border-radius: 6px;
    overflow-x: auto; line-height: 1.4;
  }
  .md pre code { background: transparent; padding: 0; }
  .md a { color: var(--accent); text-decoration: none; }
  .md a:hover { text-decoration: underline; }
  .md hr { border: 0; border-top: 1px solid var(--border); margin: 16px 0; }
  .md strong { color: var(--text); font-weight: 700; }
  .md em { color: var(--text); font-style: italic; }
  .md .wikilink {
    background: var(--chip-bg); color: var(--chip-text);
    padding: 1px 6px; border-radius: 3px; font-size: 0.92em;
    text-decoration: none; border: 1px solid transparent;
  }
  .md .wikilink:hover { border-color: var(--accent); }
  .md .wikilink.embed {
    display: inline-block;
    background: var(--panel3); color: var(--accent);
    border: 1px dashed var(--border);
    padding: 2px 8px;
  }
  .md .wikilink.embed::before { content: "📎 "; opacity: 0.7; }
  .md table {
    border-collapse: collapse; margin: 10px 0; font-size: 0.95em;
  }
  .md th, .md td {
    border: 1px solid var(--border); padding: 4px 10px; text-align: left;
  }
  .md th { background: var(--panel2); }
  .doc-empty { color: var(--muted); text-align: center; padding: 40px; margin: auto; }

  /* --- Right panel --- */
  aside.panel {
    background: var(--panel); border-left: 1px solid var(--border);
    overflow: hidden; display: flex; flex-direction: column;
  }
  .tab-bar {
    display: flex; background: var(--panel2);
    border-bottom: 1px solid var(--border); flex-shrink: 0;
  }
  .tab-bar button {
    flex: 1; padding: 9px 8px; background: transparent;
    border: 0; border-right: 1px solid var(--border);
    color: var(--muted); cursor: pointer; font-size: 12px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .tab-bar button:last-child { border-right: 0; }
  .tab-bar button.on { background: var(--panel); color: var(--accent); }
  .tab-bar button .badge {
    display: inline-block; margin-left: 4px;
    background: var(--accent2); color: #1a1300;
    border-radius: 999px; padding: 0 5px;
    font-size: 10px; font-weight: 700; text-transform: none; letter-spacing: 0;
  }
  .tab-body { flex: 1; overflow: auto; padding: 14px 16px; min-height: 0; }
  .tab-body .pair-doc {
    white-space: pre-wrap; line-height: 1.5; font-size: 13px;
  }
  .tab-body .pair-doc embed, .tab-body .pair-doc iframe {
    width: 100%; height: 70vh; border: 0; background: white;
  }
  .tab-body .pair-doc img { max-width: 100%; display: block; }
  .tab-body .pair-meta {
    color: var(--muted); font-size: 11.5px; margin-bottom: 8px;
    word-break: break-all;
  }
  .tab-body .empty { color: var(--muted); text-align: center; padding: 30px 0; }
  /* --- Translation tab: stacked vs side-by-side --- */
  /* When side-by-side is active, the tab-body becomes a fixed-height flex
     container so the two text columns can scroll independently. */
  .tab-body.is-translation-sxs {
    overflow: hidden; padding: 0;
    display: flex; flex-direction: column;
  }
  .translation-view {
    display: flex; flex-direction: column;
    height: 100%; min-height: 0;
  }
  .translation-toolbar {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; border-bottom: 1px solid var(--border);
    background: var(--panel2); flex-shrink: 0;
  }
  .translation-toolbar .label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--muted); font-weight: 600;
  }
  .translation-toolbar .view-modes {
    display: flex; border: 1px solid var(--border); border-radius: 6px;
    overflow: hidden;
  }
  .translation-toolbar .view-modes button {
    background: var(--panel); color: var(--muted);
    border: 0; padding: 4px 10px; font-size: 11.5px; cursor: pointer;
    border-right: 1px solid var(--border);
  }
  .translation-toolbar .view-modes button:last-child { border-right: 0; }
  .translation-toolbar .view-modes button.on {
    background: var(--accent); color: #0b1020; font-weight: 600;
  }
  .translation-toolbar .pair-meta { margin: 0; }
  .translation-cols {
    flex: 1; min-height: 0; display: grid;
    grid-template-columns: 1fr 1fr; gap: 1px;
    background: var(--border); /* shows as a 1px vertical divider */
  }
  .translation-cols .col {
    overflow-y: auto; padding: 12px 14px; background: var(--panel);
    min-width: 0;
  }
  .translation-cols .col-head {
    font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--muted); font-weight: 700; margin: 0 0 8px 0;
    position: sticky; top: 0; background: var(--panel);
    padding: 4px 0; border-bottom: 1px solid var(--border);
    z-index: 1;
  }
  .translation-cols .col-body { font-size: 13px; line-height: 1.55; }
  .translation-cols .col.empty-col {
    color: var(--muted); font-style: italic;
    display: flex; align-items: center; justify-content: center;
    text-align: center;
  }
  /* Stacked mode: single scrolling column inside the regular tab-body */
  .translation-stacked { padding: 0; }
  .sidecar-card {
    border: 1px solid var(--border); border-radius: 6px;
    margin-bottom: 12px; background: var(--panel2);
    overflow: hidden;
  }
  .sidecar-head {
    padding: 8px 12px; background: var(--panel3);
    border-bottom: 1px solid var(--border);
  }
  .sidecar-title { font-weight: 600; font-size: 13px; }
  .sidecar-meta { color: var(--muted); font-size: 11.5px; margin-top: 2px; }
  .sidecar-meta a { color: var(--accent); text-decoration: none; }
  .sidecar-meta a:hover { text-decoration: underline; }
  .sidecar-body { padding: 8px 12px; max-height: 320px; overflow-y: auto; font-size: 12.5px; }
  .sidecar-section-label {
    margin: 14px 0 4px 0; font-size: 10.5px; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600;
  }
  .related-card {
    border: 1px solid var(--border); border-radius: 6px;
    background: var(--panel2);
    padding: 6px 10px; margin-bottom: 6px;
  }
  .related-card:hover { border-color: var(--accent); }
  .related-card .related-title {
    color: var(--text); text-decoration: none; font-weight: 600; font-size: 12.5px;
    word-break: break-word;
  }
  .related-card .related-title:hover { color: var(--accent); text-decoration: underline; }
  .related-card .related-meta { color: var(--muted); font-size: 11px; margin-top: 2px; }
  .sidecar-yaml {
    background: var(--panel3); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 8px 10px; font-size: 11.5px; line-height: 1.45;
    overflow-x: auto;
    font-family: ui-monospace, Menlo, Monaco, monospace;
  }

  /* --- Metadata tab --- */
  .meta-tab h3 {
    margin: 14px 0 6px 0; font-size: 11.5px; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600;
  }
  .meta-tab h3:first-child { margin-top: 2px; }
  .meta-tab .header-title { font-size: 15px; font-weight: 600; margin: 0 0 4px 0; }
  .meta-tab .header-meta {
    color: var(--muted); font-size: 11.5px; margin-bottom: 6px; word-break: break-all;
  }
  .meta-tab .header-meta code {
    background: var(--panel2); padding: 1px 5px; border-radius: 3px; font-size: 11px;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 5px; }
  .chip {
    background: var(--chip-bg); color: var(--chip-text);
    padding: 3px 7px 3px 10px; border-radius: 999px; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
  }
  .chip.added { background: var(--added); color: #b6f0c5; }
  .chip.removed {
    background: var(--removed); color: #ffb3b3; text-decoration: line-through;
  }
  .chip button {
    background: transparent; border: 0; color: inherit; cursor: pointer;
    font-size: 13px; padding: 0; line-height: 1; opacity: 0.7;
  }
  .chip button:hover { opacity: 1; }

  .picker { margin-top: 8px; }
  .picker .seed-row {
    display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px;
  }
  .picker .seed-row button {
    background: var(--panel2); color: var(--muted);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 2px 8px; font-size: 11px; cursor: pointer;
  }
  .picker .seed-row button:hover { color: var(--text); border-color: var(--accent); }
  .picker .seed-row button.has { display: none; }

  .autocomplete { position: relative; }
  .autocomplete input {
    width: 100%; padding: 6px 10px; background: var(--panel2);
    border: 1px solid var(--border); border-radius: 6px; color: var(--text);
    font: inherit;
  }
  .autocomplete .results {
    position: absolute; left: 0; right: 0; top: 100%;
    background: var(--panel3); border: 1px solid var(--border);
    border-top: 0; border-radius: 0 0 6px 6px; max-height: 220px;
    overflow-y: auto; z-index: 10; display: none;
  }
  .autocomplete .results.show { display: block; }
  .autocomplete .results div {
    padding: 5px 10px; cursor: pointer; font-size: 12.5px;
  }
  .autocomplete .results div.focus, .autocomplete .results div:hover {
    background: var(--panel2);
  }
  .date-row {
    display: grid;
    grid-template-columns: 70px 1fr 60px;
    gap: 6px;
  }
  .date-row .date-input {
    background: var(--panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 6px;
    padding: 6px 8px; font: inherit;
  }
  .date-row select.date-input { padding: 5px 6px; }
  .ocr-picker { display: flex; gap: 4px; flex-wrap: wrap; }
  .ocr-picker button {
    background: var(--panel2); color: var(--muted);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 3px 10px; font-size: 11.5px; cursor: pointer;
    text-transform: capitalize;
  }
  .ocr-picker button:hover { color: var(--text); border-color: var(--accent); }
  .ocr-picker button.on { background: var(--accent); color: #0b1020; border-color: var(--accent); font-weight: 600; }
</style>
</head>
<body>
<header>
  <h1>Document Tagger</h1>
  <span class="meta" id="header-meta"></span>
  <div class="spacer"></div>
  <span class="meta">Pending: <span class="pending-badge" id="pending-count">0</span></span>
  <button id="clear-btn" title="Clear all pending edits">Clear</button>
  <button id="export-btn" class="primary">Export Changes</button>
</header>
<main>
  <aside class="list">
    <input id="search" class="search" placeholder="Search documents…" />
    <div class="view-toggle">
      <button data-view="primary" class="on">Primary <span class="n" id="vt-primary-n"></span></button>
      <button data-view="sidecars">Sidecars <span class="n" id="vt-sidecars-n"></span></button>
    </div>
    <div class="filter-row">
      <button class="filter on" data-filter="all">All</button>
      <button class="filter" data-filter="untagged">Untagged</button>
      <button class="filter" data-filter="dirty">Edited</button>
      <button class="filter" data-filter="paired">Has translation/notes</button>
      <button class="filter" data-filter="needs-cleaning">Needs cleaning</button>
    </div>
    <div class="type-section">
      <button class="type-toggle" id="type-toggle">
        <span>Types <span class="caret" id="type-caret">▸</span></span>
        <span class="count" id="type-count">none selected</span>
      </button>
      <div class="type-chips" id="type-chips"></div>
    </div>
    <div class="type-section">
      <button class="type-toggle" id="ocr-toggle">
        <span>OCR confidence <span class="caret" id="ocr-caret">▸</span></span>
        <span class="count" id="ocr-count">none selected</span>
      </button>
      <div class="type-chips" id="ocr-chips"></div>
    </div>
    <div class="type-section">
      <button class="type-toggle" id="branch-toggle">
        <span>Family branch <span class="caret" id="branch-caret">▸</span></span>
        <span class="count" id="branch-count">none selected</span>
      </button>
      <div class="type-chips" id="branch-chips"></div>
    </div>
    <div class="type-section">
      <button class="type-toggle" id="lang-toggle">
        <span>Language <span class="caret" id="lang-caret">▸</span></span>
        <span class="count" id="lang-count">none selected</span>
      </button>
      <div class="type-chips" id="lang-chips"></div>
    </div>
    <div id="doc-list"></div>
  </aside>
  <section class="doc">
    <div class="doc-toolbar" id="doc-toolbar" style="display:none">
      <span class="name" id="doc-name"></span>
      <div class="spacer"></div>
      <span class="meta" id="doc-type"></span>
      <a id="doc-open-ext" class="open-ext" target="_blank" rel="noopener" style="display:none"></a>
    </div>
    <div class="doc-area" id="doc-area">
      <div class="doc-empty">Select a document on the left to begin tagging.</div>
    </div>
  </section>
  <aside class="panel" id="panel">
    <div class="tab-bar" id="tab-bar"></div>
    <div class="tab-body" id="tab-body">
      <div class="empty">No document selected.</div>
    </div>
  </aside>
</main>

<script id="data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const STORAGE_KEY = 'document-tagger-edits-v1';

const TAG_FIELDS = ['related_people', 'places', 'languages', 'topics'];

// edits[id] = {
//   <field>: { add: Set<string>, remove: Set<string> } for field in TAG_FIELDS
//   date: string|undefined
// }
function loadEdits() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    const out = {};
    for (const [k, v] of Object.entries(parsed)) {
      out[k] = {};
      for (const f of TAG_FIELDS) {
        const e = v[f] || { add: [], remove: [] };
        out[k][f] = { add: new Set(e.add || []), remove: new Set(e.remove || []) };
      }
      if (v.date != null) out[k].date = v.date;
      if (v.ocr_confidence !== undefined) out[k].ocr_confidence = v.ocr_confidence;
    }
    return out;
  } catch (e) { return {}; }
}
function saveEdits() {
  const serial = {};
  for (const [k, v] of Object.entries(edits)) {
    if (!isDirty(k)) continue;
    serial[k] = {};
    for (const f of TAG_FIELDS) {
      serial[k][f] = { add: [...v[f].add], remove: [...v[f].remove] };
    }
    if (v.date != null) serial[k].date = v.date;
    if (v.ocr_confidence !== undefined) serial[k].ocr_confidence = v.ocr_confidence;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(serial));
}

let edits = loadEdits();
let selectedId = null;
let currentTab = 'metadata';
let currentFilter = 'all';
let selectedTypes = loadSelectedTypes();
let typesExpanded = false;
let selectedOcr = loadSelectedOcr();
let ocrExpanded = false;
let selectedBranches = loadSelectedBranches();
let branchesExpanded = false;
let selectedLanguages = loadSelectedLanguages();
let languagesExpanded = false;
let currentView = localStorage.getItem('document-tagger-view-v1') || 'primary'; // 'primary' | 'sidecars'
let translationView = localStorage.getItem('document-tagger-translation-view-v1') || 'side-by-side'; // 'stacked' | 'side-by-side'

const LANG_FILTER_KEY = 'document-tagger-language-filter-v1';
function loadSelectedLanguages() {
  try {
    const raw = localStorage.getItem(LANG_FILTER_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch (e) { return new Set(); }
}
function saveSelectedLanguages() {
  localStorage.setItem(LANG_FILTER_KEY, JSON.stringify([...selectedLanguages]));
}
function docLanguages(d) {
  const list = d.languages || [];
  return list.length ? list : ['(none)'];
}

const BRANCH_FILTER_KEY = 'document-tagger-branch-filter-v1';
function loadSelectedBranches() {
  try {
    const raw = localStorage.getItem(BRANCH_FILTER_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch (e) { return new Set(); }
}
function saveSelectedBranches() {
  localStorage.setItem(BRANCH_FILTER_KEY, JSON.stringify([...selectedBranches]));
}
function docBranches(d) {
  const list = d.branches || [];
  return list.length ? list : ['(no branch)'];
}

const OCR_FILTER_KEY = 'document-tagger-ocr-filter-v1';
function loadSelectedOcr() {
  try {
    const raw = localStorage.getItem(OCR_FILTER_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch (e) { return new Set(); }
}
function saveSelectedOcr() {
  localStorage.setItem(OCR_FILTER_KEY, JSON.stringify([...selectedOcr]));
}
function ocrEffective(doc) {
  const e = edits[doc.id];
  if (e && e.ocr_confidence !== undefined) return e.ocr_confidence || '';
  return doc.ocr_confidence || '';
}
function ocrBucket(val) {
  return val ? val : '(not set)';
}

const TYPE_FILTER_KEY = 'document-tagger-type-filter-v1';
function loadSelectedTypes() {
  try {
    const raw = localStorage.getItem(TYPE_FILTER_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch (e) { return new Set(); }
}
function saveSelectedTypes() {
  localStorage.setItem(TYPE_FILTER_KEY, JSON.stringify([...selectedTypes]));
}

function ensureEdit(id) {
  if (!edits[id]) {
    edits[id] = {};
    for (const f of TAG_FIELDS) edits[id][f] = { add: new Set(), remove: new Set() };
  }
  return edits[id];
}
function isDirty(id) {
  const e = edits[id]; if (!e) return false;
  for (const f of TAG_FIELDS) {
    if (e[f].add.size || e[f].remove.size) return true;
  }
  if (e.date != null) return true;
  if (e.ocr_confidence !== undefined) return true;
  return false;
}
function pendingTotal() {
  return Object.keys(edits).filter(isDirty).length;
}
function effectiveTags(doc, field) {
  const base = new Set(doc[field] || []);
  const e = edits[doc.id];
  if (e && e[field]) {
    for (const t of e[field].remove) base.delete(t);
    for (const t of e[field].add) base.add(t);
  }
  return [...base];
}
function isUntagged(doc) {
  return effectiveTags(doc, 'related_people').length === 0
      && effectiveTags(doc, 'topics').length === 0;
}
function parseDate(s) {
  if (!s) return { y: '', m: '', d: '' };
  const m = String(s).trim().match(/^(\d{4})(?:[-/](\d{1,2}))?(?:[-/](\d{1,2}))?$/);
  if (!m) return { y: String(s), m: '', d: '' };
  return {
    y: m[1] || '',
    m: m[2] ? String(m[2]).padStart(2, '0') : '',
    d: m[3] ? String(m[3]).padStart(2, '0') : '',
  };
}
function joinDate(y, mo, d) {
  if (!y) return '';
  let out = String(y);
  if (mo) out += '-' + String(mo).padStart(2, '0');
  if (mo && d) out += '-' + String(d).padStart(2, '0');
  return out;
}
function effectiveDate(doc) {
  const e = edits[doc.id];
  const raw = (e && e.date != null) ? e.date : (doc.date || '');
  return parseDate(raw);
}
function effectiveDateStr(doc) {
  const dd = effectiveDate(doc);
  return joinDate(dd.y, dd.m, dd.d);
}
function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderList() {
  const wrap = document.getElementById('doc-list');
  wrap.innerHTML = '';
  const q = (document.getElementById('search').value || '').toLowerCase();
  // Update view toggle counts
  const primaryN = DATA.docs.filter(d => !d.is_synthesis).length;
  const sidecarN = DATA.docs.filter(d => d.is_synthesis).length;
  document.getElementById('vt-primary-n').textContent = primaryN;
  document.getElementById('vt-sidecars-n').textContent = sidecarN;
  document.querySelectorAll('.view-toggle button').forEach(b => {
    b.classList.toggle('on', b.dataset.view === currentView);
  });
  const docs = DATA.docs.filter(d => {
    if (currentView === 'primary' && d.is_synthesis) return false;
    if (currentView === 'sidecars' && !d.is_synthesis) return false;
    if (currentFilter === 'untagged' && !isUntagged(d)) return false;
    if (currentFilter === 'dirty' && !isDirty(d.id)) return false;
    if (currentFilter === 'paired' && !(d.translation || d.notes || d.transcription)) return false;
    if (currentFilter === 'needs-cleaning' && d.cleaned_text_status === 'has-text') return false;
    if (selectedTypes.size > 0) {
      const t = (d.type || '').trim() || '(no type)';
      if (!selectedTypes.has(t)) return false;
    }
    if (selectedOcr.size > 0) {
      if (!selectedOcr.has(ocrBucket(ocrEffective(d)))) return false;
    }
    if (selectedBranches.size > 0) {
      const branches = docBranches(d);
      if (!branches.some(b => selectedBranches.has(b))) return false;
    }
    if (selectedLanguages.size > 0) {
      const langs = docLanguages(d);
      if (!langs.some(l => selectedLanguages.has(l))) return false;
    }
    if (!q) return true;
    if (d.title.toLowerCase().includes(q)) return true;
    if (d.id.toLowerCase().includes(q)) return true;
    for (const f of TAG_FIELDS) {
      if ((d[f] || []).some(t => t.toLowerCase().includes(q))) return true;
    }
    return false;
  });
  for (const d of docs) {
    const row = document.createElement('div');
    row.className = 'doc-row' + (selectedId === d.id ? ' active' : '');
    const pairCount = (d.translation ? 1 : 0) + (d.notes ? 1 : 0) + (d.transcription ? 1 : 0);
    const ocr = ocrEffective(d);
    const ocrClass = ocr ? ('ocr-' + ocr) : 'ocr-unset';
    const ocrLabel = ocr ? ('OCR ' + ocr) : 'OCR ?';
    const cts = d.cleaned_text_status || 'missing';
    const ctsLabels = {
      'has-text': 'text ✓',
      'placeholder': 'text placeholder',
      'missing': 'no text section',
    };
    row.innerHTML = `
      <div class="t">${escapeHtml(d.title)}</div>
      <div class="sub">${escapeHtml(d.type || 'untyped')}${d.date ? ' · ' + escapeHtml(d.date) : ''}</div>
      <div class="badges">
        <span class="badge ${ocrClass}">${ocrLabel}</span>
        <span class="badge cleaned-${cts}" title="cleaned text status">${ctsLabels[cts]}</span>
        ${isDirty(d.id) ? '<span class="badge dirty">edited</span>' : ''}
        ${pairCount ? `<span class="badge pair">${pairCount} attachment${pairCount===1?'':'s'}</span>` : ''}
        ${isUntagged(d) ? '<span class="badge untagged">untagged</span>' : ''}
      </div>`;
    row.addEventListener('click', () => selectDoc(d.id));
    wrap.appendChild(row);
  }
  document.getElementById('header-meta').textContent =
    `${DATA.docs.length} docs · ${docs.length} shown · ${DATA.people.length} people`;
  document.getElementById('pending-count').textContent = pendingTotal();
}

function selectDoc(id) {
  selectedId = id;
  // Update the URL so the selection is deep-linkable / shareable.
  // Use replaceState so we don't pollute the back stack with every click.
  if (id) {
    const params = new URLSearchParams(location.search);
    params.set('doc', id);
    history.replaceState({}, '', location.pathname + '?' + params.toString() + location.hash);
  }
  renderList();
  renderMainDoc();
  renderPanel();
}

function renderMainDoc() {
  const area = document.getElementById('doc-area');
  const toolbar = document.getElementById('doc-toolbar');
  const doc = DATA.docs.find(d => d.id === selectedId);
  if (!doc) {
    toolbar.style.display = 'none';
    area.innerHTML = '<div class="doc-empty">Select a document on the left to begin tagging.</div>';
    return;
  }
  toolbar.style.display = 'flex';
  document.getElementById('doc-name').textContent = doc.main.name || doc.id;
  document.getElementById('doc-type').textContent = doc.type || '';
  // Open-externally link in the toolbar when the doc has a file src
  const ext = document.getElementById('doc-open-ext');
  if (doc.main.src) {
    ext.style.display = '';
    ext.href = doc.main.src;
    ext.textContent = 'Open in new tab ↗';
  } else {
    ext.style.display = 'none';
  }
  area.innerHTML = renderDocBlob(doc.main);
}

// --- Minimal markdown renderer ---------------------------------------------
// Handles: headings, bold/italic, lists (nested), blockquotes, code (inline +
// fenced), horizontal rules, links, paragraphs, wikilinks [[Foo]] and embeds
// ![[Foo]]. Tables are parsed but kept simple (pipe rows with header row).
function renderMarkdown(md) {
  if (!md) return '';
  let src = String(md).replace(/\r\n/g, '\n');

  // Extract fenced code blocks first so their contents aren't processed.
  const codeBlocks = [];
  src = src.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (_, lang, body) => {
    const idx = codeBlocks.length;
    codeBlocks.push(`<pre><code>${escapeHtml(body.replace(/\n$/, ''))}</code></pre>`);
    return ` CODE${idx} `;
  });

  const lines = src.split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    // Code-block placeholder
    if (/^ CODE\d+ $/.test(line.trim())) {
      out.push(line.trim());
      i++; continue;
    }
    // Horizontal rule
    if (/^(\s*[-*_]\s*){3,}$/.test(line.replace(/\s+/g, ''))) {
      out.push('<hr/>'); i++; continue;
    }
    // ATX heading
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      const lvl = h[1].length;
      out.push(`<h${lvl}>${renderInline(h[2])}</h${lvl}>`);
      i++; continue;
    }
    // Blockquote
    if (/^>\s?/.test(line)) {
      const block = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        block.push(lines[i].replace(/^>\s?/, ''));
        i++;
      }
      out.push(`<blockquote>${renderMarkdown(block.join('\n'))}</blockquote>`);
      continue;
    }
    // Lists (unordered or ordered) — may be nested by indentation
    if (/^(\s*)([-*+]|\d+[.)])\s+/.test(line)) {
      const [block, consumed] = collectListBlock(lines, i);
      out.push(renderListBlock(block));
      i += consumed; continue;
    }
    // Table (very minimal)
    if (i + 1 < lines.length && /^\s*\|.*\|\s*$/.test(line)
        && /^\s*\|?\s*:?-{2,}/.test(lines[i+1])) {
      const headerCells = parseTableRow(line);
      const rows = [];
      i += 2; // skip header + separator
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        rows.push(parseTableRow(lines[i]));
        i++;
      }
      const thead = `<thead><tr>${headerCells.map(c => `<th>${renderInline(c)}</th>`).join('')}</tr></thead>`;
      const tbody = `<tbody>${rows.map(r => `<tr>${r.map(c => `<td>${renderInline(c)}</td>`).join('')}</tr>`).join('')}</tbody>`;
      out.push(`<table>${thead}${tbody}</table>`);
      continue;
    }
    // Blank line — paragraph break
    if (line.trim() === '') { i++; continue; }
    // Paragraph (gather contiguous non-special lines)
    const para = [line];
    i++;
    while (i < lines.length && lines[i].trim() !== ''
           && !/^(#{1,6})\s+/.test(lines[i])
           && !/^>\s?/.test(lines[i])
           && !/^(\s*)([-*+]|\d+[.)])\s+/.test(lines[i])
           && !/^ CODE\d+ $/.test(lines[i].trim())) {
      para.push(lines[i]); i++;
    }
    out.push(`<p>${renderInline(para.join(' '))}</p>`);
  }

  let html = out.join('\n');
  // Reinsert code blocks
  html = html.replace(/ CODE(\d+) /g, (_, n) => codeBlocks[+n] || '');
  return html;
}

function parseTableRow(line) {
  return line.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(s => s.trim());
}

function collectListBlock(lines, start) {
  // Returns [blockLines, consumed]. A list block ends on a blank line that
  // isn't immediately followed by another indented list-continuation line.
  const out = [];
  let i = start;
  while (i < lines.length) {
    const l = lines[i];
    if (l.trim() === '') {
      // Look ahead — does the next non-blank line belong to the list?
      let j = i + 1;
      if (j < lines.length && /^(\s+)([-*+]|\d+[.)])\s+/.test(lines[j])) {
        out.push(l); i++; continue;
      }
      break;
    }
    if (/^(\s*)([-*+]|\d+[.)])\s+/.test(l) || /^\s{2,}\S/.test(l)) {
      out.push(l); i++; continue;
    }
    break;
  }
  return [out, i - start];
}

function renderListBlock(lines) {
  // Parse a flat list block into a (possibly nested) ul/ol tree.
  // Tracks indent levels; each indent step opens a sub-list.
  const items = [];
  for (const raw of lines) {
    const m = raw.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/);
    if (m) {
      items.push({
        indent: m[1].length, ordered: /\d/.test(m[2]),
        text: m[3], children: [],
      });
    } else {
      // continuation of previous item's text
      if (items.length) items[items.length - 1].text += ' ' + raw.trim();
    }
  }
  function buildTree(start, baseIndent) {
    const out = [];
    let i = start;
    while (i < items.length && items[i].indent >= baseIndent) {
      if (items[i].indent > baseIndent) { i++; continue; }
      const node = items[i];
      const [children, j] = (i + 1 < items.length && items[i+1].indent > baseIndent)
        ? buildTree(i + 1, items[i+1].indent)
        : [[], i + 1];
      node.children = children;
      out.push(node);
      i = j;
    }
    return [out, i];
  }
  const [tree, _] = buildTree(0, items[0]?.indent ?? 0);
  function render(nodes) {
    if (!nodes.length) return '';
    const tag = nodes[0].ordered ? 'ol' : 'ul';
    return `<${tag}>` + nodes.map(n =>
      `<li>${renderInline(n.text)}${render(n.children)}</li>`
    ).join('') + `</${tag}>`;
  }
  return render(tree);
}

function renderInline(s) {
  if (!s) return '';
  // Escape first, then re-introduce inline markdown structures.
  let h = escapeHtml(s);
  // Embed wikilinks: ![[file]] or ![[file|alias]]
  h = h.replace(/!\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]/g,
    (_, name, alias) => `<span class="wikilink embed">${escapeHtml(alias || name)}</span>`);
  // Plain wikilinks: [[Name]] or [[Name|alias]]
  h = h.replace(/\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]/g,
    (_, name, alias) => `<span class="wikilink">${escapeHtml(alias || name)}</span>`);
  // Images: ![alt](url)
  h = h.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,
    (_, alt, url) => `<img alt="${alt}" src="${url}" style="max-width:100%"/>`);
  // Links: [text](url)
  h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
    (_, text, url) => `<a href="${url}" target="_blank" rel="noopener">${text}</a>`);
  // Inline code: `foo`
  h = h.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);
  // Bold: **text** or __text__
  h = h.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
       .replace(/__([^_]+)__/g, '<strong>$1</strong>');
  // Italic: *text* or _text_  (avoid clashing with already-emitted strong)
  h = h.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
       .replace(/(^|[^_])_([^_\n]+)_(?!_)/g, '$1<em>$2</em>');
  return h;
}

function renderDocBlob(blob) {
  if (!blob || blob.kind === 'none') {
    return '<div class="doc-empty">No document file attached.</div>';
  }
  if (blob.kind === 'pdf') {
    return `<embed src="${blob.src}" type="application/pdf" />`;
  }
  if (blob.kind === 'image') {
    return `<img src="${blob.src}" alt="${escapeHtml(blob.name || '')}" />`;
  }
  if (blob.kind === 'markdown') {
    return `<div class="md-body md">${renderMarkdown(blob.text || '')}</div>`;
  }
  return '<div class="doc-empty">Unsupported document type.</div>';
}

function renderPanel() {
  const tabBar = document.getElementById('tab-bar');
  const body = document.getElementById('tab-body');
  const doc = DATA.docs.find(d => d.id === selectedId);
  if (!doc) {
    tabBar.innerHTML = '';
    body.innerHTML = '<div class="empty">No document selected.</div>';
    return;
  }

  const tabs = [];
  if (doc.translation) tabs.push({ id: 'translation', label: 'Translation' });
  if (doc.notes) tabs.push({ id: 'notes', label: 'Notes' });
  if (doc.transcription) tabs.push({ id: 'transcription', label: 'Transcription' });
  if ((doc.referenced_by || []).length) {
    tabs.push({ id: 'sidecars', label: `Sidecars (${doc.referenced_by.length})` });
  }
  const relCount = (doc.related_cluster || []).length + (doc.related_by_people || []).length;
  if (relCount) {
    tabs.push({ id: 'related', label: `Related (${relCount})` });
  }
  tabs.push({ id: 'sidecar', label: 'Sidecar' });
  tabs.push({ id: 'metadata', label: 'Metadata' });

  // If currently selected tab no longer exists for this doc, fall back to metadata.
  if (!tabs.find(t => t.id === currentTab)) currentTab = 'metadata';

  tabBar.innerHTML = tabs.map(t =>
    `<button data-tab="${t.id}" class="${t.id === currentTab ? 'on' : ''}">${t.label}</button>`
  ).join('');
  tabBar.querySelectorAll('button').forEach(b => {
    b.addEventListener('click', () => { currentTab = b.dataset.tab; renderPanel(); });
  });

  // The translation tab can use a side-by-side layout that needs the
  // tab-body to be a fixed-height flex container. Toggle the class up front
  // so all branches start from a clean state.
  body.classList.remove('is-translation-sxs');

  if (currentTab === 'metadata') {
    body.innerHTML = renderMetadataTab(doc);
    wireMetadataTab(doc);
  } else if (currentTab === 'sidecars') {
    body.innerHTML = renderSidecarsTab(doc);
    wireSidecarsTab(doc);
  } else if (currentTab === 'sidecar') {
    body.innerHTML = renderSidecarSourceTab(doc);
  } else if (currentTab === 'related') {
    body.innerHTML = renderRelatedTab(doc);
    wireRelatedTab();
  } else if (currentTab === 'translation') {
    if (translationView === 'side-by-side') body.classList.add('is-translation-sxs');
    body.innerHTML = renderTranslationTab(doc);
    wireTranslationTab(doc);
  } else {
    body.innerHTML = renderPairTab(doc[currentTab]);
  }
}

function renderTranslationTab(doc) {
  const blob = doc.translation;
  if (!blob) return '<div class="empty">No translation companion.</div>';
  const name = escapeHtml(blob.name || '');
  const modes = `
    <div class="view-modes">
      <button data-mode="side-by-side" class="${translationView === 'side-by-side' ? 'on' : ''}">Side by side</button>
      <button data-mode="stacked" class="${translationView === 'stacked' ? 'on' : ''}">Stacked</button>
    </div>`;
  const toolbar = `
    <div class="translation-toolbar">
      ${modes}
      <div class="pair-meta"><code>${name}</code></div>
    </div>`;

  if (translationView === 'stacked') {
    // Stacked: existing single-pane behavior, with the toolbar on top so the
    // user can flip back to side-by-side.
    const inner = blob.kind === 'pdf'
      ? `<embed src="${blob.src}" type="application/pdf" />`
      : blob.kind === 'image'
      ? `<img src="${blob.src}" alt="${name}" />`
      : `<div class="md">${renderMarkdown(blob.text || '')}</div>`;
    return `${toolbar}<div class="pair-doc" style="padding:14px 16px">${inner}</div>`;
  }

  // Side-by-side: original (cleaned text from primary) on the left,
  // translation on the right.
  const left = (doc.cleaned_text || '').trim()
    ? `<div class="col-body md">${renderMarkdown(doc.cleaned_text)}</div>`
    : `<div class="col-body" style="color:var(--muted);font-style:italic">No "## Cleaned Text" section in the primary sidecar — switch to Stacked to view the translation alone, or add a Cleaned Text section to the primary.</div>`;
  const rightBody = blob.kind === 'pdf'
    ? `<embed src="${blob.src}" type="application/pdf" style="width:100%;height:80vh;border:0;background:#fff" />`
    : blob.kind === 'image'
    ? `<img src="${blob.src}" alt="${name}" style="max-width:100%;display:block" />`
    : `<div class="md">${renderMarkdown(blob.text || '')}</div>`;
  return `
    <div class="translation-view">
      ${toolbar}
      <div class="translation-cols">
        <div class="col" data-col="left">
          <div class="col-head">Original (cleaned text)</div>
          ${left}
        </div>
        <div class="col" data-col="right">
          <div class="col-head">English translation</div>
          <div class="col-body">${rightBody}</div>
        </div>
      </div>
    </div>`;
}

function wireTranslationTab(doc) {
  document.querySelectorAll('.translation-toolbar .view-modes button').forEach(b => {
    b.addEventListener('click', () => {
      translationView = b.dataset.mode;
      localStorage.setItem('document-tagger-translation-view-v1', translationView);
      renderPanel();
    });
  });
  if (translationView !== 'side-by-side') return;
  const left = document.querySelector('.translation-cols .col[data-col="left"]');
  const right = document.querySelector('.translation-cols .col[data-col="right"]');
  if (!left || !right) return;
  let syncing = false;
  function syncFrom(src, dst) {
    if (syncing) return;
    const srcRange = src.scrollHeight - src.clientHeight;
    const dstRange = dst.scrollHeight - dst.clientHeight;
    if (srcRange <= 0 || dstRange <= 0) return;
    syncing = true;
    dst.scrollTop = dstRange * (src.scrollTop / srcRange);
    // Release on the next animation frame so the scroll event the assignment
    // triggers on `dst` doesn't bounce back to `src`.
    requestAnimationFrame(() => { syncing = false; });
  }
  left.addEventListener('scroll', () => syncFrom(left, right));
  right.addEventListener('scroll', () => syncFrom(right, left));
}

function renderSidecarSourceTab(doc) {
  const raw = doc.sidecar_raw || '(sidecar file is empty)';
  // Split frontmatter from body so we can show YAML as a code block and the
  // body as rendered markdown.
  let fm = '', body = raw;
  if (raw.startsWith('---')) {
    const end = raw.indexOf('\n---', 3);
    if (end > -1) {
      fm = raw.slice(3, end).replace(/^\n/, '');
      body = raw.slice(end + 4).replace(/^\n/, '');
    }
  }
  const obsidianUri = 'obsidian://open?vault=genealogy&file=' + encodeURIComponent(doc.sidecar);
  return `
    <div class="pair-meta">
      <code>${escapeHtml(doc.sidecar)}</code>
      &nbsp;·&nbsp;
      <a href="${doc.sidecar ? '../' + doc.sidecar : '#'}" target="_blank" rel="noopener">view raw</a>
      &nbsp;·&nbsp;
      <a href="${obsidianUri}" target="_blank" rel="noopener">open in Obsidian</a>
    </div>
    ${fm ? `<div class="sidecar-section-label">YAML frontmatter</div>
            <pre class="sidecar-yaml"><code>${escapeHtml(fm)}</code></pre>` : ''}
    <div class="sidecar-section-label">Body</div>
    <div class="md">${renderMarkdown(body)}</div>`;
}

function renderSidecarsTab(doc) {
  const refs = doc.referenced_by || [];
  if (!refs.length) return '<div class="empty">No synthesis docs reference this one.</div>';
  const parts = refs.map(id => {
    const s = DATA.docs.find(d => d.id === id);
    if (!s) return '';
    const meta = `${escapeHtml(s.type || 'synthesis')}${s.date ? ' · ' + escapeHtml(s.date) : ''}`;
    return `
      <div class="sidecar-card" data-sidecar="${escapeHtml(id)}">
        <div class="sidecar-head">
          <div class="sidecar-title">${escapeHtml(s.title)}</div>
          <div class="sidecar-meta">${meta} · <a href="#" data-open-sidecar="${escapeHtml(id)}">open as main</a></div>
        </div>
        <div class="sidecar-body md">${renderMarkdown(s.body_text || '(no body)')}</div>
      </div>`;
  });
  return parts.join('');
}

function relatedCardHtml(id, hint) {
  const d = DATA.docs.find(x => x.id === id);
  if (!d) return '';
  const sub = `${escapeHtml(d.type || 'untyped')}${d.date ? ' · ' + escapeHtml(d.date) : ''}`;
  return `
    <div class="related-card">
      <a class="related-title" href="?doc=${encodeURIComponent(id)}" data-related="${escapeHtml(id)}">${escapeHtml(d.title)}</a>
      <div class="related-meta">${sub}${hint ? ' · ' + escapeHtml(hint) : ''}</div>
    </div>`;
}

function renderRelatedTab(doc) {
  const cluster = doc.related_cluster || [];
  const byPeople = doc.related_by_people || [];
  if (!cluster.length && !byPeople.length) {
    return '<div class="empty">No related documents.</div>';
  }
  const parts = [];
  if (cluster.length) {
    parts.push(`<div class="sidecar-section-label">Same source cluster (${cluster.length})</div>`);
    for (const id of cluster) parts.push(relatedCardHtml(id, null));
  }
  if (byPeople.length) {
    parts.push(`<div class="sidecar-section-label">Shares people (${byPeople.length})</div>`);
    for (const entry of byPeople) {
      parts.push(relatedCardHtml(entry.id, `${entry.overlap} shared person${entry.overlap === 1 ? '' : 's'}`));
    }
  }
  return parts.join('');
}

function wireRelatedTab() {
  document.querySelectorAll('a[data-related]').forEach(a => {
    a.addEventListener('click', ev => {
      ev.preventDefault();
      const id = a.dataset.related;
      const target = DATA.docs.find(d => d.id === id);
      if (!target) return;
      // Flip the left-panel view if needed so the target is visible.
      const needView = target.is_synthesis ? 'sidecars' : 'primary';
      if (currentView !== needView) {
        currentView = needView;
        localStorage.setItem('document-tagger-view-v1', currentView);
      }
      selectDoc(id);
    });
  });
}

function wireSidecarsTab(doc) {
  document.querySelectorAll('a[data-open-sidecar]').forEach(a => {
    a.addEventListener('click', ev => {
      ev.preventDefault();
      // Switch to sidecars view (if not already) and select this sidecar as the main doc.
      currentView = 'sidecars';
      localStorage.setItem('document-tagger-view-v1', currentView);
      selectDoc(a.dataset.openSidecar);
    });
  });
}

function renderPairTab(blob) {
  if (!blob) return '<div class="empty">Not present.</div>';
  let inner = '';
  if (blob.kind === 'pdf') {
    inner = `<embed src="${blob.src}" type="application/pdf" />`;
  } else if (blob.kind === 'image') {
    inner = `<img src="${blob.src}" alt="${escapeHtml(blob.name || '')}" />`;
  } else {
    inner = `<div class="md">${renderMarkdown(blob.text || '')}</div>`;
  }
  return `
    <div class="pair-meta"><code>${escapeHtml(blob.name || '')}</code></div>
    <div class="pair-doc">${inner}</div>`;
}

function renderChipsBlock(doc, field, seed) {
  const e = ensureEdit(doc.id);
  const ee = e[field];
  const base = doc[field] || [];
  const parts = [];
  for (const t of base) {
    if (ee.remove.has(t)) {
      parts.push(`<span class="chip removed" data-tag="${escapeHtml(t)}" data-field="${field}"><span>${escapeHtml(t)}</span><button data-action="undo-remove">↺</button></span>`);
    } else {
      parts.push(`<span class="chip" data-tag="${escapeHtml(t)}" data-field="${field}"><span>${escapeHtml(t)}</span><button data-action="remove">×</button></span>`);
    }
  }
  for (const t of ee.add) {
    parts.push(`<span class="chip added" data-tag="${escapeHtml(t)}" data-field="${field}"><span>${escapeHtml(t)}</span><button data-action="undo-add">×</button></span>`);
  }
  let seedBtns = '';
  if (seed && seed.length) {
    const present = new Set(effectiveTags(doc, field));
    seedBtns = `<div class="seed-row">` + seed.map(s =>
      `<button data-seed="${escapeHtml(s)}" data-field="${field}" class="${present.has(s) ? 'has' : ''}">+ ${escapeHtml(s)}</button>`
    ).join('') + `</div>`;
  }
  return { chips: parts.join(''), seedBtns };
}

function renderMetadataTab(doc) {
  const peopleBlock = renderChipsBlock(doc, 'related_people', null);
  const placesBlock = renderChipsBlock(doc, 'places', null);
  const langsBlock = renderChipsBlock(doc, 'languages', DATA.language_seed);
  const topicsBlock = renderChipsBlock(doc, 'topics', DATA.topic_seed);
  const dd = effectiveDate(doc);
  return `
    <div class="meta-tab">
      <h3 class="header-title" style="font-size:15px;color:var(--text);text-transform:none;letter-spacing:0">${escapeHtml(doc.title)}</h3>
      <div class="header-meta">
        <code>${escapeHtml(doc.sidecar)}</code>
        ${doc.type ? `<br/>type: <code>${escapeHtml(doc.type)}</code>` : ''}
      </div>

      <h3>People</h3>
      <div class="chips" data-block="related_people">${peopleBlock.chips}</div>
      <div class="picker">
        <div class="autocomplete">
          <input id="ac-people" type="text" placeholder="+ Add person — start typing…" autocomplete="off" data-field="related_people"/>
          <div class="results" id="ac-people-results"></div>
        </div>
      </div>

      <h3>Places</h3>
      <div class="chips" data-block="places">${placesBlock.chips}</div>
      <div class="picker">
        <div class="autocomplete">
          <input id="ac-places" type="text" placeholder="+ Add place…" autocomplete="off" data-field="places"/>
        </div>
      </div>

      <h3>Languages</h3>
      <div class="chips" data-block="languages">${langsBlock.chips}</div>
      <div class="picker">
        ${langsBlock.seedBtns}
        <div class="autocomplete">
          <input id="ac-languages" type="text" placeholder="+ Add language…" autocomplete="off" data-field="languages"/>
        </div>
      </div>

      <h3>Topics</h3>
      <div class="chips" data-block="topics">${topicsBlock.chips}</div>
      <div class="picker">
        ${topicsBlock.seedBtns}
        <div class="autocomplete">
          <input id="ac-topics" type="text" placeholder="+ Add topic…" autocomplete="off" data-field="topics"/>
        </div>
      </div>

      <h3>OCR confidence</h3>
      <div class="ocr-picker" id="ocr-picker">
        ${['high','medium','low'].map(v => {
          const cur = ocrEffective(doc);
          return `<button data-ocr="${v}" class="${cur === v ? 'on' : ''}">${v}</button>`;
        }).join('')}
        <button data-ocr="" class="${!ocrEffective(doc) ? 'on' : ''}">(unset)</button>
      </div>

      <h3>Date</h3>
      <div class="date-row">
        <input id="date-y" class="date-input" type="number" placeholder="YYYY" min="1700" max="2100" value="${escapeHtml(dd.y)}"/>
        <select id="date-m" class="date-input">
          <option value="">— month —</option>
          <option value="01">January</option><option value="02">February</option>
          <option value="03">March</option><option value="04">April</option>
          <option value="05">May</option><option value="06">June</option>
          <option value="07">July</option><option value="08">August</option>
          <option value="09">September</option><option value="10">October</option>
          <option value="11">November</option><option value="12">December</option>
        </select>
        <input id="date-d" class="date-input" type="number" placeholder="DD" min="1" max="31" value="${escapeHtml(dd.d)}"/>
      </div>
      <div class="header-meta" style="margin-top:4px">Currently saved: <code id="date-preview">${escapeHtml(effectiveDateStr(doc) || '(none)')}</code></div>
    </div>`;
}

function wireMetadataTab(doc) {
  const body = document.getElementById('tab-body');

  // Chip clicks (remove / undo)
  body.querySelectorAll('[data-block]').forEach(block => {
    block.addEventListener('click', ev => {
      const btn = ev.target.closest('button'); if (!btn) return;
      const chip = btn.closest('.chip');
      const tag = chip.dataset.tag; const field = chip.dataset.field;
      const ee = ensureEdit(doc.id)[field];
      const action = btn.dataset.action;
      if (action === 'remove') ee.remove.add(tag);
      else if (action === 'undo-remove') ee.remove.delete(tag);
      else if (action === 'undo-add') ee.add.delete(tag);
      saveEdits(); renderPanel(); renderList();
    });
  });

  // Seed-button quick picks
  body.querySelectorAll('button[data-seed]').forEach(b => {
    b.addEventListener('click', () => {
      const field = b.dataset.field; const val = b.dataset.seed;
      const ee = ensureEdit(doc.id)[field];
      if ((doc[field] || []).includes(val)) ee.remove.delete(val);
      else ee.add.add(val);
      saveEdits(); renderPanel(); renderList();
    });
  });

  // People autocomplete
  wirePersonAutocomplete(doc, 'related_people', 'ac-people', 'ac-people-results', DATA.people);

  // Free-text inputs (places / languages / topics) — Enter to add
  for (const fid of [['ac-places', 'places'], ['ac-languages', 'languages'], ['ac-topics', 'topics']]) {
    const [id, field] = fid;
    const el = body.querySelector('#' + id); if (!el) continue;
    el.addEventListener('keydown', ev => {
      if (ev.key !== 'Enter') return;
      ev.preventDefault();
      const val = el.value.trim(); if (!val) return;
      const ee = ensureEdit(doc.id)[field];
      if ((doc[field] || []).includes(val)) ee.remove.delete(val);
      else ee.add.add(val);
      el.value = '';
      saveEdits(); renderPanel(); renderList();
    });
  }

  // OCR confidence picker
  body.querySelectorAll('#ocr-picker button').forEach(b => {
    b.addEventListener('click', () => {
      const val = b.dataset.ocr;
      const ee = ensureEdit(doc.id);
      if (val === (doc.ocr_confidence || '')) {
        // back to original — clear edit
        delete ee.ocr_confidence;
      } else {
        ee.ocr_confidence = val;
      }
      saveEdits(); renderPanel(); renderList();
    });
  });

  // Date
  const dY = body.querySelector('#date-y');
  const dM = body.querySelector('#date-m');
  const dD = body.querySelector('#date-d');
  const dPreview = body.querySelector('#date-preview');
  const cur = effectiveDate(doc);
  if (cur.m) dM.value = cur.m;
  function pushDate() {
    const ee = ensureEdit(doc.id);
    const newStr = joinDate(dY.value.trim(), dM.value, dD.value.trim());
    if (newStr === (doc.date || '')) delete ee.date;
    else ee.date = newStr;
    dPreview.textContent = newStr || '(none)';
    saveEdits(); renderList();
  }
  [dY, dM, dD].forEach(el => el.addEventListener('input', pushDate));
  dM.addEventListener('change', pushDate);
}

function wirePersonAutocomplete(doc, field, inputId, resultsId, options) {
  const body = document.getElementById('tab-body');
  const inp = body.querySelector('#' + inputId);
  let resultsEl = body.querySelector('#' + resultsId);
  if (!resultsEl) {
    // results container — create it adjacent
    resultsEl = document.createElement('div');
    resultsEl.className = 'results';
    resultsEl.id = resultsId;
    inp.parentElement.appendChild(resultsEl);
  }
  let focusIdx = -1;
  function update() {
    const q = inp.value.trim().toLowerCase();
    if (!q) { resultsEl.classList.remove('show'); resultsEl.innerHTML = ''; return; }
    const present = new Set(effectiveTags(doc, field));
    const matches = options.filter(o => o.toLowerCase().includes(q) && !present.has(o)).slice(0, 20);
    if (!matches.length) { resultsEl.classList.remove('show'); return; }
    resultsEl.innerHTML = matches.map((m, i) =>
      `<div data-name="${escapeHtml(m)}" class="${i===0?'focus':''}">${escapeHtml(m)}</div>`).join('');
    resultsEl.classList.add('show');
    focusIdx = 0;
  }
  function pick(val) {
    const ee = ensureEdit(doc.id)[field];
    if ((doc[field] || []).includes(val)) ee.remove.delete(val);
    else ee.add.add(val);
    inp.value = ''; resultsEl.classList.remove('show');
    saveEdits(); renderPanel(); renderList();
  }
  inp.addEventListener('input', update);
  inp.addEventListener('keydown', ev => {
    const items = [...resultsEl.querySelectorAll('div')];
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      if (!items.length) return;
      focusIdx = (focusIdx + 1) % items.length;
      items.forEach((el, i) => el.classList.toggle('focus', i === focusIdx));
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      if (!items.length) return;
      focusIdx = (focusIdx - 1 + items.length) % items.length;
      items.forEach((el, i) => el.classList.toggle('focus', i === focusIdx));
    } else if (ev.key === 'Enter') {
      ev.preventDefault();
      if (focusIdx >= 0 && items[focusIdx]) pick(items[focusIdx].dataset.name);
      else if (inp.value.trim()) pick(inp.value.trim());
    } else if (ev.key === 'Escape') {
      resultsEl.classList.remove('show');
    }
  });
  resultsEl.addEventListener('click', ev => {
    const d = ev.target.closest('div[data-name]');
    if (d) pick(d.dataset.name);
  });
}

document.getElementById('search').addEventListener('input', renderList);
document.querySelectorAll('.view-toggle button').forEach(b => {
  b.addEventListener('click', () => {
    currentView = b.dataset.view;
    localStorage.setItem('document-tagger-view-v1', currentView);
    renderList();
  });
});
document.querySelectorAll('.filter').forEach(b => {
  b.addEventListener('click', () => {
    document.querySelectorAll('.filter').forEach(x => x.classList.remove('on'));
    b.classList.add('on');
    currentFilter = b.dataset.filter;
    renderList();
  });
});

function renderTypeChips() {
  const wrap = document.getElementById('type-chips');
  const caret = document.getElementById('type-caret');
  const countEl = document.getElementById('type-count');
  caret.textContent = typesExpanded ? '▾' : '▸';
  wrap.classList.toggle('show', typesExpanded);
  if (selectedTypes.size === 0) {
    countEl.textContent = 'none selected';
    countEl.classList.remove('active');
  } else {
    countEl.textContent = selectedTypes.size + ' selected';
    countEl.classList.add('active');
  }
  if (!typesExpanded) return;
  const parts = [];
  if (selectedTypes.size > 0) {
    parts.push(`<button class="clear" data-action="clear">Clear (${selectedTypes.size})</button>`);
  }
  for (const [name, count] of DATA.type_distribution) {
    const on = selectedTypes.has(name);
    parts.push(`<button data-type="${escapeHtml(name)}" class="${on ? 'on' : ''}">${escapeHtml(name)} <span class="n">${count}</span></button>`);
  }
  wrap.innerHTML = parts.join('');
  wrap.querySelectorAll('button[data-type]').forEach(b => {
    b.addEventListener('click', () => {
      const t = b.dataset.type;
      if (selectedTypes.has(t)) selectedTypes.delete(t);
      else selectedTypes.add(t);
      saveSelectedTypes();
      renderTypeChips();
      renderList();
    });
  });
  const clear = wrap.querySelector('button[data-action="clear"]');
  if (clear) clear.addEventListener('click', () => {
    selectedTypes.clear();
    saveSelectedTypes();
    renderTypeChips();
    renderList();
  });
}
document.getElementById('type-toggle').addEventListener('click', () => {
  typesExpanded = !typesExpanded;
  renderTypeChips();
});
// Initial render of type filter state (collapsed but shows count if any persisted)
renderTypeChips();

function renderOcrChips() {
  const wrap = document.getElementById('ocr-chips');
  const caret = document.getElementById('ocr-caret');
  const countEl = document.getElementById('ocr-count');
  caret.textContent = ocrExpanded ? '▾' : '▸';
  wrap.classList.toggle('show', ocrExpanded);
  if (selectedOcr.size === 0) {
    countEl.textContent = 'none selected';
    countEl.classList.remove('active');
  } else {
    countEl.textContent = selectedOcr.size + ' selected';
    countEl.classList.add('active');
  }
  if (!ocrExpanded) return;
  const parts = [];
  if (selectedOcr.size > 0) {
    parts.push(`<button class="clear" data-action="clear">Clear (${selectedOcr.size})</button>`);
  }
  for (const [name, count] of DATA.ocr_distribution) {
    const on = selectedOcr.has(name);
    parts.push(`<button data-ocr-bucket="${escapeHtml(name)}" class="${on ? 'on' : ''}">${escapeHtml(name)} <span class="n">${count}</span></button>`);
  }
  wrap.innerHTML = parts.join('');
  wrap.querySelectorAll('button[data-ocr-bucket]').forEach(b => {
    b.addEventListener('click', () => {
      const v = b.dataset.ocrBucket;
      if (selectedOcr.has(v)) selectedOcr.delete(v);
      else selectedOcr.add(v);
      saveSelectedOcr();
      renderOcrChips();
      renderList();
    });
  });
  const clear = wrap.querySelector('button[data-action="clear"]');
  if (clear) clear.addEventListener('click', () => {
    selectedOcr.clear();
    saveSelectedOcr();
    renderOcrChips();
    renderList();
  });
}
document.getElementById('ocr-toggle').addEventListener('click', () => {
  ocrExpanded = !ocrExpanded;
  renderOcrChips();
});
renderOcrChips();

function renderBranchChips() {
  const wrap = document.getElementById('branch-chips');
  const caret = document.getElementById('branch-caret');
  const countEl = document.getElementById('branch-count');
  caret.textContent = branchesExpanded ? '▾' : '▸';
  wrap.classList.toggle('show', branchesExpanded);
  if (selectedBranches.size === 0) {
    countEl.textContent = 'none selected';
    countEl.classList.remove('active');
  } else {
    countEl.textContent = selectedBranches.size + ' selected';
    countEl.classList.add('active');
  }
  if (!branchesExpanded) return;
  const parts = [];
  if (selectedBranches.size > 0) {
    parts.push(`<button class="clear" data-action="clear">Clear (${selectedBranches.size})</button>`);
  }
  for (const [name, count] of DATA.branch_distribution) {
    const on = selectedBranches.has(name);
    parts.push(`<button data-branch="${escapeHtml(name)}" class="${on ? 'on' : ''}">${escapeHtml(name)} <span class="n">${count}</span></button>`);
  }
  wrap.innerHTML = parts.join('');
  wrap.querySelectorAll('button[data-branch]').forEach(b => {
    b.addEventListener('click', () => {
      const v = b.dataset.branch;
      if (selectedBranches.has(v)) selectedBranches.delete(v);
      else selectedBranches.add(v);
      saveSelectedBranches();
      renderBranchChips();
      renderList();
    });
  });
  const clear = wrap.querySelector('button[data-action="clear"]');
  if (clear) clear.addEventListener('click', () => {
    selectedBranches.clear();
    saveSelectedBranches();
    renderBranchChips();
    renderList();
  });
}
document.getElementById('branch-toggle').addEventListener('click', () => {
  branchesExpanded = !branchesExpanded;
  renderBranchChips();
});
renderBranchChips();

function renderLanguageChips() {
  const wrap = document.getElementById('lang-chips');
  const caret = document.getElementById('lang-caret');
  const countEl = document.getElementById('lang-count');
  caret.textContent = languagesExpanded ? '▾' : '▸';
  wrap.classList.toggle('show', languagesExpanded);
  if (selectedLanguages.size === 0) {
    countEl.textContent = 'none selected';
    countEl.classList.remove('active');
  } else {
    countEl.textContent = selectedLanguages.size + ' selected';
    countEl.classList.add('active');
  }
  if (!languagesExpanded) return;
  const parts = [];
  if (selectedLanguages.size > 0) {
    parts.push(`<button class="clear" data-action="clear">Clear (${selectedLanguages.size})</button>`);
  }
  for (const [name, count] of DATA.language_distribution) {
    const on = selectedLanguages.has(name);
    parts.push(`<button data-lang="${escapeHtml(name)}" class="${on ? 'on' : ''}">${escapeHtml(name)} <span class="n">${count}</span></button>`);
  }
  wrap.innerHTML = parts.join('');
  wrap.querySelectorAll('button[data-lang]').forEach(b => {
    b.addEventListener('click', () => {
      const v = b.dataset.lang;
      if (selectedLanguages.has(v)) selectedLanguages.delete(v);
      else selectedLanguages.add(v);
      saveSelectedLanguages();
      renderLanguageChips();
      renderList();
    });
  });
  const clear = wrap.querySelector('button[data-action="clear"]');
  if (clear) clear.addEventListener('click', () => {
    selectedLanguages.clear();
    saveSelectedLanguages();
    renderLanguageChips();
    renderList();
  });
}
document.getElementById('lang-toggle').addEventListener('click', () => {
  languagesExpanded = !languagesExpanded;
  renderLanguageChips();
});
renderLanguageChips();

// Deep-link: if ?doc=<id> is in the URL, auto-select that doc.
(function initialSelection() {
  const params = new URLSearchParams(location.search);
  const wantId = params.get('doc');
  if (!wantId) return;
  const doc = DATA.docs.find(d => d.id === wantId);
  if (!doc) {
    console.warn('Deep-link target not found:', wantId);
    return;
  }
  // If the requested doc is a synthesis sidecar but the persisted view is
  // primary (or vice versa), switch to the matching view so it shows up.
  if (doc.is_synthesis && currentView !== 'sidecars') {
    currentView = 'sidecars';
    localStorage.setItem('document-tagger-view-v1', currentView);
  } else if (!doc.is_synthesis && currentView !== 'primary') {
    currentView = 'primary';
    localStorage.setItem('document-tagger-view-v1', currentView);
  }
  selectDoc(wantId);
})();
document.getElementById('clear-btn').addEventListener('click', () => {
  if (!confirm('Clear all pending edits? This cannot be undone.')) return;
  edits = {}; saveEdits();
  renderList(); renderPanel();
});
document.getElementById('export-btn').addEventListener('click', () => {
  const out = { schema: 'document-tagger/v1', exported_at: new Date().toISOString(), edits: [] };
  for (const d of DATA.docs) {
    if (!isDirty(d.id)) continue;
    const e = edits[d.id];
    const entry = { doc: d.id, sidecar: d.sidecar, places_field: d.places_field };
    for (const f of TAG_FIELDS) {
      entry[f] = { add: [...e[f].add], remove: [...e[f].remove] };
    }
    if (e.date != null) entry.date = e.date;
    if (e.ocr_confidence !== undefined) entry.ocr_confidence = e.ocr_confidence;
    out.edits.push(entry);
  }
  const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `document-tagger-changes-${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
});

renderList();
</script>
</body>
</html>
"""


def build() -> None:
    docs = collect_docs()
    people = collect_people()
    people_branches = collect_people_branches()

    # Per-doc branch set: union of branches across related_people.
    wikilink_pat = re.compile(r"^\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]$")
    branch_counts: dict[str, int] = {}
    for d in docs:
        branches: set[str] = set()
        for raw in d.get("related_people", []):
            m = wikilink_pat.match(raw.strip()) if isinstance(raw, str) else None
            if not m:
                continue
            name = m.group(1).strip()
            br = people_branches.get(name)
            if br:
                branches.add(br)
        d["branches"] = sorted(branches) if branches else []
        for b in d["branches"]:
            branch_counts[b] = branch_counts.get(b, 0) + 1
        # Also tally an explicit "(no branch)" bucket for docs with no person tags
        if not d["branches"]:
            branch_counts["(no branch)"] = branch_counts.get("(no branch)", 0) + 1
    branch_distribution = sorted(branch_counts.items(), key=lambda kv: (-kv[1], kv[0]))

    # Language distribution — flatten the multi-value languages: lists.
    lang_counts: dict[str, int] = {}
    for d in docs:
        langs = d.get("languages") or []
        if not langs:
            lang_counts["(none)"] = lang_counts.get("(none)", 0) + 1
            continue
        for lg in langs:
            lang_counts[lg] = lang_counts.get(lg, 0) + 1
    language_distribution = sorted(lang_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    # Type distribution for the filter UI — descending by count.
    type_counts: dict[str, int] = {}
    for d in docs:
        t = (d.get("type") or "").strip() or "(no type)"
        type_counts[t] = type_counts.get(t, 0) + 1
    type_distribution = sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    # OCR confidence distribution.
    ocr_counts: dict[str, int] = {}
    for d in docs:
        v = d.get("ocr_confidence") or "(not set)"
        ocr_counts[v] = ocr_counts.get(v, 0) + 1
    # Fixed order: high → medium → low → (not set) → anything else
    ocr_order = ["high", "medium", "low", "(not set)"]
    ocr_distribution = []
    for k in ocr_order:
        if k in ocr_counts:
            ocr_distribution.append((k, ocr_counts[k]))
    for k, c in sorted(ocr_counts.items()):
        if k not in ocr_order:
            ocr_distribution.append((k, c))

    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "docs": docs,
        "people": people,
        "topic_seed": TOPIC_SEED,
        "language_seed": LANGUAGE_SEED,
        "type_distribution": type_distribution,
        "ocr_distribution": ocr_distribution,
        "branch_distribution": branch_distribution,
        "language_distribution": language_distribution,
    }
    data_json = json.dumps(data, ensure_ascii=False)
    data_json_safe = data_json.replace("</script>", "<\\/script>")
    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json_safe)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(VAULT)}")
    n_paired = sum(1 for d in docs if d["translation"] or d["notes"] or d["transcription"])
    n_untagged = sum(1 for d in docs if not d["related_people"] and not d["topics"])
    print(f"  {len(docs)} documents, {n_paired} with translation/notes/transcription, "
          f"{n_untagged} untagged (no people + no topics)")
    print(f"  {len(people)} people, {len(TOPIC_SEED)} topic seeds, {len(LANGUAGE_SEED)} language seeds")


if __name__ == "__main__":
    build()
    sys.exit(0)
