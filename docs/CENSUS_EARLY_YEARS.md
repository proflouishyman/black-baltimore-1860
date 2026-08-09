# Ward-level population in the printed censuses of 1800, 1810 and 1830

Checked 2026-08-09. This asks one question of three federal volumes: **does the
printed census give Baltimore City population by ward?**

| Year | Volume | Below county level? | Baltimore broken out? | Ward table? |
|---|---|---|---|---|
| **1800** | Return of the Whole Number of Persons (2nd Census) | yes, "Cities, Counties, Towns and Hundreds" | **one row: "City of Baltimore"** | **NO** |
| **1810** | Aggregate Amount of Each Description of Persons (3rd Census) | yes, "Counties, &c." | **three rows: City, Eastern precincts, Western precincts** | **NO** |
| **1830** | Fifth Census, or Enumeration of the Inhabitants (5th Census) | yes, "NAME OF WARD, TOWN, TOWNSHIP, PARISH, PRECINCT, HUNDRED, OR DISTRICT" | **twelve wards, First through Twelfth, plus "Total of Baltimore City"** | **YES** |

**The answer the exhibit was waiting on: 1800 genuinely has no ward table.** The
marshal for Maryland returned Baltimore as a single line and the Census Office
printed it that way. There is no federal ward-level table for 1800 to be found,
missed or recovered. That conclusion rests on having rendered and read the whole
Maryland section, which is exactly one page, plus the corrected Maryland return
printed later in the same volume, which is also one page.

**1830 is a genuine find and it was not previously known to this project.** The
Fifth Census prints Baltimore City by twelve wards on printed pages 80 and 81,
under the same stub heading that eventually located the 1840 table. It has not
been transcribed. See section 4 for why, and for exactly where a transcriber
should work.

---

## 1. 1800, Second Census

**Volume.** *Return of the Whole Number of Persons within the Several Districts
of the United States, according to "An act providing for the second Census or
Enumeration of the Inhabitants of the United States." Passed February the twenty
eighth, one thousand eight hundred.* Printed by order of the House of
Representatives. Transmitted to the President by **James Madison, Department of
State, 8 December 1801**.

- Hosted by the Census Bureau itself:
  <https://www2.census.gov/library/publications/decennial/1800/1800-returns.pdf>
  (72 PDF pages, 53 MB, listed from
  <https://www.census.gov/library/publications/1801/dec/return.html>). Accessed
  2026-08-09.
- Also on HathiTrust as catalog record 002815952 (N. Ross reprint, 1990).

**Maryland occupies exactly one page**, **PDF page 50** of the census.gov file
(the volume's leaves are largely unnumbered, so cite by PDF page), headed
"MARYLAND. Schedule
of the whole number of Persons in the District of Maryland", signed **REUBEN
ETTING, Marshal of the Maryland District**. The page carries the whole state:
twenty-one county rows, the District of Columbia, an "Additional return" line
for Baltimore county, the column totals, and an ABSTRACT block. Delaware is the
page before and Virginia the page after, so there is no continuation.

The stub is headed "NAMES OF Cities, Counties, Towns and Hundreds", so the
volume is capable of going below county level. For Maryland it does so exactly
once, and the entry is:

> City of Baltimore

as a single row. There are no wards.

**What the 1800 volume actually gives for Baltimore City** (printed p.50, the
row "City of Baltimore"):

| Column | Value |
|---|---:|
| Free white males, under 10 / to 16 / to 26 / to 45 / 45 and up | 3,035 · 1,849 · 3,180 · 2,519 · 711 |
| Free white females, under 10 / to 16 / to 26 / to 45 / 45 and up | 2,675 · 1,621 · 2,418 · 2,126 · 766 |
| All other free persons except Indians not taxed | **2,771** |
| Slaves | **2,843** |

There is no per-row total column for the county rows (the "Total of all
descriptions" column is used only for the additional return).

Note the column set. In 1800 free people of colour are a **single
undifferentiated count**, not banded by age or sex, and headed "All other free
Persons except Indians not taxed". Only free white persons are banded. This is
the same shape as 1790 and it is not the modern free-coloured/enslaved split.

**Reconciliation, city level.**

| | printed 1800 | IPUMS complete count | difference | % |
|---|---:|---:|---:|---:|
| total population | 26,514 | 26,520 | −6 | −0.02% |
| free people of colour | 2,771 | 2,614 | +157 | +6.0% |
| enslaved | 2,843 | 2,752 | +91 | +3.3% |
| Black total | 5,614 | 5,366 | +248 | +4.6% |

The total is derived by summing the twelve printed cells (white males 11,294 +
white females 9,606 + 2,771 + 2,843). It lands within six people of the IPUMS
control, which is as close as this comparison ever gets. The race components run
a few percent above IPUMS in the direction you would expect from a published
aggregate against a modern recount of surviving schedules, though the gap is
wider than 1840's.

**The corrected Maryland return.** Printed later in the same volume (PDF pp.70
and 71) is a **second, corrected Maryland schedule**, sent in by Etting from
Baltimore on 21 December 1801 after John Archer reported the Harford county
returns were wrong. Jefferson transmitted it to Congress as a replacement.
Baltimore's own row is **identical in both printings** (3,035 · 1,849 · 3,180 ·
2,519 · 711 · 2,675 · 1,621 · 2,418 · 2,126 · 766 · 2,771 · 2,843), and the
corrected version is still a single line. Two separately typeset printings
agreeing digit for digit is a real check on the reading above, and it also
closes off the possibility that a ward breakdown appears in one printing and not
the other.

**Evidence saved** to `data/evidence/census1800/`:

| File | What it shows |
|---|---|
| `return1800_titlepage_second_census.png` | Volume identity |
| `return1800_madison_transmittal_8dec1801.png` | Madison's covering letter, 8 Dec 1801 |
| `return1800_p50_maryland_schedule_baltimore_one_row.png` | **The Maryland page. Baltimore is one row.** |
| `return1800_p71_maryland_corrected_return_etting.png` | The corrected return, also one row |

---

## 2. 1810, Third Census

**Volume.** *Aggregate Amount of each DESCRIPTION OF PERSONS within the UNITED
STATES OF AMERICA, and the Territories thereof, Agreeably to actual enumeration
made according to law, in the year 1810.* Washington: 1811.

- Not on census.gov. The Census Bureau's page for it
  (<https://www.census.gov/library/publications/1811/dec/1810a.html>) says "This
  volume is not part of our digital collection" and offers only an Illinois
  Territory extract.
- Read from the full-view Google Books copy **`N6AYMlQK_xUC`**, a Norman Ross
  Publishing 1990 facsimile of the 1811 printing, digitised from the University
  of Michigan copy. 167 page images. Accessed 2026-08-09.
  <https://books.google.com/books?id=N6AYMlQK_xUC>

**Maryland occupies exactly one page**, printed **page 53**, headed "Aggregate
amount of each description of Persons within the DISTRICT OF MARYLAND", signed
**THOS. RUTTER, Marshal of the District of Maryland**, dated 17 January 1811.
Delaware (printed p.52a) is before it and Virginia (printed p.54) after, so
again there is no continuation.

The stub is headed "NAMES OF THE RESPECTIVE COUNTIES, &c." and under the "&c."
Baltimore is split into **three** rows, not twelve:

> City of Baltimore · Eastern precincts of Baltimore · Western ditto of ditto

That is a real sub-city geography and it is better than nothing, but it is
precincts, not wards.

**What the 1810 volume gives** (printed p.53):

| Row | white M (5 bands) | white F (5 bands) | all other free | slaves | printed total |
|---|---|---|---:|---:|---:|
| City of Baltimore | 3,997 · 1,882 · 3,376 · 4,323 · 1,215 | 3,881 · 1,818 · 2,984 · 3,078 · 1,343 | 3,973 | 3,718 | 35,583 |
| Eastern precincts of Baltimore | 463 · 189 · 325 · 409 · 167 | 505 · 225 · 341 · 336 · 142 | 686 | 262 | 4,050 |
| Western ditto of ditto | 855 · 368 · 603 · 624 · 269 | 797 · 367 · 474 · 470 · 386 | 1,012 | 697 | 6,922 |

As in 1800, free people of colour are one undifferentiated count ("All other
free persons, except Indians not taxed") with no age or sex detail. Only free
white persons are banded.

**Arithmetic checks against the printed page.**

- Eastern precincts: the twelve cells sum to **4,050**, the printed total. Exact.
- Western precincts: the twelve cells sum to **6,922**, the printed total. Exact.
- Baltimore county (the row above the city): sums to **29,255**, the printed
  total. Exact.
- **City of Baltimore: the twelve cells sum to 35,588 against a printed total of
  35,583, a discrepancy of 5.** Every digit was re-read at full resolution and
  the reading did not change. Since the three neighbouring rows all close
  exactly, this looks like an error in the 1811 printing rather than a
  transcription error here. It is carried as a flag, not corrected.
- Maryland column totals sum to the printed state total of **380,546**, which is
  the accepted 1810 figure for Maryland. Exact.

**Reconciliation, city and precincts combined, against the IPUMS controls.**

| | printed 1810 | IPUMS complete count | difference | % |
|---|---:|---:|---:|---:|
| total population | 46,555 | 46,465 | +90 | +0.19% |
| free people of colour | 5,671 | 5,658 | +13 | +0.23% |
| enslaved | 4,677 | 4,649 | +28 | +0.60% |
| Black total | 10,348 | 10,307 | +41 | +0.40% |

This reconciles cleanly and it confirms that the IPUMS 1810 Baltimore universe
is city **plus** both precincts, not the city alone.

**One trap worth recording.** A keyword scan of this volume flags the word
"Baltimore" on printed p.52a as well. That page is **Delaware**, and the hit is
Sussex County's "Baltimore, Dagsborough, Indian River, Lewes and Rehoboth and
Broadkiln hundreds". Anyone searching for Baltimore in the 1810 volume will find
Delaware first.

**Errata.** The volume's "MEMORANDA AND ERRATA of the Census of the United
States for the year 1810" (printed at the end) records that "The return for
Maryland was transmitted to the marshal of that district" for revision, the same
treatment given Massachusetts, whose first return had omitted persons. It lists
no numeric correction for Maryland, so the printed p.53 already is the revised
return.

**Evidence saved** to `data/evidence/census1810/`:

| File | What it shows |
|---|---|
| `aggregate1810_titlepage_washington_1811.png` | Volume identity and the 1990 facsimile imprint |
| `aggregate1810_p53_maryland_baltimore_city_and_precincts.png` | **The Maryland page** |
| `crop_1810_p53_baltimore_city_eastern_western_precincts.png` | The three Baltimore rows, legible |
| `crop_1810_p53_stub_names_of_counties.png` | The stub heading and column heads |
| `aggregate1810_p52a_delaware_baltimore_hundred_false_positive.png` | The Delaware "Baltimore hundred" trap |
| `aggregate1810_memoranda_and_errata.png` | Errata, including the Maryland note |
| `aggregate1810_grand_recapitulation_by_state.png` | State-level recapitulation |

---

## 3. 1830, Fifth Census: the ward table exists

**Volume.** *FIFTH CENSUS; OR, ENUMERATION OF THE INHABITANTS OF THE UNITED
STATES. 1830. To which is prefixed a Schedule of the Whole Number of Persons
within the Several Districts of the United States, taken according to the Acts
of 1790, 1800, 1810, 1820. Published by authority of an Act of Congress.*
**WASHINGTON: PRINTED BY DUFF GREEN. 1832.**

- **Not on census.gov.** The Bureau's page for it
  (<https://www.census.gov/library/publications/1832/dec/1830a.html>) says "This
  volume is not part of our digital collection", exactly as for the 1840
  population volume.
- **Not on HathiTrust.** Searched by title, by author heading "United States.
  Census Office. 5th census, 1830", and by full text on 2026-08-09. HathiTrust
  holds only the *Abstract*, plus microform reprints. This is the reverse of the
  1840 case, where HathiTrust was the answer.
- **Not on the Internet Archive.** IA holds the 1830 manuscript schedules on
  microfilm and the *Abstract*, not the population volume.
- **Read from the full-view Google Books copy `NWt-ODj-9zEC`**, digitised from
  the Purdue University Libraries copy, 214 page images, 165 printed pages.
  Accessed 2026-08-09.
  <https://books.google.com/books?id=NWt-ODj-9zEC>

**The Maryland section runs printed pp.79 to 83.** The county detail table is a
two-page spread:

| Printed page | Google pid | Content |
|---|---|---|
| 80 | `RA1-PA80` | **Baltimore City, twelve wards: FREE WHITE PERSONS, males and females, thirteen age bands each** |
| 81 | `RA1-PA81` | **Baltimore City, twelve wards: SLAVES and FREE COLORED PERSONS, males and females, six bands each, then TOTAL** |
| 82 | `RA1-PA82` | End of the Maryland county detail, then "Recapitulation ... by county" where Baltimore folds back into "Baltimore County, including City" |
| 83 | `RA1-PA83` | Maryland by classes, state total 447,040 |

The stub column on printed p.80 is headed, in full:

> NAME OF WARD, TOWN, TOWNSHIP, PARISH, PRECINCT, HUNDRED, OR DISTRICT.

with a second stub column headed "NAME OF COUNTY." This is the same heading that
located the 1840 table. Under the county heading **BALTIMORE CITY** the rows
run:

> First Ward, Second Ward, Third Ward, Fourth Ward, Fifth Ward, Sixth Ward,
> Seventh Ward, Eighth Ward, Ninth Ward, Tenth Ward, Eleventh Ward, Twelfth
> Ward, **Total of Baltimore City**

Twelve wards. The block sits between "Total of Anne Arundel" above and
"BALTIMORE COUNTY, First Collection District ..." below, so the city and the
county are separately enumerated.

**The one figure read with confidence: "Total of Baltimore City" = 80,620.**
That is the accepted published 1830 population of Baltimore, and it is
corroborated locally by Matchett's *Baltimore Director* 1837
(`data/raw/matchettsbaltimo1837balt.txt`, chapter III), which gives the 1830
census as 80,625 in one sentence and 80,622 in another (both OCR-mangled forms
of 80,620) with "nearly 19,000 were colored, slaves 4,100".

Against the IPUMS control of 79,473 that is a difference of 1,147, or 1.4%. That
is a larger gap than 1840's 0.09%, and it is worth knowing before anyone
compares the two years.

**Ward geography.** June 1830 falls inside the HUE ward period **1818-1831**.
`data/raw/hue/HUE_Baltimore_Wards/baltimore_wards_1818_1831.shp` was verified to
contain exactly 12 features with `Ward_Num` 1-12. This is **the same polygon set
that `ward_census_1820.csv` joins to**, which means 1820 and 1830 would be
directly comparable ward by ward, unlike 1820 against 1840. Do **not** join 1830
to `baltimore_wards_1832_1840`.

**Evidence saved** to `data/evidence/census1830/`:

| File | What it shows |
|---|---|
| `fifthcensus1830_titlepage_duff_green_1832.png` | Volume identity and imprint |
| `fifthcensus1830_p80_maryland_baltimore_12wards_freewhite.png` | **The table, left page** |
| `fifthcensus1830_p81_maryland_baltimore_12wards_slaves_freecolored_total.png` | **The table, right page** |
| `crop_1830_p80_stub_name_of_ward_baltimore_city_12_wards.png` | The stub, twelve wards named |
| `crop_1830_p80_column_headings_free_white_persons.png` | Column heads, white age bands |
| `crop_1830_p81_column_headings_slaves_free_colored_total.png` | Column heads, slaves / free colored / TOTAL |
| `crop_1830_p81_baltimore_12_wards_data_block.png` | The twelve ward rows at best available magnification |
| `fifthcensus1830_p82_maryland_recapitulation_by_counties.png` | The recapitulation, city folded into county |
| `fifthcensus1830_p83_maryland_by_classes_total_447040.png` | Maryland totals |
| `abstract1830_titlepage_duff_green_1832.png` | The *Abstract*, the volume that is easy to find |
| `abstract1830_p15_maryland_baltimore_and_city_one_row.png` | **The trap: the Abstract prints "Baltimore, and city" as one row** |

---

## 4. Why there is no `ward_census_1830.csv`

**The table was found. It has not been transcribed, and no CSV was written.**

The only digital copy that exists is the Google Books scan, and Google caps
delivery of that scan at **1917 x 2500 pixels for the whole page**. Every
delivery path was tested: `zoom` 0 through 5, `w` up to 4000, `h` up to 3000.
The ceiling does not move. The PDF download, which would carry the underlying
higher-resolution images, is gated behind a captcha.

At that resolution a ward row is about 14 pixels tall and a digit is about 6
pixels wide. Upscaling with Lanczos, percentile contrast stretch and unsharp
masking was tried and does not add information that is not there. In practice
the digit pairs 3/8, 5/6, 0/6 and 0/9 are frequently indistinguishable, and the
five-digit figures in the TOTAL column are the worst-set on the page.

The proof that this is a real limit and not excess caution: the twelve ward
totals were read twice, at two magnifications, and the two readings disagree
with each other in four places, and **neither reading sums to 80,620**. So at
least one cell is wrong in each pass, and there is no way to tell which from the
image. The same happened in the slave and free-coloured blocks, where individual
column sums came out several units away from the printed column totals and the
printed column totals were themselves ambiguous to the same degree.

For comparison, the 1840 pages were transcribed from HathiTrust scans of **3536
x 4568** pixels, and the 1840 transcription closed on all three checks on the
first pass. That is the difference between a scan that supports a 612-cell
transcription and one that does not.

**Writing a plausible-looking CSV out of this scan would be exactly the failure
mode this project has already made twice.** The tables in `docs/CENSUS1840.md`
close because the arithmetic closes. These would not, and adjusting numbers to
make them close is the thing that must never happen.

### What a transcriber needs

Work from **printed pp.80 and 81** of the Fifth Census (Duff Green, 1832), and
nothing else. The row order is fixed: twelve wards then "Total of Baltimore
City". The column set is:

- **p.80**: FREE WHITE PERSONS, males 13 bands (under 5, to 10, to 15, to 20, to
  30, to 40, to 50, to 60, to 70, to 80, to 90, to 100, 100 and upwards), then
  females, the same 13 bands. 26 columns.
- **p.81**: SLAVES, males 6 bands (under 10, to 24, to 36, to 55, to 100, 100
  and upwards), then females, the same 6. FREE COLORED PERSONS, males 6, females
  6. Then TOTAL. 25 columns.

51 cells per ward, 612 cells for the twelve wards, plus the printed city row.

Required checks before the transcription is accepted, the same three that
validated 1840:

1. The twelve ward TOTAL values sum to **80,620**.
2. For each ward, the 50 band cells sum to that ward's printed TOTAL.
3. Each of the 51 columns sums down the twelve wards to the printed "Total of
   Baltimore City" value in that column.

Then reconcile the city row against IPUMS: 79,473 total, 14,364 free Black,
4,058 enslaved.

### Where a better scan might come from

1. **A physical or library-digitised copy** of the Duff Green 1832 printing.
   This is the direct route and the volume is common in research libraries.
   Johns Hopkins is the obvious first call.
2. **The 1830 manuscript schedules**, NARA microfilm **M19**, Maryland. On the
   Internet Archive as `populationsc18300054unit` and
   `populationsc18300053unit`, free and public, and on Ancestry. The enumerators'
   end-of-ward recapitulation leaves are what corroborated 1840 (see
   `docs/census1840_manuscript_recon.md`), and they would serve here as either
   the primary source or the second witness.
3. **A contemporary Baltimore reprinting.** Matchett's *Baltimore Director* for
   1831, and Niles' *Weekly Register* for late 1830 and 1831, are the likely
   places a Baltimore printer would have set the ward table locally. Neither was
   checked. This is a cheap lead and worth an hour.

---

## 5. What this changes for the exhibit

- **1800 is closed, negatively and for good.** There is no federal ward table.
  If Lawrence Jackson needs 1800 at sub-city level it will have to come from the
  manuscript schedules (NARA M32) or from city records, not from the printed
  census. The printed census does give a solid city total, 26,514, with 2,771
  free people of colour and 2,843 enslaved, which is 21.2% of the city Black.
- **1810 is closed too**, but it yields a three-part city geography (city,
  eastern precincts, western precincts) that could be mapped if a coarse
  three-zone snapshot is useful. Black share was 22.2% across the three.
- **1830 is open and reachable.** The table is printed and located. It needs
  either a better scan or a couple of hours on the manuscript recapitulation
  leaves. If it is completed it would join the **1818-1831** polygons, the same
  as 1820, giving the exhibit a genuine decade-on-decade ward comparison that no
  other pair of years in the series supports.

## 6. What was actually opened and looked at

Recorded so nobody repeats it.

| Tried | Result |
|---|---|
| census.gov 1800 `1800-returns.pdf` | **The 2nd Census return. Maryland p.50. Baltimore one row.** |
| census.gov page for the 1810 volume | "This volume is not part of our digital collection." Only an Illinois extract. |
| census.gov `1830b.pdf` | The *Abstract of the Returns of the Fifth Census*, Doc. No. 263, Duff Green 1832. County level. **Baltimore county and city as one row.** No wards. |
| census.gov page for the 1830 population volume | "This volume is not part of our digital collection." |
| census.gov `decennial/1800/` and `decennial/1810/` directories | Empty of population volumes. |
| HathiTrust, title / author / full-text searches for the 1830 volume | **Not held.** Only the Abstract and microform reprints. |
| HathiTrust for 1800 | Held (record 002815952), but census.gov's own PDF is equivalent and easier. |
| Internet Archive, six query forms | Manuscript microfilm and reprints only. No printed 1810 or 1830 population volume. |
| Google Books | **Holds both.** 1810 = `N6AYMlQK_xUC`, 1830 = `NWt-ODj-9zEC`. Both full view. Page images capped at 2500 px tall. |
| Google Books PDF download for `NWt-ODj-9zEC` | Redirects to a captcha. |
| Any text search of any of these scans | Meaningless. All are image scans, and the 1830 OCR is bad enough that HathiTrust full-text search does not even match "Total of Baltimore city". |
| `data/raw/matchettsbaltimo1837balt.txt` | City-level 1830 figures only, no wards, but a useful independent check on 80,620 and on roughly 19,000 Black and 4,100 enslaved. |

Two method notes, both consistent with the 1820 and 1840 lessons:

- **Every one of these volumes was identified by rendering its title page and
  reading it before anything else.** The 1810 copy turned out to be a 1990
  facsimile, the 1830 copy on census.gov turned out to be the Abstract rather
  than the census, and neither fact is visible from a file name.
- **The state sections were found by looking, not by searching.** The 1810
  volume's page order as Google reports it is scrambled, so every page was
  rendered and its running head read by OCR to build a map of where each state
  begins. That is what turned up Maryland on printed p.53, one page, no wards.
