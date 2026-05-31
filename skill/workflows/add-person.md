# Workflow: Add a Person

**Triggers:** "add a person," "add my grandmother," "create a file for X,"
"parents are X and Y," "married to Z," or any new-person mention not already
in `people/`.

## Steps

1. **Decide the filename.** `Firstname Lastname (YYYY).md` where YYYY is the
   birth year. If birth year is unknown, use `Firstname Lastname.md`.

2. **Create the file** in `people/` using the template at
   `templates/person.md`. Fill all known fields; leave unknown as `""` or
   `[]` (do not delete the keys).

3. **Update bidirectional links.** Open the files of:
   - Each parent → append the new person to `children:`.
   - Each child → set the new person in `parents:`.
   - Each sibling → append the new person to `siblings:`.
   - Each spouse → append a `spouses:` entry; add the spouse to this
     person's `spouses:` too.

4. **Compute `branch`** by tracing ancestry to the tree root(s). See
   `skill/family-context.md` for branch definitions.

5. **Compute `generation`** relative to the root ancestor(s) (root =
   generation 1). Married-in spouses inherit their partner's generation.

6. **Add tags:**
   ```yaml
   tags:
     - branch/<name>
     - generation/<N>
     - gender/<male|female|other>
     - status/<living|deceased>
     - surname/<lastname>
   ```

7. **Set `confidence:`** — `proven`, `probable`, `possible`, or `uncertain`
   (see `skill/SKILL.md` § Confidence levels).

8. **Add citations** for every fact. Inline body bullets use
   `^[[[Source Name]]]`. Frontmatter `sources:` uses the array form.

9. **Add research follow-ups.** For any incomplete fields, add categorized
   `todo:` entries (`[vital-records]`, `[identity]`, etc.) and tag with
   `research/has-questions`.

10. **(Optional) Charted Roots fields.** If the vault uses the Charted Roots
    plugin, also fill `cr_id`, `cr_type`, `legacy_slug`, and the flat
    `born` / `died` / `birth_place` / `death_place` duplicates. Otherwise
    leave blank — they're harmless.

## Common pitfalls

- **Don't skip the bidirectional update.** A relationship listed on one
  side but not the other will silently desync over time.
- **Don't invent dates.** If you only have a year, write `"1885"` not
  `"1885-01-01"`. The Charted Roots plugin reads both forms.
- **Don't pick between conflicting sources.** Add a `[discrepancy]` todo
  and document both in `## Research Notes`.
