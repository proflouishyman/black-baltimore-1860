# 1840 Baltimore City ward population — full transcription

Transcribed 2026-08-09. Output: `data/work/ward_census_1840.csv`.

This closes the 1840 hole in the ward series on the same footing as 1820, 1850
and 1860: a printed federal census volume, hand-transcribed from page images,
reconciled against its own printed totals.

## Source

**PRIMARY.** *Sixth Census or Enumeration of the Inhabitants of the United
States, as Corrected at the Department of State, in 1840.* Washington: Printed
by Blair and Rives, 1841.

- Section: "AGGREGATE AMOUNT OF EACH DESCRIPTION OF PERSONS WITHIN THE DISTRICT
  OF MARYLAND", running head "CENSUS OF THE UNITED STATES, JUNE 1, 1840".
  Maryland runs printed pp.193–201.
- **Printed p.194** — FREE WHITE PERSONS (males, then females; 13 age bands
  each) and FREE COLORED PERSONS (males, then females; 6 age bands each).
- **Printed p.195** — SLAVES (males, then females; 6 age bands each), then the
  TOTAL column.
- Stub column headed "NAME OF WARD, TOWN, TOWNSHIP, PARISH, PRECINCT, HUNDRED,
  OR DISTRICT." Under BALTIMORE: twelve ward rows braced and labelled
  "Baltimore city", then "Total Baltimore city", then First–Fifth district,
  then "Total Baltimore city and county".
- Copy used: HathiTrust id `uc1.31175023953089`, 496 page scans,
  Google-digitized from the University of California copy, public domain in the
  US. Catalog record <https://catalog.hathitrust.org/Record/002815958>.
- Page URLs: printed p.194 = scan seq 204,
  <https://babel.hathitrust.org/cgi/pt?id=uc1.31175023953089&seq=204&view=1up> ;
  printed p.195 = scan seq 205, same URL with `seq=205`.
- Accessed 2026-08-09.

**Local page images actually transcribed from** (nothing else was used):

- `data/evidence/census1840/sixthcensus1840_p194_baltimore_12wards_freewhite_freecolored.jpg` (3536 × 4568)
- `data/evidence/census1840/sixthcensus1840_p195_baltimore_12wards_slaves_totals.jpg` (3440 × 4496)

Both are printed sideways; read after `PIL Image.transpose(Image.ROTATE_270)`.
The Baltimore city block sits in the lower-right quadrant as scanned, at
approximately y 2440–2900 in the rotated p.194 and y 1960–2420 in the rotated
p.195. The page is slightly skewed, so the numeric columns sit progressively
lower relative to the ward-name stub as you move right. Row identity was
therefore fixed by ordinal position within each ruled column (always exactly 12
values between the two horizontal rules) and then confirmed arithmetically by
check (b) below, which would fail if any value were assigned to the wrong ward.

**CORROBORATING.** *Compendium of the Enumeration of the Inhabitants and
Statistics of the United States … from the Returns of the Sixth Census, by
Counties and Principal Towns*, printed pp.28–30 (Maryland),
<https://www2.census.gov/library/publications/decennial/1840/1840v3/1840c-03.pdf>
(PDF pp.5–7), accessed 2026-08-09. Its separately typeset "Baltimore" row in
PRINCIPAL TOWNS matches the Sixth Census "Total Baltimore city" row band for
band. The Compendium has **no ward breakdown** and was not used for any ward
figure.

## Method

All 38 printed columns were transcribed for all 12 wards — 456 cells — not just
the four race/sex subtotals. Age-band detail was read in full precisely so that
both a row check and a column check would be available. The four race/sex
totals in the CSV are computed by summing the transcribed bands, never read off
directly.

## Reconciliation — all three checks pass, with no adjustment

**(a) Ward TOTAL column sums to the printed city total.**
7,421 + 7,393 + 10,102 + 8,601 + 8,212 + 6,611 + 6,242 + 9,646 + 7,337 + 9,592
+ 9,521 + 11,635 = **102,313** = printed "Total Baltimore city". ✓

**(b) Every ward row closes against its own printed TOTAL.**
For each of the 12 wards, free white + free coloured + enslaved (summed across
all 38 transcribed bands, both pages) equals that ward's printed TOTAL exactly.
12 of 12. ✓

**(c) Every column closes against the printed "Total Baltimore city" row.**
All 38 columns — 13 free white male bands, 13 free white female, 6 free
coloured male, 6 free coloured female, 6 enslaved male, 6 enslaved female —
sum down the twelve wards to the printed city figure exactly. 38 of 38. ✓

(b) and (c) together are a genuine double-entry closure: (c) catches a misread
digit, (b) catches a value assigned to the wrong ward. Both passing on 456
cells is strong evidence the transcription is clean.

Grand totals implied by the transcription:

| | transcribed | printed city row |
|---|---|---|
| free white | 81,147 | 81,147 |
| free coloured | 17,967 | 17,967 |
| enslaved | 3,199 | 3,199 |
| **aggregate** | **102,313** | **102,313** |

Confirmed column endpoints supplied as ground truth in the brief (verified
against the independently typeset Compendium pp.29–30) were reproduced exactly:
free coloured males 2,170 / 1,825 / 1,601 / 1,287 / 369 / 9; free coloured
females 2,254 / 3,092 / 2,731 / 1,861 / 738 / 30; enslaved males 281 / 505 /
231 / 113 / 35 / 4; enslaved females 364 / 946 / 453 / 206 / 61 / —.

## Reconciliation against the IPUMS check values

The printed volume and the modern re-count of the manuscript schedules are two
different things and are not expected to agree to the person. They agree to
well within a percent.

| | printed 1840 | IPUMS complete count | difference |
|---|---|---|---|
| total population | 102,313 | 102,225 | +88 (0.09%) |
| free Black | 17,967 | 17,958 | +9 (0.05%) |
| enslaved | 3,199 | 3,152 | +47 (1.5%) |
| Black total | 21,166 | 21,110 | +56 (0.27%) |

The residuals are the ordinary gap between a published aggregate corrected at
the Department of State and a modern recount of the surviving schedules. No
column fails to reconcile; nothing was adjusted to fit.

## Ward geography

The 1840 census was enumerated from 1 June 1840 and the table prints **twelve**
wards. Join to `data/raw/hue/HUE_Baltimore_Wards/baltimore_wards_1832_1840.dbf`
(12 features, `Ward_Num` 1–12), **not** the 1841–1845 set (14 features). The
14-ward division post-dates the enumeration; Craig's Business Directory 1842,
printed p.50, "Boundaries of Wards in Baltimore", already describes 14 wards.
The 1840 ward numbers are therefore **not** comparable ward-for-ward with 1850
or 1860 (20 wards).

## Results

| ward | white | free coloured | enslaved | Black total | aggregate | Black % |
|---|---|---|---|---|---|---|
| 1 | 6,020 | 1,220 | 181 | 1,401 | 7,421 | 18.88 |
| 2 | 6,035 | 1,229 | 129 | 1,358 | 7,393 | 18.37 |
| 3 | 7,503 | 2,415 | 184 | 2,599 | 10,102 | 25.73 |
| 4 | 7,205 | 1,286 | 110 | 1,396 | 8,601 | 16.23 |
| 5 | 6,894 | 933 | 385 | 1,318 | 8,212 | 16.05 |
| 6 | 5,628 | 727 | 256 | 983 | 6,611 | 14.87 |
| 7 | 4,756 | 1,058 | 428 | 1,486 | 6,242 | 23.81 |
| 8 | 7,322 | 2,031 | 293 | 2,324 | 9,646 | 24.09 |
| 9 | 5,676 | 1,292 | 369 | 1,661 | 7,337 | 22.64 |
| 10 | 7,372 | 1,991 | 229 | 2,220 | 9,592 | 23.14 |
| 11 | 7,340 | 1,842 | 339 | 2,181 | 9,521 | 22.91 |
| 12 | 9,396 | 1,943 | 296 | 2,239 | 11,635 | 19.24 |
| **city** | **81,147** | **17,967** | **3,199** | **21,166** | **102,313** | **20.69** |

Ward 3 is the densest Black ward (25.7%), followed by wards 8, 7 and 10. Wards
5, 6 and 4 are the whitest. Enslaved people are concentrated differently from
free Black residents: ward 7 has the highest enslaved count (428) but only the
fourth-highest free coloured count, while ward 3 has the largest free coloured
population (2,415) and comparatively few enslaved (184).

## Notes and limits

- Two cells were legible only at high magnification and were resolved with the
  help of the column check, then re-read on the page to confirm: free white
  males 20 & under 30, ward 3 = **684** (the middle digit is broken in the
  scan; 684 is what the column total requires and what the glyph shows at
  full resolution), and enslaved females 36 & under 55, ward 11 = **22** (not
  23; at low magnification the final stroke reads as a 3). Both are recorded
  here rather than silently corrected.
- The enslaved female "100 and upwards" column is blank for every Baltimore
  ward; the printed city cell is a dash, not a zero. It is carried as 0.
- Only the twelve city wards were transcribed. The five Baltimore *county*
  districts on the same pages were not, and are not in the CSV.
- No manuscript-schedule work was needed. The M704 images in
  `data/evidence/census1840/` are from a separate line of inquiry; the ward 1
  enumerator recapitulation there independently gives 7,421, matching the
  printed ward 1 total, but no CSV figure derives from them.

## Files

- `data/work/ward_census_1840.csv` — columns `ward,white,free_colored,slave,black_total,aggregate,black_pct`, matching `ward_census_1820.csv` and `ward_census_1860.csv` exactly.
- `docs/census1840_transcription.md` — this file.
- `docs/census1840_printed_check.md` — the prior source-location work (city-level figures and the ward TOTAL column only).

## Appendix — full band-level transcription (456 cells as printed)

Every cell below was read from the page images named above. Row and column
sums are the checks (b) and (c) described earlier. A dash in the printed table
is carried as 0.

**Free white persons — MALES (printed p.194)**

| ward | under 5 | 5 & u10 | 10 & u15 | 15 & u20 | 20 & u30 | 30 & u40 | 40 & u50 | 50 & u60 | 60 & u70 | 70 & u80 | 80 & u90 | 90 & u100 | 100+ | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 450 | 317 | 316 | 323 | 599 | 451 | 225 | 123 | 57 | 24 | 6 | 2 | 0 | 2893 |
| 2 | 500 | 374 | 259 | 279 | 631 | 450 | 227 | 112 | 55 | 10 | 3 | 0 | 0 | 2900 |
| 3 | 616 | 442 | 360 | 331 | 684 | 481 | 272 | 139 | 53 | 24 | 8 | 5 | 1 | 3416 |
| 4 | 576 | 408 | 340 | 315 | 731 | 579 | 280 | 132 | 70 | 16 | 7 | 2 | 1 | 3457 |
| 5 | 540 | 359 | 319 | 356 | 749 | 417 | 248 | 129 | 64 | 19 | 4 | 0 | 0 | 3204 |
| 6 | 404 | 265 | 271 | 306 | 754 | 477 | 216 | 118 | 53 | 13 | 6 | 0 | 0 | 2883 |
| 7 | 316 | 227 | 242 | 262 | 510 | 332 | 209 | 116 | 54 | 12 | 6 | 0 | 0 | 2286 |
| 8 | 650 | 413 | 391 | 357 | 843 | 547 | 253 | 122 | 55 | 18 | 7 | 0 | 0 | 3656 |
| 9 | 394 | 263 | 257 | 385 | 638 | 368 | 182 | 106 | 50 | 18 | 5 | 0 | 0 | 2666 |
| 10 | 548 | 433 | 355 | 470 | 697 | 466 | 254 | 152 | 69 | 24 | 5 | 1 | 0 | 3474 |
| 11 | 556 | 400 | 329 | 400 | 818 | 537 | 256 | 132 | 81 | 25 | 8 | 0 | 1 | 3543 |
| 12 | 800 | 597 | 487 | 428 | 882 | 616 | 339 | 171 | 103 | 35 | 5 | 0 | 0 | 4463 |
| **city** | 6350 | 4498 | 3926 | 4212 | 8536 | 5721 | 2961 | 1552 | 764 | 238 | 70 | 10 | 3 | **38841** |

**Free white persons — FEMALES (printed p.194)**

| ward | under 5 | 5 & u10 | 10 & u15 | 15 & u20 | 20 & u30 | 30 & u40 | 40 & u50 | 50 & u60 | 60 & u70 | 70 & u80 | 80 & u90 | 90 & u100 | 100+ | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 479 | 330 | 344 | 349 | 637 | 419 | 271 | 173 | 92 | 25 | 8 | 0 | 0 | 3127 |
| 2 | 498 | 327 | 294 | 356 | 755 | 420 | 239 | 161 | 47 | 32 | 5 | 1 | 0 | 3135 |
| 3 | 600 | 452 | 391 | 479 | 963 | 491 | 327 | 214 | 110 | 46 | 13 | 1 | 0 | 4087 |
| 4 | 562 | 390 | 404 | 431 | 810 | 509 | 290 | 194 | 116 | 34 | 6 | 2 | 0 | 3748 |
| 5 | 513 | 405 | 369 | 512 | 841 | 472 | 269 | 166 | 96 | 34 | 11 | 2 | 0 | 3690 |
| 6 | 353 | 273 | 270 | 356 | 650 | 389 | 213 | 137 | 77 | 14 | 8 | 4 | 1 | 2745 |
| 7 | 298 | 211 | 242 | 318 | 598 | 382 | 215 | 106 | 69 | 22 | 9 | 0 | 0 | 2470 |
| 8 | 602 | 476 | 386 | 392 | 766 | 504 | 274 | 148 | 74 | 31 | 10 | 2 | 1 | 3666 |
| 9 | 342 | 303 | 293 | 467 | 683 | 404 | 244 | 149 | 87 | 27 | 9 | 1 | 1 | 3010 |
| 10 | 550 | 495 | 430 | 485 | 843 | 451 | 300 | 205 | 91 | 38 | 10 | 0 | 0 | 3898 |
| 11 | 627 | 435 | 382 | 453 | 835 | 475 | 271 | 164 | 96 | 41 | 12 | 4 | 2 | 3797 |
| 12 | 796 | 526 | 511 | 574 | 1084 | 628 | 366 | 251 | 143 | 45 | 7 | 1 | 1 | 4933 |
| **city** | 6220 | 4623 | 4316 | 5172 | 9465 | 5544 | 3279 | 2068 | 1098 | 389 | 108 | 18 | 6 | **42306** |

**Free colored persons — MALES (printed p.194)**

| ward | under 10 | 10 & u24 | 24 & u36 | 36 & u55 | 55 & u100 | 100+ | total |
|---|---|---|---|---|---|---|---|
| 1 | 176 | 145 | 83 | 124 | 33 | 0 | 561 |
| 2 | 157 | 125 | 96 | 105 | 33 | 2 | 518 |
| 3 | 348 | 210 | 240 | 171 | 59 | 0 | 1028 |
| 4 | 145 | 147 | 161 | 102 | 37 | 2 | 594 |
| 5 | 71 | 69 | 57 | 48 | 12 | 0 | 257 |
| 6 | 63 | 103 | 91 | 28 | 8 | 0 | 293 |
| 7 | 66 | 92 | 104 | 48 | 9 | 1 | 320 |
| 8 | 278 | 230 | 174 | 201 | 35 | 0 | 918 |
| 9 | 114 | 137 | 103 | 51 | 11 | 0 | 416 |
| 10 | 268 | 200 | 172 | 143 | 60 | 1 | 844 |
| 11 | 212 | 171 | 170 | 115 | 35 | 3 | 706 |
| 12 | 272 | 196 | 150 | 151 | 37 | 0 | 806 |
| **city** | 2170 | 1825 | 1601 | 1287 | 369 | 9 | **7261** |

**Free colored persons — FEMALES (printed p.194)**

| ward | under 10 | 10 & u24 | 24 & u36 | 36 & u55 | 55 & u100 | 100+ | total |
|---|---|---|---|---|---|---|---|
| 1 | 163 | 173 | 130 | 133 | 58 | 2 | 659 |
| 2 | 167 | 198 | 166 | 118 | 60 | 2 | 711 |
| 3 | 338 | 355 | 393 | 193 | 101 | 7 | 1387 |
| 4 | 167 | 184 | 159 | 116 | 65 | 1 | 692 |
| 5 | 100 | 231 | 188 | 116 | 37 | 4 | 676 |
| 6 | 47 | 135 | 146 | 81 | 25 | 0 | 434 |
| 7 | 76 | 223 | 274 | 135 | 30 | 0 | 738 |
| 8 | 282 | 330 | 225 | 214 | 62 | 0 | 1113 |
| 9 | 147 | 289 | 244 | 137 | 57 | 2 | 876 |
| 10 | 247 | 318 | 258 | 226 | 93 | 5 | 1147 |
| 11 | 232 | 354 | 283 | 179 | 82 | 6 | 1136 |
| 12 | 288 | 302 | 265 | 213 | 68 | 1 | 1137 |
| **city** | 2254 | 3092 | 2731 | 1861 | 738 | 30 | **10706** |

**Slaves — MALES (printed p.195)**

| ward | under 10 | 10 & u24 | 24 & u36 | 36 & u55 | 55 & u100 | 100+ | total |
|---|---|---|---|---|---|---|---|
| 1 | 21 | 32 | 11 | 5 | 2 | 0 | 71 |
| 2 | 13 | 20 | 2 | 10 | 2 | 0 | 47 |
| 3 | 14 | 25 | 8 | 5 | 1 | 0 | 53 |
| 4 | 12 | 27 | 3 | 1 | 0 | 0 | 43 |
| 5 | 44 | 52 | 23 | 10 | 4 | 1 | 134 |
| 6 | 25 | 49 | 25 | 9 | 3 | 1 | 112 |
| 7 | 26 | 80 | 37 | 11 | 4 | 0 | 158 |
| 8 | 21 | 38 | 32 | 15 | 2 | 0 | 108 |
| 9 | 25 | 58 | 23 | 8 | 0 | 0 | 114 |
| 10 | 19 | 32 | 15 | 7 | 5 | 0 | 78 |
| 11 | 30 | 46 | 31 | 20 | 8 | 2 | 137 |
| 12 | 31 | 46 | 21 | 12 | 4 | 0 | 114 |
| **city** | 281 | 505 | 231 | 113 | 35 | 4 | **1169** |

**Slaves — FEMALES (printed p.195)**

| ward | under 10 | 10 & u24 | 24 & u36 | 36 & u55 | 55 & u100 | 100+ | total |
|---|---|---|---|---|---|---|---|
| 1 | 28 | 41 | 26 | 10 | 5 | 0 | 110 |
| 2 | 16 | 36 | 20 | 7 | 3 | 0 | 82 |
| 3 | 16 | 71 | 29 | 11 | 4 | 0 | 131 |
| 4 | 12 | 39 | 9 | 7 | 0 | 0 | 67 |
| 5 | 44 | 110 | 68 | 23 | 6 | 0 | 251 |
| 6 | 21 | 67 | 28 | 23 | 5 | 0 | 144 |
| 7 | 43 | 113 | 71 | 30 | 13 | 0 | 270 |
| 8 | 32 | 88 | 42 | 20 | 3 | 0 | 185 |
| 9 | 40 | 137 | 47 | 21 | 10 | 0 | 255 |
| 10 | 32 | 75 | 24 | 17 | 3 | 0 | 151 |
| 11 | 43 | 86 | 44 | 22 | 7 | 0 | 202 |
| 12 | 37 | 83 | 45 | 15 | 2 | 0 | 182 |
| **city** | 364 | 946 | 453 | 206 | 61 | 0 | **2030** |
