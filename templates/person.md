---
# === CHARTED ROOTS (optional plugin compatibility)
# Leave blank if you don't use the Charted Roots Obsidian plugin.
# If you do: cr_id MUST match /^[a-z]{3}-\d{3}-[a-z]{3}-\d{3}$/
cr_id: ""              # e.g., "abc-123-def-456"
legacy_slug: ""        # human-readable slug (e.g., "jane-smith-1920") for reference
cr_type: person
born: ""               # flat duplicate of birth.date
died: ""               # flat duplicate of death.date
birth_place: ""        # flat duplicate of birth.place
death_place: ""        # flat duplicate of death.place

# === IDENTITY
name: ""
name_suffix: ""           # Jr., Sr., III, etc.
maiden_name: ""           # birth surname if changed
hebrew_name: ""
nicknames: []
gender: ""                # male | female | other

# === VITAL EVENTS
# Each event can have: date, place, source, notes
birth:
  date: ""
  place: ""               # city, state/province, country
  source: ""              # wikilink to source doc or citation
  notes: ""
death:
  date: ""
  place: ""
  cause: ""
  source: ""
  notes: ""
burial:
  date: ""
  place: ""               # cemetery name, city, state
  plot: ""                # section/lot/plot number
  source: ""
  notes: ""

# === FAMILY LINKS
# Use [[Firstname Lastname (YYYY)]] wikilink format
parents: []
siblings: []
spouses: []
#   - name: ""            # wikilink
#     marriage_date: ""
#     marriage_place: ""
#     divorce_date: ""
#     status: ""          # married | divorced | widowed | annulled
#     source: ""
children: []

# === LIFE EVENTS
# Each entry: {type, date, place, description, source, notes}
events: []
# Common types from GEDCOM:
#   religious: baptism, bar_mitzvah, bas_mitzvah, christening, confirmation, first_communion
#   education: graduation
#   civic: naturalization, immigration, emigration, census
#   career: occupation, retirement, military_service, ordination
#   legal: adoption, probate, will, name_change
#   other: any custom event
#
# Example:
#   - type: immigration
#     date: "1885"
#     place: "New York, NY"
#     from: "Bremen, Germany"
#     source: "[[Ellis Island Records]]"
#   - type: census
#     date: "1920"
#     place: "Detroit, MI"
#     source: "[[1920 US Census]]"

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
#   - institution: ""
#     degree: ""
#     year: ""

# === HEALTH
cause_of_death: ""
health_conditions: []

# === RELIGION
religion: ""

# === SOURCES & MEDIA
sources: []
#   - title: ""
#     type: ""            # see schemas/document.schema.md for canonical types
#     citation: ""
#     link: ""            # wikilink to document in sources/
photos: []
#   - file: ""            # wikilink to image in media/ or sources/
#     date: ""
#     caption: ""
obituary: ""              # link to document or inline text

# === RESEARCH
confidence: ""            # proven | probable | possible | uncertain
research_notes: ""
todo: []                  # category-prefixed: [vital-records], [identity],
                          # [relationship], [discrepancy], [document-search], [dna]

# === TREE METADATA
branch: ""
generation:
tags: []                  # branch/<name>, generation/<N>, gender/<x>,
                          # status/<living|deceased>, surname/<x>, plus user-defined
---

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

## Sources

## Stories & Memories

## Research Notes
