# Workflow: Process a Source Document

**Triggers:** A new sidecar arrives in `sources/` (typically via the
inbox-processing flow) and needs facts extracted into person files.

This workflow covers the generic case plus three specialized subtypes:
**death certificates**, **tombstones**, and **GEDCOM files**.

## Generic source

1. **Copy** the original file to `sources/` (or `media/` for pure images
   without documentary value) — this usually already happened via the inbox
   flow.

2. **Create or update the sidecar `.md`** with metadata per
   `schemas/document.schema.md`.

3. **Extract every fact** — names, dates, places, relationships, stories,
   occupations, causes of death, Hebrew names, maiden names. Put them in
   `## Extracted Facts` with citations back to the source itself.

4. **Create person files** for newly discovered people (see
   `add-person.md`).

5. **Update existing person files:**
   - Append `^[[[Source Name]]]` citations to body bullets.
   - Append to `sources:` frontmatter.
   - Fill any newly-known fields.

6. **Enrich `## Stories & Memories`** with narrative content. Direct quotes
   from the source are gold — copy them in with attribution.

7. **Update `## Research Notes`** with any open questions or discrepancies
   the source raises.

8. **Photos and images.** For **every** person in the sidecar's
   `related_people:` array, do BOTH halves of the cross-reference:
   - (a) Append the image wikilink to that person's `photos:` YAML array.
   - (b) **Embed the image in their body** with `![[filename]]` —
     typically inside `## Stories & Memories` (or `### Headstone` for
     tombstones). The YAML alone isn't enough; the body embed is what
     renders in Obsidian.
   - Add a short prose bullet near the embed with a `^[[[sidecar-name]]]`
     citation so the caption is reachable in one click.

9. **Add research follow-ups.** For incomplete or conflicting facts, add
   categorized `todo:` entries to the relevant person files and tag with
   `research/has-questions`.

## Death certificates

Scanned images (PDF or JPG). Read visually and extract:

1. **Create sidecar** named `YYYY Firstname Lastname death certificate.md`.

2. **Extract fields:**
   - Full name, death date/place, age at death.
   - Birth date/place (often present on the cert).
   - Cause (primary + contributing).
   - Occupation, marital status, spouse's name.
   - Parents (father's name + mother's maiden name).
   - Informant (often a family member — capture this).
   - Burial date/place.
   - Residence at time of death.

3. **Update person file:** fill `death:`, `burial:`, `occupation:` YAML;
   add a `## Death & Burial` section in the body.

4. **Handle discrepancies.** Death certificates are authoritative primary
   sources. If they conflict with prior data, note the conflict in
   `## Research Notes` and tend to trust the cert unless there's reason
   not to (e.g., the informant clearly didn't know the deceased well).

5. **Create new person files** for any parents or informants discovered.

6. **Flag uncertain readings** from handwriting in the `todo:` array
   (`[discrepancy] Death cert birth date unclear — could be 1885 or 1888`).

## Tombstones

1. **Create sidecar** named `Firstname Lastname tombstone.md` with
   `type: tombstone`.

2. **Read both inscriptions:**
   - English: name, dates, epithets, relationships ("beloved father of...").
   - Hebrew (if present): name, father's name, tribal affiliation (כהן /
     לוי), and the standard "פ״נ" prefix.

3. **Hebrew name format:** `"פ״נ [Name] בן/בת [Father's name]"`.

4. **Update person file:**
   - Set `hebrew_name:` YAML.
   - Add a `### Headstone` subsection inside `## Death & Burial` with the
     image embed `![[photo.jpg]]`.
   - Append to `photos:` array.

5. **Shared headstones.** Both people's files reference the same photo.

6. **Translations.** If a separate translation document exists for the
   Hebrew, create its own sidecar with `type: research` and reference it
   from the tombstone sidecar via the `translation:` companion key (see
   `translate-document.md`).

## GEDCOM files

1. **Parse** with Python (INDI + FAM records). The GEDCOM file goes in
   `sources/` like any other document.

2. **Cross-reference** against `people/` by name. Save the report to
   `_inbox/<date>-gedcom-import-report.md`:
   - Matched entries (name + birth-year overlap).
   - New people not in the vault.
   - Unmatched GEDCOM individuals.

3. **Update matches** — fill empty YAML fields ONLY. Never overwrite
   enriched data.

4. **Note discrepancies** in each affected person's `## Research Notes`.

5. **Create new person files** for unmatched GEDCOM individuals (see
   `add-person.md`).

6. **GEDCOM data is single-source.** Don't treat it as primary — it's
   secondary unless paired with citation-bearing source documents.

## RTF files

Some genealogy software exports research as RTF. Convert and embed:

```sh
textutil -convert txt -stdout "file.rtf"
```

Create a sidecar in `sources/`, copy the `.rtf` alongside, and embed with
`![[filename.rtf]]`.
