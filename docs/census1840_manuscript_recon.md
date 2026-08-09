# The 1840 manuscript schedules for Baltimore City: what exists, where, and how big the job is

Reconnaissance carried out 2026-08-09. Everything below was established by opening
actual page images and looking at them. Where a statement rests on an inference
rather than on a page I opened, it says so in those words.

Sample images are in `data/evidence/census1840/`, prefixed `m704_`.

---

## The headline

**The recapitulations exist.** Every one of Baltimore's twelve wards has a
recapitulation section bound at the end of its schedules, in the enumerator's own
hand, giving a per-page tally for every column and a ward grand total for every
column. Several wards additionally carry a signed abstract that writes the ward's
population out in words and figures, broken to exactly the six categories the
exhibit needs: white males, white females, free coloured males, free coloured
females, male slaves, female slaves.

Ward 12's abstract is the clearest example and it reconciles to the digit:

> The number of persons in my Division, 12th Ward Baltimore City, as appears in the
> foregoing Schedule subscribed by me, this twenty-first day of September eighteen
> hundred and forty:
>
> | | | |
> |---:|---|---|
> | 4,467 | Four thousand four hundred & sixty seven | White Males |
> | 4,938 | Four thousand nine hundred thirty eight | White Females |
> | 806 | Eight hundred & six | Col'd Males Free |
> | 1,138 | Eleven hundred & thirty eight | Col'd Females Free |
> | 114 | One hundred fourteen | Col'd Males Slave |
> | 190 | One hundred & ninety | Col'd Females Slave |
> | **11,653** | Total | |

4,467 + 4,938 + 806 + 1,138 + 114 + 190 = **11,653**. The arithmetic closes exactly.
Source image: `m704_img01260_ward12_ENUMERATOR_CERTIFICATE_full_ward_abstract.jpg`
(Ancestry image `4410622_01260`).

So the job is **not** 17,118 households. It is roughly **twenty-five images and
somewhere between 72 and 300 numbers**, depending on whether you want the six
headline categories per ward or the full age/sex breakdown. A careful transcriber
with the arithmetic checks below can do the whole city in under a day.

**Caveat, and it matters.** A parallel line of work in this project has meanwhile
found the printed 1840 volume's own Baltimore ward table (see
`data/evidence/census1840/sixthcensus1840_p194_*` and `_p195_*`). That means the
manuscript recapitulations are no longer the only route. Their real value now is as
an **independent check** on the printed table, and as the only place to get anything
the printed table does not carry. Use them that way rather than as a substitute.

---

## 1. How many wards Baltimore City had in 1840, and which HUE polygons match

**Twelve.** Not fourteen.

Evidence, in order of strength:

1. **The film itself.** The volume title target reads `6TH CENSUS — 1840 — MARYLAND
   — VOL·2 — BALTIMORE CITY — WARDS 1–6 — 1–295` (image `4410622_00004`,
   `m704_img00004_target_MD_vol2_baltimore_city_wards1-6_pp1-295.jpg`). Volume 3
   carries wards 7–12. There is no volume covering wards 13 or 14.
2. **The browse hierarchy of the digitised set.** Ancestry's
   `/api/browse-collection/8057/hierarchy?path=Maryland|Baltimore` returns exactly
   `Baltimore Ward 1` … `Baltimore Ward 12`, plus Baltimore County's Districts 1–5
   and a "Not Stated" bucket. Querying `Baltimore Ward 13` and `Baltimore Ward 14`
   returns empty arrays.
3. **In-period print.** Matchett's *Baltimore Director* for 1837 states flatly
   "The City is divided into twelve wards" (`data/raw/matchettsbaltimo1837balt.txt`,
   line 2917). The fourteen-ward division appears as Ordinance No. 18, "An Ordinance
   for the division of the City of Baltimore into fourteen Wards", printed in the
   appendix to Matchett's for **1842** (`data/raw/matchettsbaltimo1842balt.txt`,
   line ~32463). The 1842 appendix's city-government list is headed by Solomon
   Hillen, Jr., "Mayor, vice Saml. Brady, resigned" — Hillen took office in 1842,
   after the June 1840 enumeration.

The printed ordinance text in Matchett's 1842 carries no approval date, so I cannot
put a day on the change from the sources held locally. HUE dates the fourteen-ward
division 1841–1845, which is consistent with everything above.

**Therefore the matching polygon set is
`data/raw/hue/HUE_Baltimore_Wards/baltimore_wards_1832_1840.shp` (12 features,
`Ward_Num` 1–12).** Do **not** use `baltimore_wards_1841_1845.shp` (14 features)
for 1840.

One consequence worth flagging for the map: the 1832–1840 twelve-ward geography is
not nested inside the 1846–1860 twenty-ward geography, so 1840 and 1850/1860 ward
densities are not directly comparable polygon-for-polygon. That is a mapping
problem, not a transcription problem, but it should not be discovered later.

---

## 2. Where the images are

### Provenance chain

- **Original:** *Sixth Census of the United States, 1840*, population schedules,
  Maryland, Baltimore City. Bound as **Volume 2 (wards 1–6, pages 1–295)** and
  **Volume 3 (wards 7–12)**. Filmed by the Bureau of the Census Micro-Film Lab,
  machine No. 102 (stated on the volume target, image `4410622_00004`).
- **NARA microfilm publication:** **M704**, 580 rolls, RG 29.
- **Rolls covering Baltimore City** (read off Ancestry's own source citation on a
  sampled record in every one of the twelve wards, so all twelve are verified, not
  interpolated):

  | NARA M704 roll | Wards |
  |---|---|
  | **158** | 1, 2, 3 |
  | **159** | 4, 5, 6 |
  | **160** | 7, 8, 9, 10 |
  | **161** | 11, 12 |

- **FamilySearch/GSU film:** the second frame on the film is a shot of the film
  number plate reading **13183** (`m704_img00002_film_target_13183.jpg`), and
  Ancestry's citations give "Family History Library Film: **0013183**" for every
  Baltimore City ward. I could **not** verify the FamilySearch catalogue entry or
  its DGS number: familysearch.org returned only a sign-in page for the catalogue
  URLs I tried. Someone with a FamilySearch login should confirm film 0013183 and
  record the DGS/ark before this is cited as a FamilySearch locator.
- **NARA's own catalog:** not checked. catalog.archives.gov serves a JavaScript
  shell to non-browser fetches and I did not have the search budget to drive it in
  a browser. Do not repeat my omission — if a NARA-side citation is wanted, open
  the catalog in a browser and search M704.

### Ancestry (the working route)

- Database: **collection 8057, "1840 United States Federal Census"**, on
  **ancestrylibrary.com** (Johns Hopkins licence; not ancestry.com).
- Browse page: `https://www.ancestrylibrary.com/search/collections/8057/`
  → State *Maryland* → County *Baltimore* → the twelve ward links.
- **All twelve wards sit in one continuous image sequence, `4410622`, frames
  `00001`–`01261`.** Baltimore *County* is a different sequence (`4409449`).
- Image viewer URL template:

      https://www.ancestrylibrary.com/imageviewer/collections/8057/images/4410622_NNNNN?usePUB=true

  So **image 1 of ward 1 is**

      https://www.ancestrylibrary.com/imageviewer/collections/8057/images/4410622_00001?usePUB=true

### Ward-by-ward frame ranges

Ancestry's ward blocks are drawn at the first frame that carries an indexed
personal name. Because recapitulation pages carry no household names, the ward
boundary in Ancestry's browse tree is **offset from the physical ward boundary** —
a ward's recapitulation frequently lands either in the unindexed "Not Stated"
bucket or at the head of the *next* ward's block. Both columns below are given so
nobody trips over this.

| Ward | Ancestry block (first frame) | Block frames | **Recapitulation frames (verified by eye)** |
|---|---|---|---|
| 1 | `4410622_00001` | 00001–00107 | **00103–00108** |
| 2 | `4410622_00108` | 00108–00198 | **00199–00200** |
| 3 | `4410622_00199` | 00199–00321 | **00318–00321** |
| 4 | `4410622_00322` | 00322–00417 | **00414–00415** (00416–00417 same run, not opened) |
| 5 | `4410622_00418` | 00418–00515 | **00516–00517** |
| 6 | `4410622_00516` | 00516–00594 | **00595** (oath/certificate) + **00596** ("Recapitulation of the Whole") |
| 7 | `4410622_00595` | 00595–00660 | **00661–00662** |
| 8 | `4410622_00661` | 00661–00790 | **00787–00788** (00789–00790 same run, not opened) |
| 9 | `4410622_00791` | 00791–00869 | **00870–00871** |
| 10 | `4410622_00870` | 00870–00986 | **00987–00988** |
| 11 | `4410622_00987` | 00987–01099 | **01100–01101** |
| 12 | `4410622_01100` | 01100–01261 | **01259–01260** (certificate + abstract); 01261 is an END OF ROLL target |

Contact sheet of all twenty-four recapitulation frames:
`data/evidence/census1840/m704_contactsheet_ward_recapitulation_pages.png`.

Eighteen frames in the Baltimore City sequence carry no ward attribution at all in
Ancestry's index (browse path "Not Stated"): `00102–00107`, `00318–00321`,
`00414–00417`, `00787–00790`. Every one of those is either a final short schedule
page or a recapitulation page. They are invisible to a name search. **A keyword or
name search would never have surfaced the single most useful class of page in this
record.**

---

## 3. How many pages per ward, and in total

Each frame is one page. Each numbered schedule "page" is a **two-page opening**:
the left page carries the names and the free white and free coloured columns, the
right page carries the slave columns, the total, employment, pensioners, disability
and schools. Ancestry says the same thing in its collection description
("Each name is associated with two images as the 1840 census schedule was two pages
long"), and it is what the images show.

| Ward | Frames | ≈ openings (frames ÷ 2) |
|---|---|---|
| 1 | 107 (incl. 5 film targets) | ~50 |
| 2 | 91 | ~45 |
| 3 | 123 | ~61 |
| 4 | 96 | ~48 |
| 5 | 98 | ~49 |
| 6 | 79 | ~40 |
| 7 | 66 | ~33 |
| 8 | 130 | ~65 |
| 9 | 79 | ~40 |
| 10 | 117 | ~58 |
| 11 | 113 | ~56 |
| 12 | 162 | ~81 |
| **City total** | **1,261** | **~620** |

Cross-checks on that arithmetic, all consistent:

- The Volume 2 target says wards 1–6 occupy printed pages **1–295**. Frames
  `00001`–`00515` cover wards 1–6, which is 515 frames, ≈ 257 openings of schedule
  plus the recapitulation and target frames — the right order of magnitude for 295
  numbered pages.
- Ward 12's own certificate is headed "**77 Pages**" (image `4410622_01260`),
  against ~81 openings estimated from the frame count. The difference is the
  recapitulation and certificate leaves, which are numbered separately or not at all.
- 17,118 city households over ~590 household-schedule openings is ~29 households
  per page, against a form with 40 ruled lines. Plausible, and consistent with the
  many part-filled final pages visible at ward ends (e.g. `4410622_00101`, sixteen
  names; `4410622_00198`, nearly blank).

Ancestry's page-number citations put ward 1 at printed page 16, ward 3 at 100,
ward 4 at 159, ward 6 at 258 (all Volume 2, whose numbering runs 1–295), and
ward 7 at page 3, ward 10 at 137, ward 11 at 195, ward 12 at 251 (Volume 3, whose
numbering restarts at 1).

---

## 4. THE KEY QUESTION: recapitulation and summary pages

Yes, at three levels. I opened these pages; this is not inferred from what 1840
enumerators generally did.

### (a) A per-page tally at the foot of every sheet

Every schedule page — left and right — has a ruled total line at the bottom with
each column summed for that page. Visible on `4410622_00100`, `_00101`, `_00102`
and on every recapitulation page. This is the enumerator's own arithmetic and it is
what makes the recapitulations checkable.

### (b) A per-ward recapitulation, page by page

At the end of each ward, an opening (sometimes two) where the "NAMES OF HEADS OF
FAMILIES" column instead reads `Page 1, 2, 3 … 30`, and each row carries that
page's column totals. The foot of the recapitulation carries the ward grand total
for every column. Ward 3's is labelled in the margin, in script, **"Recapitulation
3d Ward"** (`m704_img00318_ward3_RECAPITULATION_left_labelled.jpg`); wards 11 and
12 have "Recapitulation" written across the head of the sheet; ward 6's is headed
**"Recapitulation of the Whole"**.

Worked example, ward 1 (`m704_img00104_*` and `m704_img00107_*`): the TOTAL column
lists per-page populations 174, 156, 142, 188, 128, 152, 147, 174, 159, 199, 158,
165, 164, 160, 128, 156, 162, 182, 130, 150, 158, 190, 168, 175, 171, 145, 141,
148, 140, 168 for pages 1–30; those sum to ~4,778 against a printed carry-forward
of **4,754**; the second recapitulation opening adds pages 31–47 as **2,667**; and
the grand total line reads **7,421**. 4,754 + 2,667 = 7,421 exactly. My reading of
individual per-page digits at this resolution is approximate — hence the ~24
discrepancy on my own re-addition — but the enumerator's three summary figures
close on each other, which is the check that matters.

Ward 3's recapitulation totals to **5,458** (`m704_img00319_*`).

### (c) A signed ward abstract in words and figures

Ward 12's (quoted at the top of this document) is the fullest: the enumerator
Joseph Brown's sworn oath, the justice of the peace John Wright's attestation dated
24 September 1840, the certificate that a copy was posted in two public places in
the Twelfth Ward, and then the six-category population abstract that reconciles
exactly to 11,653. It also gives employment by sector, deaf/dumb/blind/insane
counts, schools and scholars, and 292 white persons over 20 unable to read and write.

Ward 1 has the same thing in a plainer form at the foot of
`m704_img00105_ward1_RECAP_left_pages31-47_WITH_WRITTEN_WARD_SUMMARY.jpg`:

> Population of the First Ward Baltimore …
> No. of White Males 2964 / No. of do Females 3118 / No. of Free Colored 1220 /
> " Slaves 1?? — total 74??

with a second column beside it splitting free coloured and slaves by sex. **My
reading of those particular digits does not close against the 7,421 grand total on
`_00107`, so treat every figure in this paragraph as unverified.** It needs a
careful transcription at full zoom, not my reading off a downsampled render. This
is exactly the sort of number that must be reconciled before it is used.

Ward 1 also carries a further summary leaf headed, in the margin, **"Sheet No. 1
First Ward Baltimore City … Carried to Sheet No. 2"** (`4410622_00108`), which
Ancestry files under ward 2.

---

## 5. What the free coloured and slave columns look like, and what to sum

The 1840 form, as printed and as filled here (`(No. 4.)` in the top left corner):

**Left-hand page** — `SCHEDULE of the whole number of persons within the division
allotted to [enumerator], by the Marshal of the …`

| Block | Columns |
|---|---|
| NAMES OF HEADS OF FAMILIES | 1 |
| FREE WHITE PERSONS, INCLUDING HEADS OF FAMILIES — **Males** | Under 5; 5 & under 10; 10–15; 15–20; 20–30; 30–40; 40–50; 50–60; 60–70; 70–80; 80–90; 90–100; 100 and upwards |
| FREE WHITE PERSONS — **Females** | same thirteen bands |
| **FREE COLORED PERSONS — Males** | **Under 10; 10 & under 24; 24 & under 36; 36 & under 55; 55 & under 100; 100 and upwards** |
| **FREE COLORED PERSONS — Females** | **same six bands** |

**Right-hand page** — continuation of the same ruled sheet

| Block | Columns |
|---|---|
| **SLAVES — Males** | **Under 10; 10 & under 24; 24 & under 36; 36 & under 55; 55 & under 100; 100 and upwards** |
| **SLAVES — Females** | **same six bands** |
| TOTAL | 1 |
| Number of persons in each family employed in | Mining; Agriculture; Commerce; Manufactures and trades; Navigation of the ocean; Navigation of canals, lakes and rivers; Learned professions and engineers |
| Pensioners for Revolutionary or military services | names and ages |
| Deaf and dumb, blind and insane **white** persons | deaf & dumb under 14 / 14 and under 25 / 25 and upwards; blind; insane and idiots at public charge / at private charge |
| Deaf, dumb, blind and insane **colored** persons | deaf and dumb; blind; insane and idiots at public charge / at private charge |
| SCHOOLS, &c. | universities or colleges; students; academies and grammar schools; scholars; primary and common schools; scholars; scholars at public charge; No. of white persons over 20 years of age who cannot read and write |

The free coloured block and the slave block face each other across the gutter, and
both use the **same six age bands** — under 10, 10–23, 24–35, 36–54, 55–99, 100+.

### What to sum for the exhibit

For each ward, from the recapitulation grand-total line:

- **Free Black population** = the six FREE COLORED MALES columns + the six FREE
  COLORED FEMALES columns (12 numbers).
- **Enslaved population** = the six SLAVES MALES columns + the six SLAVES FEMALES
  columns (12 numbers).
- **Black total** = the above 24 numbers.
- **Ward total population** = the single TOTAL column figure on the right-hand
  recapitulation page — which is an independent check, because free white + free
  coloured + slaves must equal it.

Where a signed abstract exists (wards 12 and 1 confirmed; the contact sheet
suggests others do too), you get the four aggregates directly and can use the
column sums as the check rather than the source.

---

## 6. Feasibility, and how to actually do it

**Feasibility: easy.** Twenty-four to thirty images. Six headline numbers per ward
if you take the abstracts, twenty-four if you take the age bands. No household-level
transcription at all.

Recommended procedure:

1. Open each ward's recapitulation frames from the table in §2 at full zoom in the
   Ancestry viewer on the signed-in browser (port 9333, ancestrylibrary.com).
2. Transcribe the grand-total line for the twelve free-coloured and twelve slave
   columns, plus the TOTAL column figure.
3. **Check each ward three ways** before recording it:
   - free white + free coloured + slaves = the ward TOTAL figure on the same line;
   - the per-page column entries above the total line add to the total line;
   - where a written abstract exists, its six figures match the column sums.
4. **Check the city three ways** against what we already hold:
   - Σ ward totals ≈ **102,225** (IPUMS complete count) and ≈ 102,313 (published);
   - Σ ward free coloured ≈ **17,958**;
   - Σ ward slaves ≈ **3,152**;
   - Σ ward Black ≈ **21,110** (20.65 %).
5. **Then compare against the printed volume's ward table** at
   `data/evidence/census1840/sixthcensus1840_p194_*` / `_p195_*`. Two independent
   sources for the same twelve numbers is a much stronger position than either alone.
   If they disagree, the manuscript is the earlier witness but the printed table is
   what contemporaries used; record both and say which the map uses.
6. Record for every figure: NARA M704 roll number, Ancestry image ID, the printed
   manuscript page number written on the leaf, the viewer URL, and the date of
   access. Save the page image.

If a figure will not reconcile, it is a transcription error, not a discovery.

---

## 7. What I did not establish

Stated plainly so nobody assumes otherwise:

- **The exact date the fourteen-ward ordinance took effect.** Established only that
  it is later than the June 1840 enumeration and appears in the 1842 directory.
- **The FamilySearch locator.** Film 0013183 is what Ancestry cites and what the
  film's own target plate reads, but the FamilySearch catalogue and DGS/ark were
  not confirmed — the site returned a sign-in page.
- **The NARA catalog NAIDs** for M704 rolls 158–161. Not checked.
- **Any actual population figure.** Ward 12's abstract (11,653; free coloured
  1,944; enslaved 304) is the only ward whose numbers I read carefully enough to
  believe, and even that should be re-read at full zoom before use. Ward 1's
  7,421 grand total is legible and internally consistent; the free-coloured and
  slave splits for ward 1 are **not** yet trustworthy from my reading. Everything
  else in this document is structure, not data.
- **Frame-exact physical ward boundaries.** The Ancestry block boundaries in §2 are
  exact (they come from the API). The physical boundaries — which single frame is a
  ward's last schedule page versus its first recapitulation page — were checked at
  every ward's tail but not at every ward's head.
- **Whether every ward carries a signed abstract**, as opposed to only the
  page-by-page recapitulation. Confirmed for wards 1, 6 and 12; the contact sheet
  shows prose-bearing leaves at other wards but I did not read them.

---

## 8. Methodological note

This record is a live demonstration of the failure mode recorded in the project
LOGBOOK for the 1820 volume. The eighteen most informative frames in the Baltimore
City sequence — the recapitulations — carry **no personal names**, and therefore
appear nowhere in Ancestry's index. A name search, a keyword search, or any query
that runs against the index rather than the images returns a clean, plausible,
complete-looking answer that omits precisely the pages that make the job tractable.

They were found by walking the frame sequence, noticing that the indexed image
counts per ward did not add up to the physical frame range, and then *opening the
gaps and looking at them*.

---

## Files

Written by this reconnaissance:

- `docs/census1840_manuscript_recon.md` (this file)
- `data/evidence/census1840/m704_*.jpg` — nineteen full-resolution page images
- `data/evidence/census1840/m704_contactsheet_ward_recapitulation_pages.png` — all
  twelve wards' recapitulation openings on one sheet

Consulted, not modified:

- `data/raw/hue/HUE_Baltimore_Wards/baltimore_wards_1832_1840.shp` (12 wards)
- `data/raw/hue/HUE_Baltimore_Wards/baltimore_wards_1841_1845.shp` (14 wards)
- `data/raw/matchettsbaltimo1837balt.txt`, `data/raw/matchettsbaltimo1842balt.txt`
- `data/raw/H_1840.csv` — IPUMS 1840 complete-count household file. Its header
  carries `stateicp`, `county`, `city`, `citypop` and no ward, enumeration-district
  or page variable. It cannot be aggregated to ward. That is the gap this record
  fills.
- `data/raw/census1840_md.pdf` — is the *Recapitulation of the Aggregate Value and
  Produce … in Mines, Agriculture, Commerce, Manufactures*, 12 pages, and it is a
  pure image scan: `pdftotext` extracts **12 characters from the whole file**. It
  contains no population data and no ward data. Any search run against it is
  meaningless.

All Ancestry access was through the Johns Hopkins Ancestry Library Edition licence
on ancestrylibrary.com, targeted lookups only, paced, no captcha or block
encountered.
