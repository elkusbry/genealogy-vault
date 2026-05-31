# Workflow: Translate a Non-English Document

**Triggers:** "translate this document," "add an English translation," or
when a primary sidecar's `languages:` is non-English and its `## Cleaned
Text` is in the original language.

The translation lives in a **companion sidecar** so the document-tagger UI
can surface it as its own tab.

## Steps

1. **Read the primary sidecar's `## Cleaned Text`** (or its body text if
   that section doesn't exist) for the foreign-language source.

2. **Create the companion** at `sources/<stem>-english-translation.md` with
   minimal frontmatter:

   ```yaml
   ---
   title: "English translation — <human description>"
   type: research
   source: "[[<stem>]]"
   languages: ["English"]
   translator: "<name or model + date>"
   covers: "<which pages / sections / scope; what is NOT translated>"
   ---
   ```

3. **Body structure** for the companion:
   - A short translator's-notes preamble (audience, register, anything
     contextual the reader needs).
   - A `## Translation` block matching the original's structure
     (blockquoted, same paragraph breaks).
   - A `## Translation Notes` section calling out loanwords,
     archaic/regional terms, idioms, or anything ambiguous in the source
     language. These notes are genealogically and historically valuable.

4. **Wire the companion into the primary.** Add a single line to the
   primary sidecar's YAML frontmatter:

   ```yaml
   translation: "<stem>-english-translation.md"
   ```

   Use the **bare filename with `.md`** form. Wikilink form
   (`[[<stem>-english-translation]]`) silently breaks the tagger — see
   `schemas/document.schema.md` § Companion files.

5. **Regenerate the document-tagger** so the Translation tab lights up:

   ```sh
   python3 _scripts/taggers/build_document_tagger.py
   ```

6. **Reload** `_tools/document-tagger.html` for that document and confirm
   the Translation tab appears as the first tab in the right pane.

## Scope discipline

Don't translate pages that live in another sidecar. If the primary's
`content:` points at a separate sidecar (e.g., a re-scan of a letter already
in the vault), translate only what's in *this* sidecar's cleaned text. Note
the scope in `covers:`.

## Multiple translations

If you need translations into multiple languages, create one companion per
language and add multiple keys to the primary — but the tagger only renders
the one named in `translation:`. Use the other languages' companions as
plain reference files in the vault.
