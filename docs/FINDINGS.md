# Mapping Black Baltimore, 1800–1860 — data feasibility findings

Status: reconnaissance complete, pilot parser working. 2026-08-07.

## Headline

**NHGIS cannot produce these maps.** It has no ward geography — the geographic
level simply does not exist in the NHGIS data finder for any year, and its
smallest historical unit for antebellum Baltimore is the county/city as a
whole. NHGIS gives one number per census year for the whole city. That is a
useful control total and nothing more.

**The city directories are the actual dataset**, and they are far better than
expected: several of them segregate Black residents into their own listing,
with name, occupation and address already separated out by the publisher. No
race inference is required.

## What exists

Baltimore directories on archive.org, with usable OCR, aligned to the target
census years:

| Target | Directory available | Black residents segregated? |
|---|---|---|
| 1800 | 1799 Mullin, 1803 Mullin | No — race unmarked |
| 1820 | 1816 Matchett, 1822 Keenan | 1822 yes, via `f` prefix flag |
| 1840 | 1837, 1842 Matchett | Yes — "COLORED HOUSEHOLDERS" section |
| 1860 | 1860 Wood's | Yes — "COLORED PERSONS" section, p.427 |

The 1822 Keenan directory flags free people of colour with a lowercase `f`
prefix on the entry (360 flagged entries). Occupations and addresses confirm
the reading: laundress, labourer, drayman, bootblack, concentrated in
Strawberry, Short and Homespun alleys.

## Two address grammars — the central technical fact

Baltimore had no systematic house numbering until roughly mid-century, so the
directories change addressing style partway through the period. These need
different geocoding methods and yield different spatial precision:

- **numbered** (dominant 1850+): `Adams Dennis, coachman, 11 Temple`
  → geocodable to a point by interpolation along a street segment.
- **relative** (dominant pre-1850): `Barnet Stephen, caulker, Wolfe st s of Fleet`
  → geocodable only to a **block face**, the stretch of one street between two
  intersections. Some entries also give the side of the street
  (`w side Strawberry al n of Gough st`), which pins it further.

Block-face resolution is still good for a large display panel: in dense
antebellum Baltimore a block face is a short stretch, and dots can be
distributed along it. But it is not a true per-person pinpoint, and the
exhibit copy should not claim one for the early years.

## Pilot results

`scripts/parse_directory.py` parses the segregated sections into a stable CSV
contract (`data/work/*_people.csv`):

| Year | Records | numbered | relative | street only |
|---|---|---|---|---|
| 1860 | 4,251 | 3,946 | 6 | 299 |
| 1842 | 2,724 | 43 | 2,139 | 542 |
| 1822 | 414 | 31 | 238 | 145 |

1860 and 1842 output is clean and usable. **1822 is not yet reliable** — the
Keenan OCR is much poorer and occupation text bleeds into the address field.
That year needs more parser work or re-OCR.

## Ward boundaries — solved, and better than georeferencing

The 1842 Matchett's directory contains, in its appendix, "PLAN OF THE WARDS":
the full text of the city ordinance dividing Baltimore into fourteen wards,
with complete metes-and-bounds for each one. Crucially the boundaries are
defined by **street centre lines** ("thence along the centre line of Fleet
street to the centre line of Bond street").

That means ward polygons can be reconstructed by tracing modern street
centrelines from Baltimore's open GIS data, for every street that still
exists, rather than by georeferencing a scanned paper map and digitising by
eye. This is more accurate and much faster. Directories for other years
carry the equivalent ordinance for their own ward configuration.

## What this changes about the original plan

1. Drop NHGIS as the spatial source. Keep it only for citywide control totals.
2. The hard work is OCR parsing and building a historic street gazetteer, not
   ArcGIS. ArcGIS is the last step, not the project.
3. "A pinpoint for each person" is achievable for 1860, and for free Black
   *households* at block-face resolution for 1842/1822. It is not achievable
   for 1800 — no directory of that era marks race, so there is no way to
   identify Black residents from the directory alone.
4. Enslaved people are largely invisible in directories by construction: they
   appear in the census under an owner's name, with no address. Any map of the
   enslaved population must come from census ward aggregates, not points, and
   must be presented as a different kind of layer.

## Open questions for the historians

- Is 1800 worth pursuing at all, given no race marking? An 1810 or 1816
  alternative may be more tractable.
- Should free and enslaved populations share a panel or get separate ones?
  The data structure differs so fundamentally that combining them on one map
  risks implying a precision the enslaved data does not have.

## Next steps

1. Build the historic street gazetteer (street name variants + OCR error
   forms → modern centreline geometry).
2. Geocode 1860 by address interpolation; 1842 by block face.
3. Reconstruct 1842 ward polygons from the ordinance text.
4. Improve the 1822 parser.

---

## Ward-level census availability, 1800–1860 (settled 2026-08-07)

How far back a ward choropleth can go is decided by whether the *published*
census volumes broke Baltimore out by ward. Checked directly, volume by volume:

| Year | Volume | Baltimore by ward? |
|---|---|---|
| 1860 | Eighth Census, Table No. 3, p.214 | **Yes** — 20 wards, white / free colored / slave |
| 1850 | Seventh Census, Table II, Maryland report p.221 | **Yes** — 20 wards, same categories |
| 1840 | Compendium of the Sixth Census | **No** — Maryland by county only; Baltimore is one row |
| 1820 | Census for 1820 | **No** — no ward tables; scan carries no text layer |

1830 and 1810 were not separately confirmed, but the 1840 volume's structure
makes it near-certain they are county-level too: the detailed
"Population of Cities and Towns" table with ward subdivision is an innovation
of the 1850 volume.

**Consequence for the map series.** Ward choropleths from published sources are
possible for **1850 and 1860 only**. The two share the same ward boundary set
(1846–1860), so they are exactly comparable, which is what makes the decade
comparison on the site trustworthy.

**The remaining route to earlier years** is not the published volumes but the
manuscript schedules, which *are* arranged by ward for Baltimore from 1820
onward. Deriving 1820/1830/1840 ward counts means tallying free-colored and
slave columns off the schedule images ward by ward. That is a real but bounded
transcription job, and it is the only way LJ's earlier panels become possible.
No microdata exists for those years: IPUMS full counts begin at 1850.

### 1850 vs 1860, the finding that came out of this

Black share of the city fell from **16.79% to 13.13%**, and fell in **every one
of the twenty wards**. The Black population itself barely moved (−490, −1.7%);
the white population grew by 43,854 (+31.2%). The enslaved population fell
faster, 2,946 to 2,218. Wards 11 and 14 held their share within a fifth of a
point while ward 17 lost ten points.
