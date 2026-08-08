# Raw data manifest

The repository does **not** carry the bulk source files. They total roughly
2.6 GB, they are all publicly obtainable, and a public-facing repo is the wrong
place to mirror them. This file records where each one came from so the
pipeline stays reproducible.

Anything listed as **auth** requires a free IPUMS USA account and cannot be
fetched anonymously. Log in at <https://usa.ipums.org/>, then download.

Paths are relative to `data/raw/`.

## Directories and printed sources

| File | Source |
|---|---|
| `baltimoredirecto1799mull.txt` | <https://archive.org/details/baltimoredirecto1799mull> |
| `baltimoredirecto1803mull.txt` | <https://archive.org/details/baltimoredirecto1803mull> |
| `baltimoredirecto1816matc.txt` | <https://archive.org/details/baltimoredirecto1816matc> |
| `baltimoredirecto1822keen.txt` | <https://archive.org/details/baltimoredirecto1822keen> |
| `matchettsbaltimo1837balt.txt` | <https://archive.org/details/matchettsbaltimo1837balt> |
| `craigsbusinessdi1842balt.txt` | <https://archive.org/details/craigsbusinessdi1842balt> |
| `matchettsbaltimo1842balt.txt` | <https://archive.org/details/matchettsbaltimo1842balt> |
| `baltimoredirecto1845balt.txt` | <https://archive.org/details/baltimoredirecto1845balt> |
| `SheldonBusinessOrAdvertisingDir1845.txt` | <https://archive.org/details/SheldonBusinessOrAdvertisingDir1845> |
| `matchettsbaltimo1851balt.txt` | <https://archive.org/details/matchettsbaltimo1851balt> |
| `woodsbaltimoreci1860balt.txt`, `wood1860.djvu.xml` | <https://archive.org/details/woodsbaltimoreci1860balt> |
| `emcrosscosbaltim1863emcr.txt` | <https://archive.org/details/emcrosscosbaltim1863emcr> |
| `woodsbaltimoreci1868balt.txt`, `wood1868.djvu.xml` | <https://archive.org/details/woodsbaltimoreci1868balt> |
| `mayor1869.txt` | <https://archive.org/details/mayor1869> |
| `ord1817.txt` | Baltimore city ordinances, 1817, via Internet Archive |

The `_djvu.xml` files carry per-word page coordinates and are what
`scripts/extract_anchors.py` reads; the plain `.txt` is the same OCR without
geometry. Fetch the XML with
`https://archive.org/download/<id>/<id>_djvu.xml`.

## Transcriptions

| File | Source |
|---|---|
| `afrigeneas_1819.html` | <https://www.afrigeneas.org/library/baltimore/1819.html> |
| `afrigeneas_1822-23.html`, `afrigeneas_1822-23b.html` | <https://afrigeneas.org/library/baltimore/1822-23.html> |

## Federal census, printed volumes

| File | Source |
|---|---|
| `census1820.pdf`, `census1820_md.pdf` | <https://www2.census.gov/library/publications/decennial/1820/> |
| `census1840_md.pdf` | <https://www2.census.gov/library/publications/decennial/1840/> |
| `census1850_md.pdf` | <https://www2.census.gov/library/publications/decennial/1850/1850a/1850-census-report-maryland.pdf> |
| `census1860_md.pdf` | <https://www2.census.gov/library/publications/decennial/1860/population/1860a-18.pdf> |

The 1820 volume is a pure image scan with no text layer. It cannot be searched;
it has to be paged through. See `LOGBOOK.md`.

## IPUMS complete-count microdata (auth)

| File | Source |
|---|---|
| `H_1790.csv` … `H_1840.csv` | <https://usa.ipums.org/usa/1790_1840_household.shtml> |
| `slave_1850.dta` | <https://usa.ipums.org/usa-action/downloads/supplementals/slave_1850.dta> |
| `slave_1860.dta` | <https://usa.ipums.org/usa/slave/slave_data_old.shtml> |
| `ipums_1860_md.csv.gz`, `ipums_1860b_oversample.csv.gz` | IPUMS USA extract, 1860 1% and 1860b oversample |

Landing pages: enslaved persons <https://usa.ipums.org/usa/slave/slave.shtml>,
full count 1790–1840 <https://usa.ipums.org/usa/1790_1840_intro2.shtml>.

**Two traps, both documented in `SOLUTIONS.md`:**

1. The current enslaved-data page links `slave_1860_v2.dta`, which returns a
   genuine 404 from IPUMS's own server. Use the previous-version page above.
2. An expired session returns a **login page with a success status**, not an
   error. Verify downloads by content (`<stata_dta>` magic bytes; CSV header
   and last-line field counts must match), never by exit code.

Citation for the enslaved files: J. David Hacker, Ronald Goeken, Matt A.
Nelson, Ava Root, and Matthew Sobek, *IPUMS Full Count Datasets of the 1850 and
1860 Censuses of the Enslaved Population of the United States*, Minneapolis:
IPUMS. <https://doi.org/10.18128/D013.V2.1>

## Geography

| File | Source |
|---|---|
| `hue/` | Historical Urban Ecological data, ICPSR 35617, <https://www.icpsr.umich.edu/web/ICPSR/studies/35617> |
| `gunby.txt`, `gunby_streets.pdf` | <https://msa.maryland.gov/megafile/msa/speccol/sc5300/sc5339/000097/000000/000017/unrestricted/gunby-bc-streets-1993.pdf> |
| `mihp_baltimore.geojson` | Maryland Inventory of Historic Properties, Maryland Historical Trust |
| `balt_streets.geojson` | Derived from the HUE street file; rebuilt by the pipeline |

The HUE street file is circa 1930 and is used because it still contains alleys
that modern street data has lost. It is the best available base and it is
seventy years later than the earliest year we map. See `docs/GEOREFERENCE.md`.

## Maps

Full-resolution scans are not carried here; `*_preview.jpg` thumbnails are, so
the gallery builds without them.

| File | Source |
|---|---|
| `baltimore_1851_plan.jp2` | Sidney & Neff, *Plan of the City of Baltimore*, 1851. <https://www.loc.gov/item/2004629026/> |
| `baltimore_1822_poppleton.jp2` | Poppleton plan of Baltimore, 1822, Library of Congress |
| other `baltimore_18xx_*` | Library of Congress and Digital Maryland (CONTENTdm); see `docs/maps.html` for the per-map link |
