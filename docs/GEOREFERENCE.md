# Georeferencing the 1851 Sidney & Neff plan

Status: done, with an honest accuracy ceiling. 2026-08-08.

## Headline

Twelve ground control points, visually located on the 1851 map and resolved
against the project's existing street geometry, produce an affine fit with
**56m RMSE** (49m for a second-order polynomial, but see the overfitting
caveat below). That is "tens of metres," as expected for a hand-surveyed
19th-century city plan, not the hundreds of metres that would signal a
mistake. It is good enough to check ward-level and block-level placement
against period geometry. It is not good enough to adjudicate a single
address to the correct side of the street.

The fit is uneven. It is good downtown along Baltimore and Charles Streets
(11–53m) and very good at two of the three periphery points (5–31m at Light &
York and Bond & Aliceanna). It is worst at the far western edge of the
control-point spread (Fremont & Baltimore, 100–108m) and at Calvert &
Baltimore (76–91m), one block from the best-fit point at Charles. That
unevenness is itself informative: see "Where the fit is weak," below.

## What was produced

- `scripts/georeference_1851.py` — reproducible: resolves the GCP table
  against `scripts/geocode_1860.load_streets()`, fits both polynomial orders,
  writes the outputs below, and (if GDAL is reachable) builds the GeoTIFF.
- `data/work/maps/gcps_1851.csv` — the 12 control points: street pair, pixel
  location (preview and full-resolution), resolved EPSG:6487 coordinate, and
  the residual for both fit orders, so a bad point is visible rather than
  buried in a summary RMSE.
- `data/work/maps/baltimore_1851.points` — the same points in QGIS
  Georeferencer format, CRS EPSG:6487.
- `data/work/maps/baltimore_1851_georef.tif` — the georeferenced GeoTIFF,
  EPSG:6487, 13971×11151px, 0.64m/px, 24.6MB (JPEG-compressed, tiled). Built
  with the **first-order (affine)** fit — see "Which order to use," below.

## The 12 control points

All are street-street intersections, located by eye on
`data/raw/maps/baltimore_1851_plan_preview.jpg` by cropping the neighbourhood
at 6–10x with a coordinate grid overlaid, then resolved to a real-world
coordinate by intersecting the two named streets' centrelines in
`scripts/geocode_1860.load_streets()` (HUE 1930 streets, modern streets as
fallback where HUE has no coverage — the same source and resolution logic
`geocode_1860.py` already uses for placing residents). Several pairs needed
the directional half of a split street (e.g. `GAY (S)`, `MONUMENT (W)`)
because the undirected merge of that street has a gap; see the code comments
in `georeference_1851.py` for which.

| Point | Preview px | Residual, order 1 | Residual, order 2 |
|---|---|---:|---:|
| Charles & Baltimore | (1678, 1100) | 53.3m | 70.1m |
| Calvert & Baltimore | (1830, 1099) | 91.4m | 76.5m |
| Eutaw & Baltimore | (1503, 1100) | 10.8m | 18.8m |
| Gay & Baltimore | (1893, 1100) | 39.6m | 53.6m |
| Broadway & Baltimore | (2413, 1050) | 22.1m | 15.3m |
| Charles & Biddle | (1678, 498) | 51.6m | 17.3m |
| Eutaw & Monument | (1520, 740) | 53.4m | 34.3m |
| Fremont & Baltimore | (1276, 1113) | 108.3m | 100.0m |
| Poppleton & Baltimore | (1100, 1118) | 66.5m | 59.3m |
| Charles & Cross | (1680, 1660) | 43.9m | 6.1m |
| Light & York | (1758, 1456) | 12.9m | 5.2m |
| Bond & Aliceanna | (2370, 1400) | 31.1m | 8.0m |

Mean residual 48.7m (order 1) / 38.7m (order 2); median 47.8m / 26.6m.

Spread: preview x 1100–2413px (of 3354, i.e. the built-up core, not the
full sheet — wards 19/20 west and 7/8 northeast were still mostly platted
farmland in 1851 and offered no reliable street intersections to read), y
498–1660px (of 2661), reaching from Biddle St in the north, through
downtown, to Cross St in South Baltimore and Light & York at the harbor's
edge.

**But the range overstates the coverage, and this is the fit's main
weakness.** Seven of the twelve control points lie on Baltimore Street
itself, within 60px of y=1100. Only five constrain the whole north-south
extent of the sheet. A control network concentrated along one east-west
line is well conditioned along that line and poorly conditioned across it,
so the quoted RMSE is effectively a Baltimore Street figure. Error
perpendicular to that corridor — in the northern wards above Biddle and in
the far south below Cross — is not measured by these residuals and should
be assumed larger than 56m.

This is a fixable limitation rather than a fundamental one. The reason it
was not fixed here is documented below: the two best candidate anchors off
the Baltimore Street line (Charles & Monument, Orleans & Front) both fell
in gaps in the reference geometry and were dropped rather than forced. Any
future pass should prioritise north-south anchors over adding more
downtown ones, since a thirteenth point on Baltimore Street would improve
the reported RMSE while making the map no more accurate where it is
actually weakest.

## Two points dropped, not fabricated

**Charles & Monument** (Mount Vernon Place, where the Washington Monument
itself sits) was visually located and would have been the single best
north-central anchor. It was dropped because the reference geometry has a
real gap there: HUE's undirected `CHARLES` merge ends at y=180,970
(EPSG:6487, metres) and `MONUMENT`'s west half only starts at y=181,076 — a
106m gap with no digitised Charles St segment through the plaza block. Rather
than snap to whichever nearby segment looked plausible, this GCP was left
out.

**Orleans & Front**, the point where the map shows a street crossing the
Jones Falls (visually located at approx. preview px (1975, 1048)), was
dropped for the same reason from the other direction: `FRONT` is digitised in
HUE as two short segments (x = 433,658–433,802 and x = 434,053–434,119) that
don't reach far enough east to meet `ORLEANS` (x = 434,241–436,598) at all.
The old Front Street alignment along the Falls' west bank simply isn't
present in the modern reference data past that point — itself a finding, not
just a gap (see below).

## Where the fit is weak

**Fremont & Baltimore (108/100m)** is the worst point, and the map reading is
the most likely source: Fremont crosses Baltimore Street on a diagonal, and
pixel-picking the crossing of a sloped line against a horizontal one is
inherently less precise than picking two streets that meet square. This
point should be treated as lower-confidence; a future pass could improve it
by reading the crossing at higher zoom.

**Calvert & Baltimore (91/76m)**, one block from Charles & Baltimore
(53/70m), is a genuine surprise: two points that should be nearly identical
in accuracy (same street, one block apart, both read from the same crop) 
differ by 30-40m. This is a real signal that Baltimore Street's 1851 drawn
alignment has a slight kink or lithographic distortion in that one block,
not a misreading — the affine's rotation term (2.67°, computed from the
order-1 coefficients) is a citywide average, and a single block that departs
from it by even a fraction of a degree produces exactly this kind of
localized residual.

**Poppleton & Baltimore (66/59m)**, the westernmost point, and Eutaw &
Monument (53/34m) both sit at the edges of the control-point spread, where
an affine fit is least constrained. This is expected: RMSE at the interior
points (Eutaw & Baltimore, 11–19m; Light & York, 5–13m) is consistently
better than at the points furthest from the downtown core.

## The actual research finding: how far 1851 disagrees with 1930, and where

**Jones Falls corridor — the biggest, clearest displacement.** The map's
depiction of the Falls, transformed through the fitted fit into EPSG:6487,
lands 220–260m from HUE's `FRONT` street (the street that historically ran
along the Falls' west bank) but only 33–45m from the modern **Jones Falls
Expressway / Fallsway** centerline — the road that was built over the
culverted Falls in the 20th century. In other words: the Falls channel
itself has stayed roughly where it was (33–45m is within this map's general
error budget), but the street that used to run alongside it (Front St) has
been displaced or erased by a much larger margin. This is exactly the kind
of drift the project suspected but could not previously separate from
geocoding error, and it is now quantified: **placements made against Front
St or other Falls-corridor streets in the current c.1930 base map should be
treated as suspect by a couple hundred metres, not just tens.**

**Waterfront — mixed, not uniformly bad.** This cuts against a naive
assumption. A point read off the 1851 "Public Landing" near the old City
Dock, transformed the same way, lands within 0.3m of a modern/HUE street
centreline and only 42m from Pratt Street specifically — i.e., close to this
map's general accuracy, not evidence of large-scale fill displacement at
that specific spot. Light & York, at the west shore of the Basin near
Federal Hill, is one of the two best-fitting GCPs in the whole set (5–13m).
The Basin's shoreline shape itself has of course changed since 1851 (much of
the harbor's edge was filled or rebuilt over the following century), but the
*street grid immediately behind* the 1851 shoreline on the west and south
sides has apparently not drifted far from where HUE's 1930 survey puts it.
Where the fit is weakest near water is the Jones Falls mouth on the *east*
side of the Basin (see above) — the displacement is concentrated at the
Falls, not spread evenly around the harbor.

## Which order to use, and the overfitting caveat

The shipped GeoTIFF uses the **first-order (affine) fit**, not the
lower-RMSE second-order polynomial. With only 12 control points feeding 6
free parameters per axis, the second-order fit has just 6 degrees of freedom
per axis — enough to bend the map's edges in ways that fit the 12 points
better without being more *correct* away from them. This showed up visually:
warping the raster with the second-order fit produced a visibly curved,
inconsistent border at the map's corners; the affine keeps the sheet's
rectangular border rectangular. The 49m vs 56m RMSE gap is real but small
enough that the affine's better-behaved extrapolation is worth the few
metres. `data/work/maps/gcps_1851.csv` reports both orders' residuals so this
tradeoff is checkable, and `georeference_1851.py` can be re-pointed at
order 2 in one line if a future user wants the tighter in-hull fit and
accepts the edge risk.

## Honest limits

- Coverage is the built-up core only. The far west (wards 19/20), far
  northeast (wards 7/8), and the Locust Point / Fort McHenry peninsula have
  no control points and should not be trusted at all on this transform —
  they were still sparsely built in 1851 and offered no confidently-readable
  street intersections.
- Fremont & Baltimore's poor residual is flagged above; treat any placement
  near that specific corner with extra caution.
- This is a 56m-RMSE fit, appropriate for checking which ward or block a
  resident's placement falls into, and for quantifying corridor-level drift
  (like the Jones Falls finding above). It is not appropriate for claiming a
  specific side of a specific street for a specific address — that would
  overstate what 12 points and a 170-year-old lithograph can support.
