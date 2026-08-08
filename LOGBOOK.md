# Logbook — Mapping Black Baltimore

Running record of research decisions, not of code changes. Code changes are in
the git history; bugs and their root causes are in SOLUTIONS.md.

---

## 2026-08-07 — Substack idea: "Grep Does Not Work on the Archive"

**Flagged by Louis as a post to write.** The strongest methodological story to
come out of this project, and it is a story about a confident, wrong negative
finding.

The argument:

Searching a digitised historical source returns nothing in two completely
different situations. Either the thing is not there, or the thing is there and
the page was never OCR'd. Those two results are indistinguishable at the
terminal, and only one of them is a finding. Treating the first as the second
is how you produce research that is confidently, precisely wrong.

It happened here, in this project, to me. I ran a keyword search for "ward"
across the 1820 federal census volume, got zero hits, and reported to Louis
that published ward-level population tables for Baltimore did not exist before
1850 — and therefore that most of the proposed exhibit panels were impossible.

The data was there the whole time. Printed page 97 of the 1820 volume carries
"AGGREGATE amount of each description of persons within the DISTRICT OF
MARYLAND," which breaks the City of Baltimore into its twelve wards, with free
coloured and enslaved counts banded by age and sex. The PDF is a pure image
scan. Measured afterwards: **151 characters of extractable text across 151
pages.** Roughly one character per page. Every search run against it was
meaningless, and produced a clean, plausible, false answer.

The correction changed the project's central finding. Black Baltimore was
**23.40% of the city in 1820**, 16.79% in 1850, and 13.13% in 1860. A forty-year
decline, invisible without that page.

Three things worth saying in the post:

1. **The failure mode is asymmetric and silent.** A search that finds something
   is self-validating. A search that finds nothing tells you nothing at all,
   and looks exactly like knowledge. This is worse in an AI workflow than a
   human one, because the machine will state the negative result fluently.

2. **The fix is old technology: the index.** Nineteenth-century statistical
   volumes are meticulously indexed and paginated, because that was the
   intended access method. Read the table of contents, find the table, turn to
   the page. Louis's phrasing, which is the better title for the section:
   *read like a human when you read old documents.*

3. **Arithmetic is the transcription check.** Printed tables carry total rows.
   Sum every column and reconcile before believing anything read off a scan. In
   this project that check caught three separate errors: a misread white female
   count (1860, ward 1), an enslaved count (1850, ward 20), and a ward total a
   subagent reported wrongly (1820, ward 8). Three independent twelve-number
   sums landing exactly on 4,357 / 10,326 / 62,738 is what made the 1820
   transcription trustworthy, not care in reading it.

There is a broader point available about digitisation as a silent filter on
what gets researched: the sources with text layers get studied, and the ones
without quietly stop existing. The 1850 Maryland census report has a text layer
(295,423 characters). The 1820, 1840 and 1860 volumes have effectively none
(151, 12 and 8 characters respectively). Nothing about that ordering reflects
historical importance. It reflects scanning batches.

---

## 2026-08-07 — Ward-level census availability, settled and then re-settled

Initially concluded from keyword searches that published ward tables existed
only for 1850 and 1860. **This was wrong for 1820** (see above). Current state:

- **1820**: yes, twelve wards, verified. Fourth Census, printed p.97.
- **1850**: yes, twenty wards, verified. Seventh Census, Table II, p.221.
- **1860**: yes, twenty wards, verified. Eighth Census, Table No.3, p.214.
- **1840**: unresolved. The compendium section held locally is the
  *manufactures* recapitulation, county-level, and is not evidence either way
  about population. The 1840 population volume is **not in census.gov's digital
  collection at all**, so this needs HathiTrust or a library copy.
- **1830**: the published Abstract of the Fifth Census is county-level by
  design, per its own preamble, which was compiled to a House resolution asking
  only for free/slave/federal population by county. The fuller 1830 volume is
  not digitised.

Decision: do not claim 1830 or 1840 are impossible. Claim only that they are
not available in the digitised federal series, which is a different and
narrower statement.

---

## 2026-08-07 — Sources adopted, with reasoning

- **AfriGeneas hand transcriptions** (Louis S. Diggs, Sr.) adopted for 1819 and
  1822 in preference to our own OCR of the same volumes. Our OCR of Keenan's
  1822 placed 8 people; the transcription places 230, from 1,061 parsed entries
  against our scan's 414. A 1810 page also exists and is not yet ingested. Six
  further years are listed on the index page (1824, 1835-36, 1845, 1847-48,
  1864, 1865-66) but their links are dead placeholders on the live site.
- **Gunby, Index of Streets and Alleys** (BCA 1993) adopted as the street-rename
  concordance. This was the single largest source of silent loss in the
  project: the streets failing to geocode were overwhelmingly the alleys the
  Black population lived on, and most had been renamed rather than demolished.
  Strawberry became Dallas, Brandy became Perry, Bottle became Dover, Happy
  became Durham, Honey became Hughes, German became Redwood.
- **HUE street file** (ICPSR 35617) chosen over modern centrelines as base
  geometry, because it is c.1930 and still carries the alleys. Modern data has
  lost them, and geocoding against it would have silently emptied the densest
  blocks while appearing to succeed.

---

## 2026-08-07 — Classification stance

Records are classified resident / business / institution by heuristic. Tuned to
**under-call**, per Louis's standing preference for false negatives over false
positives. Dropped "hall" from the institution matcher because it is a common
surname and also matched a bound-in clothing advertisement. Counts are reported
as floors, not totals, in both the writeup and the user-facing copy.
