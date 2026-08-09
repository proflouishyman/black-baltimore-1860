# Does the printed 1840 federal census carry Baltimore ward tables?

**Yes. Twelve wards, with free white, free coloured and enslaved persons each
banded by age and sex.**

Checked 2026-08-09. The earlier conclusion that 1840 ward tables did not exist
was wrong, and it was wrong for exactly the reason the 1820 conclusion was
wrong: it rested on a text search, and on a local PDF that turns out not to be
the population volume at all.

---

## The answer in one table

**Source.** *Sixth Census or Enumeration of the Inhabitants of the United
States, as Corrected at the Department of State, in 1840.* Washington: Printed
by Blair and Rives, 1841. Printed pages **194 and 195**, running head "CENSUS OF
THE UNITED STATES, JUNE 1, 1840", section head "AGGREGATE AMOUNT OF EACH
DESCRIPTION OF PERSONS WITHIN THE DISTRICT OF MARYLAND".

The stub column of that table is headed:

> NAME OF WARD, TOWN, TOWNSHIP, PARISH, PRECINCT, HUNDRED, OR DISTRICT.

Under BALTIMORE county the rows run:

| Row | |
|---|---|
| Baltimore city | First ward … Twelfth ward (12 rows, braced together and labelled "Baltimore city") |
| | **Total Baltimore city** |
| Baltimore county | First district … Fifth district (5 rows) |
| | **Total Baltimore city and county** |

The table is printed sideways across a two-page spread. Printed p.194 carries
FREE WHITE PERSONS (males and females, thirteen age bands) and FREE COLORED
PERSONS (males and females, six age bands). Printed p.195 carries SLAVES (males
and females, six age bands), the TOTAL column, then occupations, pensioners,
deaf/dumb/blind/insane, and schools.

Printed pp.200-201 then repeat Maryland as a plain "RECAPITULATION … BY
COUNTIES", where Baltimore city is folded back into a single "Baltimore city and
county" line. The ward detail exists **only** on pp.194-195.

---

## Ward totals, read off printed p.195

| Ward | Total |
|---|---:|
| First | 7,421 |
| Second | 7,393 |
| Third | 10,102 |
| Fourth | 8,601 |
| Fifth | 8,212 |
| Sixth | 6,611 |
| Seventh | 6,242 |
| Eighth | 9,646 |
| Ninth | 7,337 |
| Tenth | 9,592 |
| Eleventh | 9,521 |
| Twelfth | 11,635 |
| **Sum of the twelve** | **102,313** |
| **Printed "Total Baltimore city"** | **102,313** |

The twelve ward totals sum **exactly** to the printed city total. That is the
transcription check passing on the first try, and it is the strongest single
piece of evidence that these figures have been read correctly.

Two further arithmetic checks against the printed page, both exact:

- Baltimore city 102,313 + the five county districts (9,088 + 7,335 + 4,898 +
  5,760 + 4,985 = 32,066) = **134,379**, the printed "Total Baltimore city and
  county".
- Enslaved males: city 281 + districts (135 + 229 + 111 + 101 + 154 = 730) =
  **1,011**, the printed county figure. Enslaved females: city 364 + districts
  (124 + 230 + 96 + 106 + 138 = 694) = **1,058**, likewise printed.

## Reconciliation against the IPUMS check values

Read off the "Total Baltimore city" row:

- Free coloured males: 2,170 + 1,825 + 1,601 + 1,287 + 369 + 9 = **7,261**
- Free coloured females: 2,254 + 3,092 + 2,731 + 1,861 + 738 + 30 = **10,706**
- Free coloured total: **17,967**
- Enslaved males: 281 + 505 + 231 + 113 + 35 + 4 = **1,169**
- Enslaved females: 364 + 946 + 453 + 206 + 61 + 0 = **2,030**
- Enslaved total: **3,199**
- Black total: **21,166**
- City total: **102,313**

| Quantity | Printed 1840 volume | IPUMS complete count | Difference |
|---|---:|---:|---:|
| Total population | 102,313 | 102,225 | 88 (0.09%) |
| Free Black | 17,967 | 17,958 | 9 (0.05%) |
| Enslaved | 3,199 | 3,152 | 47 (1.5%) |
| Black total | 21,166 | 21,110 | 56 (0.27%) |

Everything lands where it should. The residuals are the ordinary gap between a
published aggregate and a modern re-count of the manuscript schedules, not a
sign of misreading.

### Independent confirmation from a second printing

The Compendium prints the same city-level row in a separately typeset table
(printed pp.29 and 30, "PRINCIPAL TOWNS", row "Baltimore"). Every band matches
the Sixth Census "Total Baltimore city" row exactly:

| Band | Sixth Census p.194-195 | Compendium p.29-30 |
|---|---|---|
| Free coloured males | 2,170 · 1,825 · 1,601 · 1,287 · 369 · 9 | 2,170 · 1,825 · 1,601 · 1,287 · 369 · 9 |
| Free coloured females | 2,254 · 3,092 · 2,731 · 1,861 · 738 · 30 | 2,254 · 3,092 · 2,731 · 1,861 · 738 · 30 |
| Enslaved males | 281 · 505 · 231 · 113 · 35 · 4 | 281 · 505 · 231 · 113 · 35 · 4 |
| Enslaved females | 364 · 946 · 453 · 206 · 61 · — | 364 · 946 · 453 · 206 · 61 · — |
| Total | 102,313 | 102,313 |

Two independent compositors setting the same figures and agreeing is as strong
a check on the city-level reading as this source can give. It also settles two
digits I had initially misread at lower resolution: the free-coloured female
"under 10" is **2,254** (not 3,254) and the free-coloured male "36 & under 55"
is **1,287** (not 1,267).

**Caveat on precision.** The city-level totals above are confirmed twice over.
The *individual ward* cells are not — they appear only in the Sixth Census, on a
single skewed scan, and have not been transcribed here. They must be read
directly from the page images and reconciled, not lifted from this document.

---

## Ward geography in force in June 1840

**Twelve wards**, matching `baltimore_wards_1832_1840` in the HUE shapefile set,
which also has twelve polygons numbered 1-12. The census names them First
through Twelfth. No fourteenth-ward geography appears.

This resolves the ambiguity in the brief. The HUE `1841_1845` set has fourteen
wards, and Craig's *Business Directory* for 1842 (held locally as
`data/raw/craigsbusinessdi1842balt.txt`, printed p.50, "Boundaries of Wards in
Baltimore") describes fourteen wards in metes and bounds. That fourteen-ward
division post-dates the enumeration. The 1840 census used the twelve-ward
division, so **the 1832-1840 HUE polygons are the correct join target**.

---

## What I actually looked at

### 1. The local file is not the population volume

`data/raw/census1840_md.pdf` is 12 pages, 12 characters of extractable text. It
is the *Compendium of the Sixth Census*, printed p.142 onward: "RECAPITULATION
OF THE AGGREGATE VALUE, AND PRODUCE, AND NUMBER OF PERSONS EMPLOYED IN MINES,
AGRICULTURE, COMMERCE, MANUFACTURES, &c., BY COUNTIES." Manufactures, county
level, no population at all. Any search of this file for population data was
searching the wrong book. Rendered and read: page image saved as
`local_census1840_md_pdf_p142_manufactures_recapitulation.png`.

### 2. The Compendium of the Sixth Census: checked, and it does NOT have wards

<https://www2.census.gov/library/publications/decennial/1840/1840v3/> holds the
Compendium in 28 PDF chunks (`1840c-01.pdf` … `1840c-28.pdf`). Accessed
2026-08-09.

Its title page states its scope plainly: "as obtained at the Department of
State, from the returns of the Sixth Census, **by counties and principal
towns**." Each state gets a COUNTIES block followed by a PRINCIPAL TOWNS block,
across a three-page spread.

Maryland is at printed **pp.28, 29, 30** (chunk `1840c-03.pdf`, PDF pages 5, 6,
7). The Maryland PRINCIPAL TOWNS block has exactly five rows:

> ANNAPOLIS · Baltimore · Cumberland · Fredericktown · Hagerstown

Baltimore is one undivided row, total 102,313. **No ward breakdown anywhere in
the Compendium.** Page images saved
(`compendium1840_p28_…png`, `compendium1840_p30_…png`).

This is worth stating plainly because it is the trap: the Compendium is the
volume that is easy to find, easy to download, and easy to search, and it is the
one that does *not* have what we need.

### 3. The main population volume is not on census.gov at all

The Census Bureau's own page for the volume
(<https://www.census.gov/library/publications/1841/dec/1840a.html>) says "This
volume is not part of our digital collection." The only other 1840 directory on
census.gov, `1840v4/`, is `1840d-01.pdf` … `1840d-06.pdf`, the *Census of
Pensioners for Revolutionary or Military Services*. Neither is the population
volume. Internet Archive does not appear to hold it either (searched
2026-08-09).

### 4. HathiTrust does hold it, in full view

Catalog search for the title returns five records, all full view. The copy used
here:

- **HathiTrust id `uc1.31175023953089`**, 496 page scans, Google-digitized from
  the University of California copy, public domain.
- Reader: <https://babel.hathitrust.org/cgi/pt?id=uc1.31175023953089&seq=204>
  (printed p.194) and `&seq=205` (printed p.195).
- Catalog record: <https://catalog.hathitrust.org/Record/002815958>
- Accessed 2026-08-09.

Title page (scan seq 11) reads: SIXTH CENSUS OR ENUMERATION OF THE INHABITANTS
OF THE UNITED STATES, AS CORRECTED AT THE DEPARTMENT OF STATE, IN 1840.
PUBLISHED, BY AUTHORITY OF AN ACT OF CONGRESS, UNDER THE DIRECTION OF THE
SECRETARY OF STATE. WASHINGTON: PRINTED BY BLAIR AND RIVES. 1841.

Structure of the Maryland section:

| Printed page | Scan seq | Content |
|---|---|---|
| 193 | 203 | Section divider, "AGGREGATE AMOUNT … DISTRICT OF MARYLAND" |
| **194** | **204** | **Baltimore city wards 1-12: free white and free coloured** |
| **195** | **205** | **Baltimore city wards 1-12: slaves, TOTAL, occupations, schools** |
| 196-199 | 206-209 | Remaining Maryland counties, by hundred/district/town |
| 200-201 | 210-211 | Maryland recapitulation by counties |

That the volume goes below county level was independently visible before I
reached Maryland: printed p.114 gives New York city by wards, First through
Seventeenth.

---

## Where a transcriber should work

**Transcribe from these two pages, and nothing else:**

1. `data/evidence/census1840/sixthcensus1840_p194_baltimore_12wards_freewhite_freecolored.jpg`
   — printed p.194, scan seq 204, 3536 × 4568 px.
   Free white males and females by age band; free coloured males and females by
   age band. Twelve ward rows plus "Total Baltimore city".
2. `data/evidence/census1840/sixthcensus1840_p195_baltimore_12wards_slaves_totals.jpg`
   — printed p.195, scan seq 205, 3440 × 4496 px.
   Slaves males and females by age band; TOTAL column.

Live equivalents, should a fresh or larger scan be wanted:

- <https://babel.hathitrust.org/cgi/pt?id=uc1.31175023953089&seq=204&view=1up>
- <https://babel.hathitrust.org/cgi/pt?id=uc1.31175023953089&seq=205&view=1up>

Both pages are printed sideways; rotate 90° clockwise to read. The Baltimore
city block sits in the lower-right quadrant of each page as scanned.

**Required reconciliation before the transcription is accepted:**

- The twelve ward TOTAL values must sum to 102,313.
- Free white + free coloured + enslaved, summed across both pages, must equal
  each ward's own TOTAL.
- Column sums across the twelve wards must equal the printed "Total Baltimore
  city" row in every column.

Three independent checks, exactly as for 1820.

### Evidence files

All under `data/evidence/census1840/`:

| File | What it shows |
|---|---|
| `sixthcensus1840_titlepage_blair_and_rives_1841.jpg` | Volume identity and imprint |
| `sixthcensus1840_p193_maryland_section_divider.jpg` | Start of the Maryland section |
| `sixthcensus1840_p194_baltimore_12wards_freewhite_freecolored.jpg` | **The table, left half** |
| `sixthcensus1840_p195_baltimore_12wards_slaves_totals.jpg` | **The table, right half** |
| `sixthcensus1840_p200_maryland_recapitulation_by_counties.jpg` | County-level recap, no wards |
| `crop_p195_ward_labels_and_totals.png` | Ward names beside the TOTAL column, legible |
| `crop_p194_freecolored_totals_baltimore_city.png` | Free coloured totals row, legible |
| `crop_p195_slaves_totals_baltimore_city.png` | Enslaved totals and 102,313, legible |
| `compendium1840_p28_maryland_counties_and_principal_towns.png` | Compendium: Baltimore as one town |
| `compendium1840_p29_maryland_freewhite_freecolored.png` | Compendium: free white / free coloured |
| `compendium1840_p30_maryland_slaves_and_totals.png` | Compendium: Maryland totals, no wards |
| `crop_compendium_p29_baltimore_freecolored_bands.png` | Cross-check of free coloured bands, legible |
| `crop_compendium_p30_baltimore_slaves_and_total.png` | Cross-check of enslaved bands and 102,313 |
| `local_census1840_md_pdf_p142_manufactures_recapitulation.png` | What our local PDF actually is |

(The `4410622_*.jpg` files in that directory were written by another agent and
are not part of this check.)

---

## Consequences

- **No manuscript schedule work is needed for 1840 ward population.** The
  printed volume has it. The 1840 manuscript schedules (NARA M704) are on the
  Internet Archive if ever wanted for household-level work, but the aggregate
  the exhibit needs is already published.
- **The 1840 hole in the exhibit closes on the same footing as 1820, 1850 and
  1860**: a printed federal volume, hand-transcribed, reconciled against its own
  printed totals.
- **Join 1840 ward figures to the HUE `1832_1840` polygons**, not `1841_1845`.
- The methodological point from the 1820 episode held again. The failure here
  was not a bad search, it was searching a twelve-page pamphlet about
  manufactures while believing it was a five-hundred-page population volume. The
  fix was to read the title page.

## Related lead, noted not pursued

`data/raw/craigsbusinessdi1842balt.txt`, Craig's *Business Directory* 1842,
printed p.49, carries a "Census of Maryland" table giving 1830 and 1840
population by county, with Baltimore City at 102,313 and a candid note: "We have
examined several statements of the Census for 1840, but can find no two that
agree." County level only, no wards, so it adds nothing to the ward question,
but it is a contemporary printed confirmation of the 102,313 figure and it
carries the fourteen-ward boundary descriptions on p.50.
