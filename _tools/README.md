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

Once you've added your own photos and people, the build scripts produce
the tagger HTMLs into THIS directory (`_tools/`), with paths that point
at `../sources/` and `../media/` (i.e., your vault root).

Demo-flavored prebuilt taggers (against the Riverstone family) live at
`demo/_tools/document-tagger.html` and `demo/_tools/photo-tagger.html`,
where their relative paths resolve correctly into `demo/sources/` and
`demo/media/`. Open one of those to see the tagger working out of the
box; build your own into this directory after `install.sh`:

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
