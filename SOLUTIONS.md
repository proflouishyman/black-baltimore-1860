# SOLUTIONS

## [2026-08-07] - Directory entry parser dropped nearly all 1860 and 1842 records

### Problem
`scripts/parse_directory.py` returned 17 records for Wood's 1860 and 2 for
Matchett's 1842, against thousands of visible entries. 1822 parsed fine at 386.

### Root Cause
Two independent faults.

1. The line-rejoining rule required a comma immediately after the first word
   (`Ailand, Harriot,` - Keenan's 1822 style). Wood's and Matchett's put the
   comma after the *full* name (`Adams Benjamin,`), so every entry looked like
   a continuation of the previous one and the whole section collapsed into a
   handful of giant strings.
2. Section bounds for 1842 assumed `COLORED HOUSEHOLDERS` was a running page
   head, as it is in 1860. In Matchett's it appears only on the section title
   page, so first-to-last-occurrence spanned about 9 lines instead of ~5,000.

### Solution
Rejoin rule is now "starts with a capitalised word AND contains a comma",
which admits both name styles while still rejecting real continuations
(lowercase fragments like `atoga, dw 214 Montgomery`, or bare capitalised
street names like `Chesnut` that carry no comma). Section extraction gained an
optional `end` terminator regex, set to `APPENDIX` for 1842. Also added
hyphen-aware joining so `Sar-` + `atoga` becomes `Saratoga`.

Result: 4,251 / 2,724 / 414 records for 1860 / 1842 / 1822.

### Notes
1822 output is still unreliable - the Keenan OCR is much poorer and occupation
text bleeds into the address field. Needs separate work or re-OCR.

---

## [2026-08-07] - Street anchor table missed the largest streets

### Problem
`scripts/extract_anchors.py` recovered anchor tables for only 84 streets, and
the covered set had conspicuous alphabetical holes: no CHARLES, CALVERT,
BALTIMORE, GAY or EUTAW - precisely the busiest streets, where most addresses
are. It also invented street names like `DIRECTORY. 513` carrying 290 rows.

### Root Cause
Three faults, all from assuming the page layout is uniform.

1. **Column x-positions are not constant.** The table block is indented
   differently on different pages: cross-street names sit at x-offset ~325 on
   printed p.509 but ~455 on p.513. Fixed x bands therefore read the *name*
   column of some pages as the *number* column, so those streets produced no
   usable rows.
2. **Street headings are not reliably flush left.** The heading test used
   `x-offset < 60`, true on p.509 but false on p.513 where headings start at
   offset ~126. Those headings were missed, so their tables were attributed to
   whatever street was last seen.
3. The running page head (`STREET DIRECTORY. 513`) is ALL CAPS at the top of
   every page and parsed as a street heading. Section end detection also
   overshot into the appendix because it matched literal `BOUNDARIES` while the
   OCR reads `BOUNDAEIES`, pulling in an unrelated school table.

### Solution
Geometry is now derived per table block from the printed `Left. / Right.`
header row (matched loosely, since OCR renders it `Lejl.`, `Lafl.`, `Ei'/ht.`),
and house numbers are assigned to the left or right column by proximity to
those two header positions. Street headings are detected by **case** rather
than position - headings are ALL CAPS, cross-street names are Title Case.
Words above y=260 are dropped to remove the running head, and the terminator
regex was relaxed to `BOUND[AE]`.

Parser state (current street, current column geometry) now flows in true
reading order - left book column, then right book column, page after page -
because a long street's table continues across a column break without
repeating its heading.

Result: 214 streets, 1,520 anchor rows, 1,145 carrying a house number.

### Notes
Verified against the directory's own worked example: it states that 55 stands
on the N.E. corner of Charles and Saratoga, and that No. 71 therefore falls
between Saratoga and Pleasant on the right hand. The extracted CHARLES table
gives right-side 55 at Saratoga and 85 at Pleasant, so 71 does fall between
them. This is the regression test to re-run after any change here.

---

## [2026-08-07] - geopandas unusable in the anaconda base environment

### Problem
`import geopandas` fails with "A module that was compiled using NumPy 1.x
cannot be run in NumPy 2.4.6".

### Root Cause
Binary ABI break. The anaconda base env has NumPy 2.4.6 installed, but pandas
and its `_libs` extensions there were compiled against NumPy 1.x.

### Solution
Created a project-local `.venv` (system python3) with geopandas 1.0.1, shapely
2.0.7, pyproj 3.6.1, pyogrio and rapidfuzz. Deliberately did **not** repair the
anaconda base env, since many other projects under `~/coding` depend on it and
a numpy pin there could break them.

### Notes
Run project scripts with `./.venv/bin/python`, not `python3`.

---

## [2026-08-07] - Residents geocoded into open country miles from the 1860 city

### Problem
The first rendered map was zoomed almost entirely out, because scattered
residents landed miles from the historic core, in places that were farmland in
1860. Only 484 of 4,251 records placed at all, and just 29 with usable
precision.

### Root Cause
Three separate faults.

1. **Unclipped street geometry.** The HUE street file is a c.1930 survey, by
   which date arteries like Harford Avenue ran far past the 1860 city line.
   Tier-2 proportional placement spreads residents along a street's *whole*
   length, so those streets flung people into open country.
2. **`Aly` was not a recognised street-type suffix.** HUE writes alleys as
   "Pin Aly" while the directory writes "Pin al", so normalisation produced
   `PIN ALY` versus `PIN` and the two never matched. This hit alleys almost
   exclusively - precisely the addresses that matter most here.
3. `shapely.linemerge` raises rather than passing through when the union of a
   street's segments is already a single LineString.

### Solution
Street geometry is intersected with the dissolved 1846-1860 ward polygons
before anything is placed on it, so the domain is the city as it existed. Added
`ALY` to the suffix list - ordered before the bare `AL`, since alternation is
ordered and `AL` would otherwise strip only two characters and leave a stray
`Y`. Guarded the linemerge call on geometry type.

Result: 2,868 of 4,251 placed, 848 anchored between two named corners, and the
street pool correctly shrinks from 3,085 to 785 once clipped to the old city.

### Notes
Geocoding against modern centrelines was rejected for the same reason fault 2
mattered: the alleys this population lived on (Camel, Pin, Welcome, Strawberry,
Lerew's) are absent from modern data, so a modern basemap silently thins the
densest blocks while still looking like a clean result. Missing geometry is an
invisible failure here, not a visible one, which is why unmatched streets are
written to `data/work/unmatched_streets_1860.csv` rather than dropped quietly.

---

## [2026-08-07] - QGIS unusable for scripting straight from the cask

### Problem
`qgis_process` printed "Cannot find proj.db" on every invocation and
`import qgis.core` aborted the interpreter outright.

### Root Cause
The Homebrew cask installs QGIS as a self-contained app bundle that does not
export its PROJ, GDAL or QGIS prefix paths to the shell.

### Solution
`scripts/qgis_env.sh` sets `QGIS_PREFIX_PATH`, `PROJ_LIB`, `GDAL_DATA` and
`PYTHONPATH` against the bundle. It defines shell *functions* rather than
aliases, because aliases are not expanded in non-interactive shells, and
resolves the project root without `BASH_SOURCE`, which is empty under zsh and
was silently yielding the wrong directory.

### Notes
The bundle name carries its version (`QGIS-final-4_2_1.app`), so `QGIS_APP`
needs bumping after a QGIS upgrade. Most work here uses geopandas in `.venv`;
QGIS is only needed for georeferencing and final cartography.

---

## [2026-08-07] - Split streets placed people on the wrong side of the city

### Problem
An external check against the 1860 census (8 named residents looked up on
Ancestry Library Edition) found that of the three who could be confidently
identified, only one landed in the ward the census recorded. John Ashton, a
drayman at 143 N Caroline, was placed in ward 3; the census puts him in ward 7.
All three were in the `bracketed` tier - the highest-confidence placements.

### Root Cause
Two independent faults, both in how street identity and direction were handled.

1. **Direction was discarded when keying street ladders.** `norm_street`
   returns a core name and a direction, but the geocoder keyed everything by
   core alone. "CHARLES (N.)" and "CHARLES (S.)" both reduce to CHARLES, so the
   second silently overwrote the first, and the merged geometry fused both
   halves into one line. 34 street cores were affected, covering 581 of the
   2,939 placed 1860 residents and 473 of the 705 bracketed ones. An address on
   the north half could be interpolated onto the south half, putting a person
   on the wrong side of Baltimore Street.

2. **Ladders assumed distance rises with house number.** `build_ladders` kept
   only anchors whose distance along the line increased. On N Caroline the
   digitised geometry runs north to south while the numbering runs south to
   north, so distance *falls* as numbers rise: Baltimore (no. 2) sits at 2,287m
   and Chew (no. 254) at 1,291m. The filter therefore discarded every anchor
   but the first, collapsing a 10-anchor street to a single point at the wrong
   end. That is precisely how Ashton ended up in ward 3.

### Solution
Street geometry and ladders are both keyed by `(core, direction)`, and the HUE
data supports this because it names the halves separately ("N Caroline St",
"S Caroline St"). Where a directory entry gives no direction and several
ladders exist, the one whose anchor range actually brackets the house number is
chosen, rather than whichever happened to be stored last.

`build_ladders` now detects whether distance rises or falls with house number
and enforces monotonicity in whichever direction the street actually runs.

Result for 1860: bracketed placements rose from 705 to 758, `single_anchor`
fell from 246 to 97, and Ashton now lands in ward 7, matching the census. Ward
agreement on the validated sample went from 1 of 3 to 2 of 3.

### Notes
Wm. T. Aldridge (44 Ross) is still placed in ward 12 against a census ward of
20 and remains unexplained. Ross Street was renamed Druid Hill Avenue, so his
anchors resolve onto a much longer modern street; that alias is historically
correct but may be misplacing him. It could equally be a move between the
directory canvass and the June 1860 enumeration, or a different man of the same
name. Left open rather than explained away.

**This bug was only found because the placements were checked against an
independent source.** Nothing in the internal consistency of the data would
have revealed it: the ladders were monotone, the anchors were real, and the
output looked entirely plausible. Validate against something external.

---

## [2026-08-08] - Residents piled onto single coordinates

### Problem
An adversarial check of the data found that 44% of placed 1860 residents shared
a coordinate with another resident, and one point carried 75 people. Those 75
lived at genuinely different addresses - 9, 59, 70, 78, 84 and 116 South Howard
among them. On the map they rendered as a single dot, so the densest streets
appeared far thinner than they were.

### Root Cause
Two faults, both silently collapsing distinct addresses onto one point.

1. **A single anchor was treated as a location for every house number.**
   `interpolate()` returned `ladder[0][1]` whenever a street's ladder had only
   one entry, so every resident of that street received the same distance along
   the line regardless of their number. A single anchor locates one house; it
   says nothing about where any other number falls.

2. **The tier-2 number range was keyed by the raw street name, not the resolved
   one.** Residents of a renamed street pooled under the old name while the
   placement code looked up the new one. All 33 residents of Lerew's Alley were
   therefore scaled against the number range of the single person who wrote
   "Tyson", and since that range was degenerate they all received the midpoint
   of the street.

### Solution
`interpolate()` now refuses a ladder shorter than two anchors and returns None,
letting the caller fall through to proportional placement, which spreads
residents along the street and is labelled honestly as an estimate. The tier-2
span is keyed by the resolved street name so renamed streets pool correctly.

Result for 1860: placed rose 3,013 to 3,053, the misleading `single_anchor`
tier disappeared entirely (97 records redistributed), and the worst pileup fell
from 75 people to 27. Every year gained: 1845 1454->1527, 1851 1588->1631,
1868 6054->6070.

### Notes
Stacking is now 40% of points, but 995 of those 1,206 are genuinely the same
address - families and boarding houses sharing a door, which is real
co-residence rather than error. Only 211 points (7% of placements) remain
artifact, all in the `extrapolated` tier, where clamping to the end of a line is
the expected behaviour.

Found by auditing the data adversarially rather than by any test. The pipeline
reported success throughout: the ladders were valid, the anchors real, and every
resident received a coordinate.

---

## [2026-08-08] - Expired IPUMS session silently returned login pages instead of data

### Problem
Downloads from `usa.ipums.org` began producing small files that looked like
successful transfers. `data/raw/H_1820_test.csv` was 6,942 bytes and
`slave_1860_v2.dta` was 753 bytes, both with exit code 0. Nothing in the curl
output indicated a failure.

### Root Cause
The Rails session cookie extracted from the port-9444 browser expired partway
through the download campaign. Once it did, IPUMS answered file requests with
a **302 to a login page (6,942 bytes) or a 404 body (753 bytes) served with
HTTP 200 or 302**, never with an error status curl would surface. Because the
bytes arrived and the process exited zero, every automated check that looked
only at exit status passed.

The trap is that the failure is content-shaped, not status-shaped. A file whose
size is suspiciously uniform across unrelated URLs is the tell: every expired
request returned exactly 6,942 bytes.

### Solution
Verify downloads by **content**, not exit code. For each file, check that the
magic bytes match the expected format (`<stata_dta>` for .dta, a quoted CSV
header for .csv), and for CSVs that the last line has the same field count as
the header and the file ends in a newline. All six household files
(H_1790 through H_1840) passed this check at 134 fields.

Cookies are re-extracted from the live browser context on port 9444 rather than
reused from disk, since they expire on IPUMS's schedule, not ours.

### Notes
Two further findings from the same episode:

1. **`curl -C -` corrupted the file.** The IPUMS server ignores the `Range`
   header and returns the whole file, which curl then appends to the partial
   download. The result was 1,076,738,964 bytes for a 604,941,770-byte file.
   Resume is unsafe against this host; re-download from zero instead.

2. **IPUMS links a file that does not exist.** Their current page at
   `usa/slave/slave_data.shtml` links `slave_1860_v2.dta`, which returns a
   genuine 404 with valid credentials, while `slave_1850.dta` on the same path
   returns 200. The working route is the previous-version page,
   `usa/slave/slave_data_old.shtml`. Confirmed independently by Louis, who hit
   the same dead link in the browser.
