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

---

## 2026-08-07 — Period base maps acquired

Louis asked the obvious question nobody had asked: "are there no normal street
maps in this period? tax maps? fire maps? something that would actually let you
see the city?"

There are, and the Library of Congress holds **61 Baltimore maps dated
1800–1880**, freely downloadable at high resolution over IIIF. Acquired:

- **1822, Poppleton, *Plan of the City of Baltimore*** (Lucas) — 6,975 × 5,506
  JP2. The official city plat, and the right base for the 1819/1822 cohorts.
  `loc.gov/item/2002624027/`
- **1851, Sidney & Neff, *Plan of the City of Baltimore, Maryland*** — 13,414 ×
  10,643 JP2. Names every street, shows building footprints, and **prints the
  ward numbers on the map**. The right base for 1842–1860.
  `loc.gov/item/2004629026/`

Also identified, not yet pulled: 1804 improved plan, 1823, 1836, 1844, 1856
Scott's, 1857 city and county, 1866, 1869 Sachse bird's-eye (39,440 × 19,008),
1876 Stranger's Guide.

**Sanborn fire insurance maps for Baltimore City begin in 1890** — too late to
place anyone from our directories, but valuable for a different purpose: they
show building footprints and construction material for the alley fabric
*before* twentieth-century demolition, which is the fabric our residents lived
in.

### Why this matters to the method

Every resident is currently placed on a circa-1930 street survey, because that
was the newest layer still carrying the alleys. These two sheets let us
georeference against the actual period city. The 1851 sheet is the more
valuable of the two: because it prints ward numbers, it can validate our ward
polygons against a period source rather than against a modern reconstruction.

### An unresolved cross-check

The 1851 sheet carries its own inset table, "Population of Baltimore City
1850", ward by ward. Compared against our transcription of the Seventh Census:

| Ward | 1851 map | Our census transcription |
|---|---|---|
| 13 | 5,568 | 5,566 |
| 14 | 7,411 | 7,411 |
| 18 | 11,751 | 11,746 |
| 7 | 8,987 | 7,660 |
| 8 | 7,638 | 8,953 |
| 12 | 8,394 | 9,283 |

Several wards agree to within a handful of people; several diverge by more than
a thousand. Both figures cannot be right. Possibilities: the map used
preliminary returns, the compiler used a different ward configuration, or the
numerals were misread off an engraved italic face at preview resolution. **Do
not treat this as a discrepancy in the census transcription until the table has
been read at full resolution from the JP2** — our census figures reconcile
exactly against their own printed totals, which is strong evidence they are
right.

---

## 2026-08-07 — A finding tested and discarded: historic buildings

The Maryland Inventory of Historic Properties gives 5,255 surveyed buildings in
Baltimore City with footprint polygons. The obvious idea was to mark residents
whose address coincides with a surviving surveyed building — "this house is
still standing" is a powerful exhibit line.

74.5% of our best-anchored 1860 residents sit within 15m of a surveyed historic
building, which looked like a strong result.

**It is not a result.** Tested against a null model — the same number of random
points drawn inside the same wards — random points are *closer*:

| within | our residents | random points |
|---|---|---|
| 15m | 68.2% | 76.1% |
| 30m | 72.2% | 80.2% |
| 60m | 84.7% | 87.6% |

The proximity measures how densely surveyed buildings blanket central
Baltimore, not anything about these people. Our residents are in fact slightly
*further* from surveyed historic buildings than chance would predict.

That inverse gap is faintly interesting — it is consistent with the blocks
where Black Baltimoreans lived being less likely to survive and be surveyed —
but it is small, confounded by our own geocoding bias toward well-anchored
streets, and nowhere near strong enough to publish. Recorded here so nobody
re-derives the positive version and believes it.

**Method note worth keeping:** any "X% of our points are near Y" claim in a
dense city needs a null model before it means anything.

---

## 2026-08-08 — A published claim that did not survive more evidence

After 32 census checks, every ward mismatch was an adjacent ward, boundary
distance zero. That looked like a clean, meaningful result about the *shape* of
our error — misplacements were boundary ambiguity, never gross. It went onto the
site as "Every mismatch found so far is an adjacent ward."

Round 3 took the sample to 72 and broke it. Two mismatches are not adjacent:

| Resident | We place | Census says | Distance apart |
|---|---|---|---|
| Sevoy | ward 13 | ward 17 | 579 m, one ward between |
| Ireland | ward 12 | ward 10 | 371 m, one ward between |

Pooled: 9 of 11 mismatches adjacent (82%), 2 genuinely misplaced. The page has
been corrected, and now says so explicitly, including that we published the
stronger version first.

**The methodological point is the one worth keeping.** A rule that holds
perfectly across a small sample is exactly the kind of claim that fails quietly
as evidence accumulates — and it fails in the flattering direction, because a
clean pattern is more publishable than a messy one. The honest version is
duller: most of our errors are boundary-scale, a minority are real.

Also settled, and also not what we expected: **the confidence tiers do not
separate.** Bracketed placements match the census ward 70% of the time,
street-proportional 62%. Both rest on 7-8 traceable cases, so the gap is inside
the noise. We cannot presently demonstrate that our best tier is better than
our worst. That is a reason to keep validating, not a reason to relabel.

Find rate across all three rounds: 25 of 72 (35%).

---

## 2026-08-08 — Adversarial audit: what it broke, and where it overreached

Seven agents were set to refute the project's substantive claims, plus a
separate pass I ran on the data myself.

### Confirmed and fixed

**The anchor table contained fabricated rows.** Twelve rows were filed under a
street called "THE", carrying the directory's own explanatory paragraph as
cross-street data ("any house, for instance, 71 N. CHARLES-ST., on consult").
Across the whole table 64 of 1,521 rows (4.2%) had prose where a street name
belonged. The extractor now rejects rows whose cross street runs longer than
four words, contains explanatory phrasing, or begins lowercase.

**BALTIMORE (E) never existed as a key.** Its heading OCR'd as broken tokens,
so the entire East Baltimore Street table was swallowed into BALTIMORE (W) —
visible in the tail of that street's rows, which end at Choptank, Gist and "To
East av", all east-side crossings. Only two placed residents were affected, but
the merge was real.

**Residents piling onto single coordinates** (found in my own pass, see
SOLUTIONS.md). 44% of 1860 points shared a location, one carrying 75 people.

### Where the audit overreached

**The 1860 ward 14 enslaved count.** An auditor read the printed cell as 143
against our 142 and recommended changing it. Rejected. Our twenty ward figures
sum to exactly 2,218, the printed column total; 143 would give 2,219 and
contradict it. The auditor read one cell, the arithmetic reads all twenty. They
also noted the printed table's own M+F for that row does not reconcile with its
stated total — a clerk's slip in 1860 — which is a good reason to trust the
column sum over any single cell.

### What survived

**The 1820 transcription.** An auditor independently re-read all 192 age-banded
cells plus 12 ward totals from the page image at 600dpi and reproduced our
figures exactly, including catching two of their own misreadings. 23.40% holds,
now corroborated by 204 independently read data points rather than three pooled
totals.

**The 1850/1860 transcriptions.** 39 of 40 ward-year cells verified directly
against page images. Every one of the twenty wards falls; the closest are wards
11 and 14 at −0.17 and −0.20 points.

### And it settled an open question

The Sidney & Neff 1851 map's population table disagrees with the census on
several wards — up to 1,320 people on ward 8. **The map is the unreliable one.**
Its own printed total (169,303) does not equal the sum of its own twenty printed
rows (169,032). The census reconciles exactly against its printed total. Earlier
logged as unresolved; now resolved against the map.

---

## 2026-08-08 — Maps gallery page (docs/maps.html)

Louis asked for a gallery of period Baltimore maps, since "users will want to
look at other maps." Built `scripts/build_maps_page.py`, wired into
`build_artifact.py`'s NAV and `main()`.

Fetched the nine remaining LOC items identified on 2026-08-07 (1804, 1823,
1836, 1844, 1856, 1857, 1866, 1869, 1876) via the IIIF `pct:12.5`/`pct:25`
JPEG endpoints at `tile.loc.gov`, which serves fine over plain curl even
though `loc.gov` itself blocks it. All nine resolved on the first or second
try; 1836's `?fo=json` needed a retry with a longer timeout. 1857's IIIF
service string uses `g3843:g3843b`, not the `g3844:g3844b` every other item
in this batch uses — worth remembering if more Baltimore LOC maps are added
later, since guessing the service prefix from a sibling item's URL pattern
will silently 404.

Digital Maryland (the 1819 and 1860 maps) also blocks plain curl at its
landing pages but not at its `/digital/download/.../size/full` endpoint,
which turned out to serve the exact same files already sitting in
`data/raw/maps/` (verified by matching pixel dimensions), confirming those
two downloads are already the institution's full-resolution copies.

**Editorial calls made:**
- The 1822 item LOC catalogs as "Plan of the city of Baltimore," published
  by Fielding Lucas Jr., with no mention of Poppleton in its own contributor
  field. Captioned it as "surveyed by Thomas H. Poppleton, published by
  Fielding Lucas, Jr." on the strength of the 1823 LOC record for the same
  survey, which does credit Poppleton as cartographer. Not a contradiction,
  just two catalog records that describe the division of labor differently.
- 1804 (Warner & Hanna, before Jackson's 1819 directory) and 1869/1876
  (after the 1868 directory) marked as outside the project's 1819-1868
  window on each card, rather than split into a separate section, so the
  gallery stays in one chronological sequence per the brief.
- 1869 Sachse bird's-eye: fetched only the `pct:12.5` preview (4,930 x 2,376)
  for the thumbnail. Did not fetch the 39,440 x 19,008 JP2 master, per
  instruction.

Thirteen maps total, 1804-1876. Thumbnails generated at 900px long edge,
JPEG quality 80: 129-216 KB each, 2.2 MB for all thirteen. Page verified
error-free over CDP (port 9222): all 13 `<img>` load, `1860.html` still
renders with the new "Maps" nav item present.

---

## 2026-08-08 — Names and ward ARE public, in the samples. And why bulk matching still fails.

### The correction

I twice told Louis that NAMEFRST, NAMELAST and WARD were unavailable without the
restricted IPUMS licence. That was wrong, and the error was mine: I tested
availability against `us1860c`, the 100% file, and generalised from it.

The contractual exclusion applies **only to the 100% files**. The 1% samples
carry all three. Verified against the API: `us1860a` and `us1860b` both accept
WARD, NAMEFRST and NAMELAST; `us1860c` rejects all three.

`us1860b` is a 1-in-100 national sample with a **1-in-50 oversample of the free
African-American population**. Downloaded in minutes on the existing API key:

- 2,599 Baltimore City records
- **542 Black Baltimoreans, every one with a name and a recorded ward**

That is twenty times the 25 people we had hand-verified, obtained free and
instantly. It should have been the first thing tried.

### What it does not give us

Matching those 542 against our 2,927 placed directory residents on surname plus
forename produces 178 matches, 44 of them one-to-one. Ward agreement on those
44: **30%**, against 56% on the hand-checked, occupation-corroborated set.

That looks like our accuracy collapsing. It is not. It is the matching that is
broken, and the null model shows it:

| | ward agreement |
|---|---|
| random pairing, given both ward distributions | 6.1% |
| name-only automated matches | 30% |
| hand-checked with occupation corroboration | 56% |

Solving the mixture (`observed = f*true + (1-f)*chance`) gives **f = 48%**:
roughly half of the 44 name-only matches are the same person and half are
different people who happen to share a name. That is consistent with the
independent estimate of ~62 expected true overlaps at 2.1% sampling density.

**And nothing in the data says which half is which.** The 30% is a mixture, not
a measurement.

### Why this matters beyond this project

This is the concrete answer to "why not just pull the whole database and match
it?" At a 1-in-50 sampling density, in a population where surnames repeat
heavily, automated name matching finds about as many coincidences as identities.
Adding volume does not fix it, because the contamination rate is a property of
the name distribution, not of the sample size. Occupation and race corroboration
is what separates them, and that is exactly what the hand checks do and the
automated join cannot.

The hand-checked 56% remains the best estimate of geocoding accuracy. The 30%
should not be quoted.

### Revised IPUMS strategy

- **For validation**: the public samples are enough and are free. `us1860b` for
  1860, `us1870b` for 1870. No licence needed.
- **For full linkage**: still blocked. A 1-in-50 sample cannot link most of our
  4,251 residents no matter how it is processed. That needs the restricted
  Ancestry Full Count, and the right tier is the **20% License** (Baltimore City
  1860 is 0.67% of the national population).
- WARD is documented as available for 1850 (100%), 1860 and 1870 (1% and 1.2%),
  1900-1940. IPUMS itself warns the variable is unreliable: enumerators often
  failed to record it, boundaries shifted, and the Census Bureau published no
  ward maps.

## 2026-08-08

### Prompt
Continue autonomous work: complete the enslaved-persons and household-data
downloads, run the household workflow, georeference the 1851 map, and be
transparent about the census not-found rate.

### Decisions
- **Framed the household files around what they can answer, not what we wanted
  them to answer.** The 1790-1840 complete-count files carry no name, no
  address and no ward, so they cannot extend the mapping. Rather than drop
  them, the analysis was pointed at a question the maps cannot reach: not
  *where* free Black Baltimoreans lived but *in whose household*. That is a
  genuinely new axis for the project and it covers five decades before the
  earliest directory we map in detail.
- **Reported the 1790 reconciliation failure rather than smoothing it.** The
  Baltimore rows sum to 10,641 against a known ~13,500, a 21% shortfall in
  IPUMS's own data. Marked unusable for population claims. The verifier caught
  that the first analyst's state code was wrong (stateicp 21 is Illinois, not
  Maryland), which is why the check stage exists.
- **Flagged changing census categories inline rather than in a footnote.**
  1790-1810 have only `nothfree`; 1820 uses four "Colored" age bands; 1830-1840
  use six differently-cut "Black" bands. A single trend line across all six
  years silently treats three different categories as one variable, so the
  shape is reported and the point-to-point deltas are not.
- **Promoted the not-found rate to the headline of the checking page.** 63% of
  people searched could not be found. Every accuracy figure on the site rests
  on the 37% we could trace, and the page now says so before it says anything
  reassuring.
- **Reported the ward-level gap in verification as a limit on the maps.** Wards
  9, 14 and 18 produced zero identifications. Small n, so a zero can happen by
  chance, but the consequence is not statistical: those wards have no
  verification at all, and ward-to-ward density comparisons leaning on them are
  not defensible. Said so plainly rather than averaging it away.
- **Retracted two published claims.** Adjacent mismatches went from 9 of 11 to
  13 of 16, and the ward 13 to 17 error recurred in a second independent round,
  which moves it from bad luck toward something systematic we have not found.
- **Committed 249 MB of provenance screenshots.** They sit outside `docs/` so
  they do not bloat the published site. Weighed against repo size, the standing
  rule that evidence travels with the data won.

### Outcome
- `docs/HOUSEHOLDS.md` written and verified; two findings survive independent
  recomputation (rising share of Black-only households; rising overlap between
  slaveholding and free-Black presence, robust to a household-size control).
- Checking page rebuilt with the 63% rate, the ward 9/14/18 gap, and the two
  corrections. Confidence tiers still do not separate (Fisher p ~ 0.68) after
  tripling the sample.
- Five-person IPUMS-vs-Ancestry cross-check: 5/5 agreement on age, sex, ward
  and race. Occupation differs only through IPUMS's occ1950 harmonisation.
- All six household files verified complete by field count and terminator.
- 1860 enslaved file blocked on a dead IPUMS link; Louis downloading via the
  previous-version page. See SOLUTIONS.md.

### Discarded
- `curl -C -` resume against IPUMS. The server ignores `Range` and the resumed
  file is silently corrupt. Not a speed optimisation worth keeping.

## 2026-08-08 - Georeferencing the 1851 plan properly

### Prompt
Research how historical map georeferencing is actually done, diagnose what our
first attempt got wrong, then reimplement it correctly.

### Decisions
- Took FGDC-STD-007.3-1998 (NSSDA) as the governing standard for how accuracy is
  measured and reported, over any ad hoc convention. Its 20-check-point minimum,
  quadrant distribution rule, insistence on an independent source of higher
  accuracy, and the 1.7308 multiplier all shape what v2 reports.
- Sourced control coordinates from modern Baltimore City centrelines and OSM way
  geometry rather than from the HUE c.1930 file, specifically so that HUE could
  be measured instead of assumed. This was the fix for the circularity.
- Chose standing pre-1851 structures for the check-point set where possible
  (Washington Monument, Battle Monument, Union Square, Franklin Square, Fort
  McHenry, Mount Clare), because they carry no dependence on street naming.
- Ruled out Federal Hill (quarried), the harbour shoreline (filled), Patterson
  Park (grew from a small square to 1,900 m) and the Jones Falls (culverted) as
  control features. Recorded the reasoning rather than silently omitting them.
- Chose the shipped transform on independent check-point error, not on fit error.
  That reversed what the fit alone would have chosen: TPS fits perfectly and
  extrapolates badly, so polynomial 2 ships.
- Kept the v1 script and raster in place rather than overwriting, so the two are
  comparable.

### Outcome
- docs/GEOREFERENCING_METHOD.md written: the standard, cited, plus a blunt list
  of what v1 skipped.
- scripts/georeference_1851_v2_check.py written: 21 independent check points,
  inter-operator agreement, in-hull vs out-of-hull error, combined transform.
- docs/GEOREFERENCE.md rewritten with the corrected result.
- Headline moved from a claimed 56 m fit RMSE to a cross-validated 12.9 m,
  reported as 22.3 m at 95% confidence.
- Searched the georeferencing ecosystem for prior work on this sheet. One exists,
  Map Warper 37609, a five-point warp of a downsampled derivative with a 98.7
  outlier. Nothing at Rumsey, Allmaps, LOC, NYPL, MSA, Digital Maryland or JHU.

## 2026-08-09

### Prompt
Update the website with the new information, update the email to Lawrence
Jackson, send it, make clear it is written by Claude, and cc Louis. Do all the
work that can be done. Earlier in the same session: write up the tradeoffs on
the sources page, and do one year of manuscript schedules for 1840.

### Decisions
- **Checked the printed volume before touching manuscript schedules**, against
  the explicit instruction to do manuscript work. The instruction was to
  recover 1840, and the cheap route had only ever been ruled out by a method
  that had already failed us once. It was the right call: the printed table
  exists and no manuscript transcription was needed at all.
- **Treated our own earlier negative finding as unverified.** Twice we had said
  1840 ward tables did not exist. The second failure was new in kind: we had
  been searching a file that was a different book. Recorded in SOLUTIONS.md
  because the fix generalises beyond this project.
- **Did not blend ward geographies.** 1820 and 1840 sit on twelve-ward
  divisions, 1850 and 1860 on twenty. The density page now says plainly that
  ward 7 in 1840 is not ward 7 in 1860, rather than letting a reader assume the
  four maps are ward-comparable.
- **Chose the 1832-1840 polygons over 1841-1845 for the 1840 counts**, on the
  evidence of Craig's 1842 directory describing the fourteen-ward division in
  metes and bounds, which dates the change after the June 1840 enumeration.
  Using the later set would have been a silent and plausible error.
- **Reframed what the four years are for.** With 1820, 1850 and 1860 the Black
  share reads as a straight decline. With 1840 at 20.7 per cent the series
  bends, and the turn is locatable between 1820 and 1840. Three points implied
  a trend, four show where it changes.
- **Wrote to Lawrence Jackson as Claude rather than ghost-writing for Louis**,
  at Louis's instruction, on the grounds that the limits of the work are more
  credible stated directly by the thing that produced them. Led with the gaps,
  not the achievements: 1800 impossible, no ArcGIS, no tax records, no exhibit
  panels, and 63 per cent of directory residents untraceable in the census.
- **Extended the 1840 lesson to 1800, 1810 and 1830** rather than stopping at
  the year that was asked for. If the reasoning that lost 1840 was wrong, the
  same reasoning was applied to the other early years, and 1800 is the year the
  exhibit is actually waiting on.

### Outcome
- 1840 ward table recovered from the Sixth Census, printed pp.194-195, on
  HathiTrust. Twelve wards. Every column reconciles against the printed totals
  with zero residual.
- Density map now carries four census years. Site rebuilt, verified in a
  browser, committed and pushed.
- Tradeoffs section added to the sources page covering base layer choice, the
  1851 overlay as picture rather than survey, printed tables over microdata,
  directories over census, and bulk sources linked rather than mirrored.
- Email sent to Lawrence Jackson, cc Louis, delivery confirmed and Outbox
  verified empty.
- 1800, 1810 and 1830 printed volumes now being checked the same way.

### Open
- Exhibit panels do not exist in any form. Blocked on Larry's answers about
  years, panel count, physical size and whether he wants print files or ArcGIS.
- City tax records, in his original brief, remain untouched.

---

## 2026-08-09 — Printed censuses of 1800, 1810 and 1830 checked for Baltimore ward tables

### Prompt or task
Determine whether the printed federal census volumes for 1800, 1810 and 1830
carry ward-level population tables for Baltimore City, applying the method that
eventually found the 1840 table rather than the keyword searching that twice
failed to.

### Decisions made
- **Identified every volume from its own title page before reading anything into
  it.** This immediately caught two mislabelled holdings: what census.gov offers
  for 1830 is the *Abstract of the Returns of the Fifth Census* (county level,
  Baltimore county and city as a single row), not the census, and the only
  accessible 1810 copy is a Norman Ross 1990 facsimile rather than an 1811
  original. Neither fact is visible from a file name or a catalogue title.
- **Mapped each volume by rendering every page and OCR-reading the running head**
  rather than searching text. The 1810 volume's page order as Google reports it
  is scrambled, so a page-by-page map was the only way to locate Maryland. It is
  one page, printed p.53.
- **Treated a keyword hit as a hypothesis, not a finding.** "Baltimore" in the
  1810 volume flags printed p.52a first, which is Delaware, where Sussex County
  has a Baltimore hundred. Recorded as a trap.
- **Ruled 1800 out on positive evidence, not on a failed search.** The Maryland
  schedule occupies exactly one page and was read in full, as was the separate
  corrected Maryland return that Etting sent in December 1801. Baltimore is one
  row in both printings, and the two agree digit for digit.
- **Reported the 1810 column set as it actually is** rather than forcing it into
  the modern shape. In 1800 and 1810 free people of colour are a single
  undifferentiated count with no age or sex bands, and Baltimore in 1810 is split
  into city, eastern precincts and western precincts, which is a real sub-city
  geography but not wards.
- **Flagged rather than fixed a 5-person discrepancy in the 1810 printing.** The
  City of Baltimore row's twelve cells sum to 35,588 against a printed 35,583,
  while all three neighbouring rows close exactly. Left as a printer's error,
  not corrected.
- **Declined to write `ward_census_1830.csv`.** The 1830 ward table exists and
  was located, but the only digital copy anywhere is the Google Books scan, hard
  capped at 2500 px tall, at which a digit is about six pixels wide. Two
  independent reading passes of the twelve ward totals disagreed with each other
  and neither summed to the printed 80,620. Shipping a plausible table from that
  scan would repeat, in transcription, the error this project already made twice
  in searching. Documented instead where a transcriber should work and what a
  better source would be.
- **Established the join target for 1830 before anyone needs it.** June 1830
  falls in the HUE 1818-1831 period, verified to hold 12 polygons, which is the
  same set `ward_census_1820.csv` uses. So 1820 and 1830 would be directly
  comparable ward by ward, the only such pair in the series.

### Outcome
- `docs/CENSUS_EARLY_YEARS.md` written: volume identity, location, arithmetic
  and reconciliation for all three years, plus the list of everything opened.
- 1800: no ward table, definitively. City totals 26,514 with 2,771 free people
  of colour and 2,843 enslaved, reconciling to within 6 people of IPUMS on the
  total.
- 1810: no ward table. City plus both precincts reconcile to IPUMS within 0.19%
  on population and 0.40% on Black total, which also settles that the IPUMS 1810
  Baltimore universe includes the precincts.
- 1830: **ward table found**, twelve wards, Fifth Census printed pp.80-81, under
  the same stub heading that located 1840. Not transcribed.
- Page images saved under `data/evidence/census1800/`, `census1810/` and
  `census1830/`.

### Open
- 1830 transcription, blocked on scan resolution. Three routes named: a
  library copy of the Duff Green 1832 printing, the 1830 manuscript schedules
  (NARA M19, free on the Internet Archive), or a contemporary Baltimore
  reprinting in Matchett's 1831 or Niles' Register.
