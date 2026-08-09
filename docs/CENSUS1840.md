# 1840 Baltimore City population by ward

**Status: RECOVERED.** The 1840 hole in the ward series is closed. African
American population by ward for 1840 now exists on exactly the same footing as
1820, 1850 and 1860: a printed federal census volume, hand-transcribed from
page images, reconciled against its own printed totals.

Output: `data/work/ward_census_1840.csv` — 12 rows, columns identical to
`ward_census_1820.csv` and `ward_census_1860.csv`.

Compiled 2026-08-09.

---

## 1. What route worked

**The printed Sixth Census population volume of 1841.** The Baltimore ward
table is on printed pages 194–195.

Two routes were run in parallel and both succeeded. The printed volume is the
one the numbers come from. The manuscript route is documented because it
independently corroborates the result and because its negative findings are
worth not repeating.

### Route A — printed volume (USED)

*Sixth Census or Enumeration of the Inhabitants of the United States, as
Corrected at the Department of State, in 1840.* Washington: Printed by Blair
and Rives, 1841. Maryland section, printed pp.193–201; the Baltimore ward
table on **printed pp.194–195**.

Why it was previously believed absent, and why that was wrong twice over:

1. **The local file is the wrong book.** `data/raw/census1840_md.pdf` is not the
   population volume at all. It is 12 pages of the *Compendium* of the Sixth
   Census, printed p.142 onward: "Recapitulation of the Aggregate Value, and
   Produce, and Number of Persons Employed in Mines, Agriculture, Commerce,
   Manufactures, &c., by Counties." Manufactures, county level, no population.
   It yields **12 characters** of extractable text for the entire file. Every
   search ever run against it was searching the wrong volume, and was
   meaningless besides.
2. **The easy-to-find volume is the wrong volume.** The *Compendium* is what
   census.gov actually hosts, it is titled "by Counties and Principal Towns",
   and its Maryland PRINCIPAL TOWNS block has exactly five rows — Annapolis,
   Baltimore, Cumberland, Fredericktown, Hagerstown. **Baltimore is one
   undivided row.** The Compendium has no ward breakdown. This is the trap: it
   is the volume you find first and it does not have what is needed.
3. The Census Bureau's own page for the population volume states plainly:
   "This volume is not part of our digital collection." The population volume
   had to be found elsewhere. It is on HathiTrust in full view.

This is the 1820 failure mode repeating with a new wrinkle. In 1820 the search
failed because the PDF was an image scan. Here the search failed because it was
run against the wrong book entirely. **The table was found by reading the
volume's structure the way a person using the book would** — title page,
section heads, then Maryland — and by confirming before reaching Maryland that
this volume goes below county level (printed p.114 gives New York City by
wards, First through Seventeenth).

### Route B — manuscript schedules (corroborating, not used for figures)

NARA microfilm M704, rolls 158–161 (Baltimore City), on Ancestry Library
Edition collection 8057, image sequence 4410622, frames 00001–01261. The
enumerators' end-of-ward **recapitulation and signed abstract leaves** exist for
all twelve wards, which would have made this route cheap too (~25 images, not
17,118 households).

Two findings from this route are load-bearing:

- **It independently confirms ward 1 = 7,421**, from the enumerator's own
  recapitulation grand total, matching the printed volume exactly. Ward 12's
  signed abstract (enumerator Joseph Brown, sworn 24 Sept 1840) gives White
  Males 4,467 / White Females 4,938 / Col'd Free M 806 / Col'd Free F 1,138 /
  Slave M 114 / Slave F 190 / Total 11,653. Note this is 11,653 against the
  printed 11,635 — a digit transposition somewhere between the manuscript
  abstract and the printed volume. See §6.
- **It confirms the 1820 lesson a third time.** Eighteen frames carry no ward
  attribution in Ancestry's index, and every one of them is a recapitulation
  page. Recapitulations have no personal names, so they are invisible to any
  name or keyword search. They were found by noticing that indexed image counts
  per ward did not add up to the physical frame ranges, then opening the gaps
  and *looking*.

### Dead ends, recorded so nobody repeats them

| Tried | Result |
|---|---|
| `data/raw/census1840_md.pdf` | Compendium manufactures recapitulation. Not population. 12 chars of text. |
| census.gov 1840v3 (28 PDF chunks) | The Compendium. County + principal towns only. **No wards.** |
| census.gov 1840v4 (`1840d-01..06`) | Census of *Pensioners*, not population. |
| census.gov page for the population volume | "This volume is not part of our digital collection." |
| Internet Archive advanced search | No copy of the main population volume (it does hold M704 manuscripts). |
| `data/raw/H_1840.csv` (IPUMS complete count) | **No ward, ED or page variable.** Cannot be aggregated to ward at all. |
| Any text search of any 1840 scan | Meaningless. All are image scans. |

---

## 2. Ward count — twelve, established not assumed

**Baltimore City had twelve wards at the June 1840 enumeration.** Four
independent confirmations:

1. The printed census names them First through Twelfth ward, braced under
   "Baltimore city", then "Total Baltimore city".
2. The microfilm's own volume target reads "6TH CENSUS 1840 MARYLAND VOL·2
   BALTIMORE CITY WARDS 1-6"; vol. 3 is wards 7–12. There is no volume for
   wards 13–14. Ancestry's browse hierarchy returns Wards 1–12 and nothing for
   13 or 14.
3. Matchett's *Baltimore Director* 1837: "The City is divided into twelve
   wards."
4. The fourteen-ward division post-dates the enumeration. Craig's Business
   Directory 1842 (`data/raw/craigsbusinessdi1842balt.txt`, printed p.50)
   describes 14 wards in metes and bounds; the enabling Ordinance No. 18
   appears in the 1842 Matchett's appendix, whose city-government list is headed
   by Solomon Hillen Jr., mayor from 1842.

**Join to `baltimore_wards_1832_1840.shp`** — verified to contain exactly 12
features with `Ward_Num` 1–12, matching the CSV keys. **Not** the 1841–1845 set
(verified 14 features).

*Exact effective date of the 14-ward ordinance was not established — only that
it postdates June 1840.*

---

## 3. What was transcribed

All **38 printed columns for all 12 wards — 456 cells** — read off two page
images and nothing else:

- `data/evidence/census1840/sixthcensus1840_p194_baltimore_12wards_freewhite_freecolored.jpg` (3536 × 4568) — free white M/F (13 age bands each), free coloured M/F (6 bands each)
- `data/evidence/census1840/sixthcensus1840_p195_baltimore_12wards_slaves_totals.jpg` (3440 × 4496) — slaves M/F (6 bands each), then the TOTAL column

The full age-band detail was read deliberately rather than just the four
race/sex subtotals, **so that both a row check and a column check would be
available**. The four race/sex figures in the CSV are computed by summing the
transcribed bands. None was read off the page directly.

Both tables are printed sideways and the scan is skewed, so numeric columns
drift downward relative to the ward-name stub as you move right. Row identity
was fixed by ordinal position within each ruled column and then confirmed
arithmetically (check b), which fails if any value lands on the wrong ward.

The complete 456-cell band-level transcription is preserved in
`docs/census1840_transcription.md`, appendix, so the raw reading is auditable
without re-opening the scans.

---

## 4. The ward table

| ward | white | free coloured | enslaved | **Black total** | aggregate | **Black %** |
|---|---|---|---|---|---|---|
| 1 | 6,020 | 1,220 | 181 | 1,401 | 7,421 | 18.88 |
| 2 | 6,035 | 1,229 | 129 | 1,358 | 7,393 | 18.37 |
| 3 | 7,503 | 2,415 | 184 | **2,599** | 10,102 | **25.73** |
| 4 | 7,205 | 1,286 | 110 | 1,396 | 8,601 | 16.23 |
| 5 | 6,894 | 933 | 385 | 1,318 | 8,212 | 16.05 |
| 6 | 5,628 | 727 | 256 | 983 | 6,611 | **14.87** |
| 7 | 4,756 | 1,058 | **428** | 1,486 | 6,242 | 23.81 |
| 8 | 7,322 | 2,031 | 293 | 2,324 | 9,646 | 24.09 |
| 9 | 5,676 | 1,292 | 369 | 1,661 | 7,337 | 22.64 |
| 10 | 7,372 | 1,991 | 229 | 2,220 | 9,592 | 23.14 |
| 11 | 7,340 | 1,842 | 339 | 2,181 | 9,521 | 22.91 |
| 12 | 9,396 | 1,943 | 296 | 2,239 | 11,635 | 19.24 |
| **city** | **81,147** | **17,967** | **3,199** | **21,166** | **102,313** | **20.69** |

For the exhibit: **ward 3 is the densest Black ward at 25.7%**, then 8, 7 and
10. Wards 6, 5 and 4 are the whitest. Free and enslaved populations cluster
*differently* — ward 7 has the most enslaved people in the city (428) but only
the fourth-largest free coloured population, while ward 3 has the largest free
coloured population (2,415) and comparatively few enslaved (184). The
free/enslaved distinction is not a single "Black Baltimore" gradient and the
map should not flatten it.

---

## 5. Reconciliation arithmetic

### Internal checks against the printed volume — all pass, nothing adjusted

**(a) Ward TOTAL column sums to the printed city total.**
7,421 + 7,393 + 10,102 + 8,601 + 8,212 + 6,611 + 6,242 + 9,646 + 7,337 + 9,592
+ 9,521 + 11,635 = **102,313** = printed "Total Baltimore city". ✓

**(b) Every ward row closes against its own printed TOTAL.**
For each ward, free white + free coloured + enslaved summed across all 38 bands
equals that ward's printed TOTAL. **12 of 12.** ✓

**(c) Every column closes against the printed city row.**
All 38 columns sum down the twelve wards to the printed "Total Baltimore city"
figure. **38 of 38.** ✓

(b) and (c) are genuine double-entry. (c) catches a misread digit; (b) catches
a correctly-read value assigned to the wrong ward, which is the live risk on a
skewed scan. Both passing on 456 cells is strong.

Independently re-verified 2026-08-09: the appendix cell tables regenerate
`ward_census_1840.csv` byte-for-byte, and checks (a), (b) and (c) were re-run
from the raw cells rather than taken on report.

**Externally corroborated column endpoints.** The *Compendium* (pp.29–30)
prints the same Baltimore city row from separate typesetting. It matches the
Sixth Census city row digit for digit — two independent compositors agreeing:
free coloured males 2,170 / 1,825 / 1,601 / 1,287 / 369 / 9; free coloured
females 2,254 / 3,092 / 2,731 / 1,861 / 738 / 30; enslaved males 281 / 505 /
231 / 113 / 35 / 4; enslaved females 364 / 946 / 453 / 206 / 61 / —. This check
corrected two digits misread at lower resolution before it was applied.

**Further check on the printed page itself:** the twelve city wards plus the
five Baltimore county districts (9,088 + 7,335 + 4,898 + 5,760 + 4,985 =
32,066) give 102,313 + 32,066 = **134,379** = printed "Total Baltimore city and
county". ✓

### Reconciliation against the IPUMS check values

| | printed 1840 | IPUMS complete count | difference | % |
|---|---|---|---|---|
| total population | 102,313 | 102,225 | +88 | +0.09% |
| free Black | 17,967 | 17,958 | +9 | +0.05% |
| enslaved | 3,199 | 3,152 | +47 | +1.49% |
| **Black total** | **21,166** | **21,110** | **+56** | **+0.27%** |

**This reconciles.** Every quantity lands within half a percent except the
enslaved count, which is within 1.5% on a base of ~3,000 — i.e. 47 people.

To be plain about what this comparison is and is not: the two figures are not
supposed to be identical. The printed volume is an aggregate as corrected at the
Department of State in 1841; IPUMS is a modern re-count of the surviving
manuscript schedules. The residuals are the ordinary gap between those two
things, and they run in the expected direction (the published total slightly
exceeds the modern recount, consistent with minor schedule loss and clerical
correction). The city total independently matches the *published* city figure
of 102,313 exactly, because it **is** that figure.

Nothing was adjusted, at any point, to make any of this close.

---

## 6. Uncertain figures — every one of them

The transcription is clean, but historians should know precisely where the soft
spots are.

1. **Free white males, 20 & under 30, ward 3 = 684.** The middle digit is
   broken in the scan. 684 is what the column total requires and what the glyph
   shows at full resolution. Resolved, but resolved with the help of the check
   rather than read cold.
2. **Enslaved females, 36 & under 55, ward 11 = 22, not 23.** At low
   magnification the final stroke reads as a 3. The column total is 206 and the
   glyph at full resolution is a 2.
3. **Enslaved females "100 and upwards" is a dash, not a zero,** for every
   Baltimore ward. Carried as 0 in the CSV. This is a printing convention, not
   an observation of zero centenarians.
4. **Ward 12 manuscript vs print: 11,653 vs 11,635.** The enumerator's signed
   abstract totals 11,653 (and its six components sum to 11,653 internally),
   while the printed volume gives 11,635. This is a transposition, almost
   certainly by the printer or the State Department clerk. **The CSV carries the
   printed 11,635**, because that is the figure the whole table is internally
   consistent with and the one checks (a)/(b)/(c) close on. Flagged, not
   resolved. If it matters for an exhibit label, say "about 11,600".
5. **Ward 1's written manuscript summary was not made to close** by the
   manuscript-route agent's digit reading. The ward 1 *recapitulation* grand
   total (7,421) does match the print exactly. Only the prose summary line
   is unverified, and nothing depends on it.
6. **Only the twelve city wards were transcribed.** The five Baltimore County
   districts on the same pages were not, and are not in the CSV.
7. **The per-ward figures rest on a single scan.** The city-level row is
   confirmed twice over (Sixth Census + Compendium). The individual ward cells
   appear in only one printed source. Checks (b) and (c) are what stand behind
   them, and they are strong, but there is no second printing of the ward detail
   to compare against. The manuscript recapitulation leaves in
   `data/evidence/census1840/m704_*.jpg` are the available second witness if
   ward-level certainty is ever needed: ward 1 (7,421) and ward 3 (5,458 partial)
   were spot-checked and agree.

### One caution that is not about transcription at all

**1820 ward N and 1840 ward N are not the same place.** Both censuses have
twelve wards, which invites a false comparison. The boundaries were redrawn in
1832. Comparing the HUE polygon sets confirms it: the total city footprint is
unchanged (331,205,159 vs 331,205,149 map units) but individual wards moved
enormously — ward 10 more than tripled in area, ward 2 shrank to 31% of its
former size, ward 9 to 37%, ward 11 to 46%, while wards 3, 7 and 5 grew by 2.1×,
1.7× and 1.7×.

Do **not** compute ward-level change between 1820 and 1840 by ward number. Any
change-over-time layer must be built by areal interpolation onto a common
geography, or presented as separate snapshots. The same applies with more force
to 1850/1860 (20 wards).

---

## 7. Provenance

**PRIMARY SOURCE.** *Sixth Census or Enumeration of the Inhabitants of the
United States, as Corrected at the Department of State, in 1840.* Washington:
Printed by Blair and Rives, 1841.

- **Printed pp.194–195** (Maryland section runs pp.193–201). Running head
  "CENSUS OF THE UNITED STATES, JUNE 1, 1840"; section head "AGGREGATE AMOUNT
  OF EACH DESCRIPTION OF PERSONS WITHIN THE DISTRICT OF MARYLAND"; stub column
  headed "NAME OF WARD, TOWN, TOWNSHIP, PARISH, PRECINCT, HUNDRED, OR DISTRICT."
- Copy used: **HathiTrust id `uc1.31175023953089`**, 496 page scans,
  Google-digitized from the University of California copy, public domain in the
  United States.
- Catalog record: <https://catalog.hathitrust.org/Record/002815958>
- Printed p.194 = scan **seq 204**:
  <https://babel.hathitrust.org/cgi/pt?id=uc1.31175023953089&seq=204&view=1up>
- Printed p.195 = scan **seq 205**: same URL with `seq=205`.
- Full-resolution JPEG is retrievable from within an authenticated page context
  via `https://babel.hathitrust.org/cgi/imgsrv/image?id=uc1.31175023953089;seq=204;size=full;rotation=0`
  (a direct fetch from outside the page context returns 403).
- **Accessed 2026-08-09.**

**CORROBORATING SOURCE.** *Compendium of the Enumeration of the Inhabitants and
Statistics of the United States … from the Returns of the Sixth Census, by
Counties and Principal Towns.* Printed pp.28–30 (Maryland).
<https://www2.census.gov/library/publications/decennial/1840/1840v3/1840c-03.pdf>,
PDF pp.5–7. Accessed 2026-08-09. Confirms the city-level row digit for digit.
**Contains no ward breakdown and was not used for any ward figure.**

**CORROBORATING MANUSCRIPT.** Sixth Census of the United States, 1840,
population schedules, Maryland, Baltimore City, bound as Volume 2 (wards 1–6,
pp.1–295) and Volume 3 (wards 7–12). NARA microfilm publication M704, RG 29 —
Baltimore City on rolls 158 (wards 1–3), 159 (wards 4–6), 160 (wards 7–10),
161 (wards 11–12). FHL/GSU film 0013183. Digitised on Ancestry Library Edition
(ancestrylibrary.com), collection 8057, image sequence 4410622, frames
00001–01261. Accessed 2026-08-09 under the Johns Hopkins licence; targeted
lookups only, paced, no captcha or block encountered.

**PAGE IMAGES SAVED** to `data/evidence/census1840/`:

- `sixthcensus1840_p194_baltimore_12wards_freewhite_freecolored.jpg` — the transcribed page
- `sixthcensus1840_p195_baltimore_12wards_slaves_totals.jpg` — the transcribed page
- `sixthcensus1840_titlepage_blair_and_rives_1841.jpg`, `..._p193_maryland_section_divider.jpg`, `..._p200_maryland_recapitulation_by_counties.jpg`
- `crop_p195_ward_labels_and_totals.png`, `crop_p194_freecolored_totals_baltimore_city.png`, `crop_p195_slaves_totals_baltimore_city.png` — legible orientation crops
- `compendium1840_p28/p29/p30_*.png` and two crops — the corroborating printing
- `local_census1840_md_pdf_p142_manufactures_recapitulation.png` — proof of what the local PDF actually is
- `m704_*.jpg` (19 frames) and `m704_contactsheet_ward_recapitulation_pages.png` — the manuscript recapitulation leaves

**WARD GEOGRAPHY.** `data/raw/hue/HUE_Baltimore_Wards/baltimore_wards_1832_1840.shp`
— verified 12 features, `Ward_Num` 1–12. Craig's Business Directory 1842,
printed p.50, "Boundaries of Wards in Baltimore" (14 wards),
`data/raw/craigsbusinessdi1842balt.txt`.

**RELATED DOCS.** `docs/census1840_transcription.md` (method + all 456 cells),
`docs/census1840_printed_check.md` (source-location work),
`docs/census1840_manuscript_recon.md` (M704 reconnaissance, frame index).

---

## 8. Bottom line

1840 African American population by ward is **recovered, reconciled and safe to
map.** Confidence in the ward totals is high; confidence in the four race/sex
figures per ward is high; the honest caveats are the four flagged cells in §6
and the fact that ward detail rests on one printed source rather than two.

Join to the **1832–1840** twelve-ward polygons. Do not compare ward numbers
across census years.
