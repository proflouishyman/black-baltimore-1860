# Geocoding and census linkage plan (1860 pilot)

Supersedes the geocoding assumptions in FINDINGS.md. 2026-08-07.

## The anchor table — why 1860 geocodes precisely

Baltimore renumbered its houses in the 1880s, so 1860 house numbers do not
correspond to modern ones. That would normally make address-level geocoding of
an 1860 directory guesswork.

It does not here, because Wood's 1860 contains its own **Street Directory**
(pp. 509–529), which lists, for every street in the city, the house number
standing at each cross street, in separate Left and Right columns. Its own
worked example:

> "55 is on the N.E. corner of Charles and Saratoga-sts., hence the desired
> No. 71 will be between Saratoga and Pleasant-sts., right hand."

This is a house-number-to-intersection lookup table in 1860 numbering. It
removes the renumbering problem entirely: we never convert 1860 numbers to
modern ones, we locate them between two named intersections and interpolate.

**Extraction note.** The plain `_djvu.txt` OCR destroys this table by
flattening the columns into three decoupled runs (for AISQUITH: 10 left
numbers, 14 right numbers, 21 cross-street names, no alignment). The table
must be rebuilt from word coordinates in `_djvu.xml` / `_hocr.html`, pairing
numbers to street names by x/y position. Do not attempt this from the flat
text.

## Street geometry — modern centrelines are NOT the authority

The street grid has shifted, and in places vanished. Using modern Baltimore
centreline data as the geometric base would introduce large, *systematic*, and
spatially clustered error precisely where the Black population was densest.

Known high-change zones, where modern geometry must not be trusted:

- **Jones Falls corridor** — channelized and buried under the Fallsway and
  I-83. It was a ward boundary and a major reference line in 1860.
- **Harbor shoreline** — substantially filled since 1860. Waterfront addresses
  at Fell's Point and the city dock will project into what is now dry land.
- **Downtown urban renewal** — Charles Center and Inner Harbor clearance
  removed whole blocks and street stubs.
- **The alley network** — most of it is gone. This matters more than anything
  else on this list, because the alleys (Camel, Pin, Homespun, Strawberry,
  Welcome, Lerew's) are exactly where the Black population lived. An alley
  missing from modern data is a silently dropped record, not a visible error.

Approach instead:

1. Georeference a period map as the geometric authority. Candidates: the
   "Map of the City of Baltimore, corrected to date" bound into Wood's 1860
   itself; Sidney & Neff 1851; Sachse 1869; Hopkins 1876 atlas.
2. Digitize intersection points from that map.
3. Use modern centrelines only as a cross-check where the grid is provably
   unchanged, never as the source for the changed zones above.
4. Record a per-point confidence flag so the exhibit can distinguish a
   well-anchored address from an approximate one.

## Pipeline

    directory OCR ──> people records        (done: scripts/parse_directory.py)
    street directory ──> anchor table       (number, street, cross street, side)
    period map ──> intersection coordinates
    anchors + intersections ──> block-face geometry
    people + block faces ──> interpolated points + confidence flag

## Census cross-reference

IPUMS USA has the **1860 complete count** (100% sample, revised Nov 2023), not
just the 1% sample. Also available: 1850, 1870, 1880 at 100%, and an 1860 1%
sample with a Black oversample. Complete count means every named free person,
so this is true person-level linkage rather than statistical matching.

The two sources are complementary in a specific way:

- The **directory** has the street address. The 1860 census does *not* record
  street addresses, so the directory is the only route to a location.
- The **census** has the household: every member, ages, birthplace, occupation,
  real estate value and personal estate value, plus ward.

So linkage buys the map its depth. Each dot can be sized by household size or
shaded by wealth or birthplace, none of which the directory knows. The census
ward also independently validates the geocode: if an address interpolates into
Ward 11 but the census says Ward 17, the geocode is wrong.

Linkage method: block on surname plus first initial plus ward, score on
occupation agreement and plausibility, keep a match score on every record.
Expect partial linkage, not complete. Common surnames (Johnson, Brown,
Jackson) will generate false matches and must be scored down, not accepted.

Caveats to state in the exhibit:

- Directories systematically undercount the poor and transient. Wood's lists
  roughly 4,251 Black entries against a free Black population of over 25,000,
  so this is a map of listed householders, not of everyone.
- **Enslaved people cannot be mapped as points at all.** They appear on
  separate slave schedules under an owner's name with no address. They can
  only be a ward-level layer, and should be visually distinct from the point
  layer so the map does not imply a precision that does not exist.

## Ward polygons

Both directories carry the ward ordinance text with metes-and-bounds defined
by street centre lines: 1842 in its appendix ("PLAN OF THE WARDS"), 1860 at
p. 530 ("Boundaries of the Wards"). Ward polygons are reconstructed by tracing
those descriptions across the georeferenced period map, subject to the same
street-shift caution above.
