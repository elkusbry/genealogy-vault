# Workflow: Tag Photos via the Viewer

**Triggers:** "tag photos," "photo tagger," "open the photo tagger," or any
request to interactively review who is in the photos.

## The viewer

`_tools/photo-tagger.html` is a single self-contained HTML file. It bakes
in a snapshot of every image in `media/` plus any image in `sources/` whose
sidecar `type:` is `photo`, `tombstone`, or `portrait`, along with the full
`people/` list as an autocomplete graph.

## Regenerate after adding photos or new people

```sh
python3 _scripts/taggers/build_photo_tagger.py
```

Re-run any time you've added photos to `media/`, added new people to
`people/`, or want the tagger to pick up newly-updated sidecars.

## Use

1. Open `_tools/photo-tagger.html` in a browser (double-click; loads via
   `file://`).
2. Click a photo. Existing tags appear as chips; remove with ×, add via the
   autocomplete input. Captions can be added too.
3. Edits persist in `localStorage` — refreshing won't lose them.
4. Click **Export Changes** → downloads `photo-tagger-changes-<ts>.json`
   containing only the diff.
5. Hand the JSON to the agent ("apply these photo-tag changes") OR run:
   ```sh
   python3 _scripts/taggers/apply_photo_tagger_changes.py photo-tagger-changes-*.json
   ```

## What the applier does

- Surgically edits each sidecar's `related_people:` (or `people:`) YAML
  list — add/remove only, never reorders the rest.
- Creates a fresh sidecar if the image didn't have one.
- Updates the bidirectional half: each affected person's `photos:` array
  gains or loses the image wikilink.
- Optionally upserts a `## Caption` section in the body when a caption is
  supplied.
- Idempotent — re-running the same JSON is a no-op.

## Sibling: document-tagger

A parallel tagger exists for non-photo source documents:
`_tools/document-tagger.html`, built by
`_scripts/taggers/build_document_tagger.py`. Same workflow — tri-pane UI
(doc list / main document / metadata tabs), edits persist in localStorage,
exports JSON, applies via
`_scripts/taggers/apply_document_tagger_changes.py`. Use it for batch
metadata curation across many sidecars (dates, types, related_people,
languages, topics).
