# _tools

Self-contained HTML curation interfaces, regenerated from your vault contents.

## document-tagger.html

Tri-pane UI for batch-curating source sidecars (set dates, types,
related_people, languages, topics, translation companions). Built from
the contents of `sources/` and `people/`.

## photo-tagger.html

UI for tagging photos with people via autocomplete. Built from images in
`media/` and `sources/` (whose sidecar `type:` is `photo`, `portrait`, or
`tombstone`).

## Build / regenerate

The prebuilt files in this directory are generated against the **Riverstone
demo fixture** so cloning the repo gives you a working tagger to click
through immediately. When you add your own photos and people, regenerate:

```sh
python3 _scripts/taggers/build_document_tagger.py
python3 _scripts/taggers/build_photo_tagger.py
```

Run after any of:

- Adding photos to `media/`
- Adding sources to `sources/`
- Adding people to `people/`
- Updating sidecar metadata that the tagger should reflect

Then open the resulting `.html` file in a browser (double-click — loads via
`file://`).

## Export → apply workflow

The taggers persist edits in browser `localStorage`. When you're done:

1. Click **Export Changes** → downloads a JSON diff.
2. Apply with:
   ```sh
   python3 _scripts/taggers/apply_document_tagger_changes.py <path>.json
   python3 _scripts/taggers/apply_photo_tagger_changes.py <path>.json
   ```

Both appliers are idempotent — re-running the same JSON is a no-op.
