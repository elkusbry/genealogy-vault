# Person File Schema

Every file in `people/` follows this schema. The full annotated template lives
at `templates/person.md`.

## Filename

`Firstname Lastname (Birth Year).md` — birth year disambiguates duplicates.

If birth year is unknown: `Firstname Lastname.md`. Some filenames retain old
birth years for consistency even after later sources correct them — the
authoritative date is always in YAML `birth.date`.

## Frontmatter

```yaml
---
# === CHARTED ROOTS (optional plugin compatibility — see Optional fields below)
cr_id: ""               # match /^[a-z]{3}-\d{3}-[a-z]{3}-\d{3}$/ e.g. "abc-123-def-456"
legacy_slug: ""         # human-readable slug for cross-reference
cr_type: person
born: ""                # flat duplicate of birth.date
died: ""                # flat duplicate of death.date
birth_place: ""         # flat duplicate of birth.place
death_place: ""         # flat duplicate of death.place

# === IDENTITY
name: ""
name_suffix: ""         # Jr., Sr., III
maiden_name: ""
hebrew_name: ""
nicknames: []
gender: ""              # male | female | other

# === VITAL EVENTS
birth:
  date: ""              # YYYY-MM-DD or YYYY
  place: ""             # City, State/Province, Country
  source: ""            # wikilink to source sidecar
  notes: ""
death:
  date: ""
  place: ""
  cause: ""
  source: ""
  notes: ""
burial:
  date: ""
  place: ""             # cemetery, city, state
  plot: ""
  source: ""
  notes: ""

# === FAMILY LINKS — use [[Firstname Lastname (YYYY)]] wikilinks
parents: []
siblings: []
spouses: []
#   - name: ""
#     marriage_date: ""
#     marriage_place: ""
#     divorce_date: ""
#     status: ""        # married | divorced | widowed | annulled
#     source: ""
children: []

# === LIFE EVENTS — each entry: {type, date, place, description, source, notes}
events: []
# Common types: baptism, bar_mitzvah, christening, confirmation, graduation,
#   naturalization, immigration, emigration, census, occupation, retirement,
#   military_service, ordination, adoption, probate, will, name_change.

# === RESIDENCES
residences: []
#   - address: ""
#     city: ""
#     state: ""
#     country: ""
#     from: ""
#     to: ""
#     source: ""
#     notes: ""

# === EDUCATION & CAREER
occupation: ""
education: []

# === HEALTH
cause_of_death: ""
health_conditions: []

# === RELIGION
religion: ""

# === SOURCES & MEDIA
sources: []
photos: []
obituary: ""

# === RESEARCH
confidence: ""          # proven | probable | possible | uncertain
research_notes: ""
todo: []                # categorized: [vital-records], [identity], [relationship],
                        #              [discrepancy], [document-search], [dna]

# === TREE METADATA
branch: ""
generation:
tags: []                # branch/name, generation/N, gender/X, status/Y,
                        # surname/X, plus user-defined
---
```

## Body sections (in order)

```markdown
# {{name}}

**Born:**
**Died:**
**Hebrew Name:**
**Branch:**
**Generation:**

## Family

**Spouse:**

### Children

### Siblings

## Parents

## Life Events

## Residences

## Education & Career

## Health

## Death & Burial

### Headstone
(tombstone photo embed goes here)

## Sources

## Stories & Memories

## Research Notes
```

## Optional fields: Charted Roots compatibility

The flat `cr_id`, `cr_type`, `born`, `died`, `birth_place`, `death_place`
fields and parallel `parents_id` / `children_id` / `siblings_id` /
`spouses_id` arrays are for the [Charted
Roots](https://github.com/skiqh/charted-roots) Obsidian plugin. If you don't
use Charted Roots, leave them blank — they're harmless.

`cr_id` must match `/^[a-z]{3}-\d{3}-[a-z]{3}-\d{3}$/` (e.g.,
`"abc-123-def-456"`). The plugin rejects human-readable slugs.

When using Charted Roots:

- `born` mirrors `birth.date`, `birth_place` mirrors `birth.place`, etc.
- Add the person's relationships via the wikilink arrays
  (`parents:`, `children:`, etc.) — the human-readable view.
- The `_id` arrays drive Charted Roots' tree rendering. A future migration
  may add a helper script to keep them in sync; for now, maintain manually
  or skip the plugin.

## Citation pattern (in body)

```markdown
- **1936** — Family moved to Vienna. ^[[[1937 Family Letter from Vienna]]]
```

The `^[[[...]]]` is an Obsidian inline footnote whose content is itself a
wikilink. Renders as a clickable footnote in reading view.

## Bidirectional rule

If person A's file lists B as a child, B's file **must** list A as a parent.
Same for spouses ↔ spouses and siblings ↔ siblings. Always update both files.

## Confidence

```yaml
confidence: ""          # proven | probable | possible | uncertain
```

When a fact conflicts across sources, do not silently pick one. Add a
`[discrepancy]` entry to `todo:` and document both values in `## Research
Notes`.
