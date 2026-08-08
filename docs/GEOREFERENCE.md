# Georeferencing the 1851 Sidney & Neff plan

Status: redone 2026-08-08. The numbers in the first version of this file were wrong. What
follows is the corrected result, with the first version's claims retained where they are needed
to explain what changed.

Method, standards and citations: **`docs/GEOREFERENCING_METHOD.md`**. Read that first if you
want to know why any of this is done the way it is.

## Headline

Sixty-eight ground control points, all read at full resolution off the Library of Congress
master, with world coordinates from modern survey sources rather than from the c.1930 HUE file.
A second-order polynomial fit gives a **leave-one-out cross-validated RMSE of 12.9 m**, which in
the form the federal accuracy standard asks for is:

> **Tested 22.3 metres horizontal accuracy at 95% confidence level**
> (FGDC-STD-007.3-1998, `Accuracy_r = 1.7308 * RMSE_r`)

Independently, on 21 check points that were located by a separate pass and never used in any
fit, the same transform returns **12.4 m RMSE**. Those two numbers agreeing is the reason to
believe either of them.

The sheet is a 1:7,800 publication at 0.626 m per master pixel, rotated 2.67 degrees from grid
north.

## What changed, and why the first numbers were wrong

The first pass reported **56 m RMSE** for the affine and 49 m for a second-order polynomial, and
shipped the affine. Both figures were wrong in kind as well as in size. Four reasons, in order of
how much damage each did.

**1. The control points were picked on an image four times too small.** `georeference_1851.py`
read pixel positions off `baltimore_1851_plan_preview.jpg` (3354x2661) and multiplied by four to
reach the 13414x10643 master. Street names are not legible at that size. Re-reading the master
shows the picks are not merely imprecise but wrong: Eutaw Street crosses Baltimore Street at
master x≈5917, and v1 recorded 6011. That is 94 pixels, about **59 m on the ground**, on one of
twelve points, in a fit whose whole reported error was 56 m. Two independent readings of the
master, made separately, agree with each other to 4 pixels and disagree with v1 by 94.

**2. Twelve points, seven of them on Baltimore Street.** The network was close to collinear. It
pinned the east-west axis and barely constrained anything across it, and it covered about a
quarter of the sheet. It also failed the federal minimum of 20 check points and the requirement
that at least 20 percent fall in each quadrant. Wards 19 and 20, wards 7 and 8, Canton, Locust
Point and Fort McHenry had no control at all, so every placement there was extrapolation.

**3. The RMSE was measured on the points the transform was fitted to.** That is a training
error, optimistically biased by construction, and the bias is worst exactly where v1 leaned on
it: the second-order fit spent 6 of its 12 available observations per axis on parameters, so its
apparent improvement over the affine was mostly the model fitting noise. No held-out point and
no cross validation appeared anywhere in v1.

**4. The reference layer was the layer being tested.** Every world coordinate came from the HUE
c.1930 street file, and the stated purpose was to measure disagreement with the HUE c.1930
street file. `docs/GEOREFERENCING_METHOD.md` section 3.3 works through exactly how much of the
v1 displacement finding that destroys. The short version is in the next section.

A fifth thing v1 did not do at all: it never tried a local transform. Thin plate spline is the
standard tool for warping an early map, `gdalwarp -tps` was already in the script's reach, and it
was not attempted.

## Does the circularity invalidate the displacement findings?

**Partly, and in a way that is now measurable.**

Destroyed: any absolute statement of where the 1851 map puts a feature, because the fit absorbed
whatever offset, rotation and scale error HUE carries. And any statement about the *average*
1851-to-1930 displacement, because least squares drives the mean disagreement with the reference
to zero, so the average v1 could measure was zero whatever the truth.

Survives: comparisons *between* two features measured through the same transform. A global affine
has no local freedom, so it cannot manufacture a 200 m difference between two things a few
hundred metres apart. The v1 finding that the Jones Falls channel lands 33-45 m from the modern
Fallsway while Front Street lands 220-260 m from HUE's `FRONT` is a differential statement and it
holds. Treat its magnitudes as lower bounds.

**And now the part that was not knowable before.** With the transform fitted to modern
centrelines instead, HUE can finally be measured rather than assumed. At the 50 control
intersections where both files carry the streets, the HUE c.1930 crossing sits a **median 2.4 m**
from the modern crossing (mean 3.1 m, 90th percentile 5.2 m, worst 14.7 m at Light & Hughes).
Per-point figures are the `hue_offset_m` column of `data/work/maps/gcps_1851.csv`.

So the c.1930 base layer that this project places residents against is within a few metres of a
modern survey wherever the street grid survived. **The seventy-year gap is not what is costing us
accuracy.** That reframes the original worry. The cost of using HUE is not spread thinly across
the whole city, it is concentrated in the specific places the grid did not survive: the Jones
Falls corridor, where Front Street no longer exists in any form, and the filled waterfront. Those
are identifiable and can be flagged individually rather than discounted globally.

It also reassigns the blame for the 56 m. Since HUE is only about 3 m from modern, almost none of
that number was HUE's error. It was v1's own.

## Which transform, and the thing only an independent check could find

Four models were fitted and compared: Helmert (4 parameters), affine, second-order polynomial,
and thin plate spline. Full tables in `docs/GEOREFERENCING_METHOD.md` section 3.4.

Fit on the 54-point control network, tested on the 21 independent check points:

| Model | Check-point RMSE | Inside control hull | Outside it | Worst |
|---|---:|---:|---:|---:|
| Helmert | 16.11 m | 14.78 m | 19.04 m | 26.6 m |
| Affine | 16.42 m | 14.46 m | 20.51 m | 36.3 m |
| **Polynomial 2** | **12.37 m** | 11.39 m | **14.54 m** | 23.9 m |
| Thin plate spline | 22.76 m | **12.15 m** | 38.00 m | 78.9 m |

Thin plate spline is the best model inside the hull and the worst outside it, by a factor of
2.6. Its radial basis grows without bound away from the control points, so where there is
nothing to hold it down it runs away: 78.9 m at Fort McHenry, which sits 2,600 pixels below the
lowest control point on the sheet. A second-order polynomial degrades gracefully in the same
place, 10.5 m at the same point.

No fit RMSE would have shown this. Neither would leave-one-out cross validation, because every
held-out point is by construction surrounded by the others. It took check points deliberately
placed outside the control hull. **The sheet is therefore warped with polynomial order 2**, on
the evidence of the check points rather than on the evidence of the fit.

Leave-one-out on the final combined 68-point network:

| Model | Fit RMSE (training) | LOOCV RMSE | NSSDA 95% |
|---|---:|---:|---:|
| Helmert | 15.89 m | 16.36 m | 28.31 m |
| Affine | 15.42 m | 16.22 m | 28.06 m |
| **Polynomial 2** | 11.80 m | **12.86 m** | **22.26 m** |
| Thin plate spline | 0.00 m | 14.35 m | 24.83 m |

The TPS row is the argument for cross validation in one line: a fit RMSE of exactly zero and a
real error of 14.35 m. Quoting that zero as an accuracy would have been a fabrication, and it is
the trap the first pass would have walked into had it tried TPS at all.

## How well can we even read this map?

Seven intersections were located twice, by two passes that had not seen each other's work. The
distance between the two picks measures the reading precision of the method, and no accuracy
claim can honestly be tighter than it.

| Intersection | Distance between the two picks |
|---|---:|
| Gay & Baltimore | 1.0 px (0.6 m) |
| Broadway & Monument | 1.0 px (0.6 m) |
| Broadway & Baltimore | 3.6 px (2.3 m) |
| Eutaw & Baltimore | 5.0 px (3.1 m) |
| Chester & Baltimore | 6.1 px (3.8 m) |
| Charles & Cross | 9.2 px (5.8 m) |
| Charles & Baltimore | 35.8 px (22.4 m) |

Median 5.0 px, 3.1 m. Six of seven under 4 m. Reading precision is therefore roughly a quarter
of the fitted accuracy, which means the 12.9 m is the map's error and not ours.

The outlier is a property of the object. Both passes independently noted that Charles Street
reads as a pale band rather than a crisp corridor, because **the sheet join runs down Charles
Street**, and both flagged x as the weaker coordinate before the two readings were compared.

## What was produced

- `scripts/georeference_1851_v2.py` — the 54-point control pass. Fits affine, polynomial 2 and
  TPS, cross validates, and measures HUE against modern at every control intersection.
- `scripts/georeference_1851_v2_check.py` — the independent check-point pass. Adds 21 points,
  reports inter-operator agreement, tests in-hull against out-of-hull, builds the final combined
  transform and warps the raster.
- `data/work/maps/gcps_1851.csv` — the 54 control points with per-point fit and leave-one-out
  residuals for every model, plus `hue_offset_m`.
- `data/work/maps/checkpoints_1851_v2.csv` — the 21 check points, their provenance, their OSM way
  ids, whether each is inside the control hull, per-model error, and the `gdal_translate -srcwin`
  crop box each pick was read from, so any pick can be reopened and argued with.
- `data/work/maps/gcps_1851_v2_combined.csv` — the final 68-point network with per-point LOO error.
- `data/work/maps/accuracy_1851_v2.json` — every statistic in this file, machine readable.
- `data/work/maps/baltimore_1851_v2.points` — QGIS Georeferencer format, EPSG:6487.
- `data/work/maps/baltimore_1851_georef_v2.tif` — the warped raster. Polynomial 2, EPSG:4326,
  27.2 MB.

`data/work/maps/baltimore_1851_georef.tif` now holds pass one's affine warp of the 54-point
control network, which replaced the original v1 raster in place. The v1 raster itself is
recoverable from git history at commit `2625137`. Use `baltimore_1851_georef_v2.tif`: it is
warped with the model the independent check points selected, and the affine is 4 m worse in the
interior and 6 m worse outside the control hull.

## Honest limits

**The bottom third of the sheet is extrapolation.** Control stops at master y=6653 on a sheet
10643 pixels tall, because almost none of Locust Point's 1851 street names survive. The single
observation below that line is Fort McHenry, where polynomial 2 is out by 10.5 m, which is
reassuring but is one point. Whetstone Point, Locust Point and the Middle Branch shore should be
treated as unverified.

**The northern strip is thin.** The highest control point is Greenmount & Lanvale at y=988, but
above roughly y=2000 the sheet is projected plat rather than built city: block outlines with no
legible street-name crossings, partly under the decorative border. There is no way to do better
from this sheet.

**Charles Street carries the sheet join.** Any placement whose x-coordinate is determined near
Charles Street inherits the 22 m disagreement documented above.

**Some features on this map are not control features and were deliberately not used.** Federal
Hill was quarried through the nineteenth century, so its 1851 outline is not its present one. The
harbour shoreline was filled. Patterson Park is 1,900 m across today and was a small "Paterson
Square" in 1851; matching one to the other would have injected a fabricated displacement of
several hundred metres. The reasoning is in `docs/GEOREFERENCING_METHOD.md` section 1.4.

**What 22 m at 95% confidence is good for.** Ward-level and block-level work, comfortably.
Corridor-level drift, as in the Jones Falls finding. It is not good enough to adjudicate a single
address to a specific side of a specific street, and no amount of further control points on this
sheet will make it so, because the map itself is not that accurate.

## Is this map already georeferenced anywhere else?

Once, badly. **Map Warper 37609** (https://mapwarper.net/maps/37609, accessed 2026-08-08) is this
exact sheet, warped in 2019 from a 4500x3650 derivative with **five** control points whose
reported errors include one of 98.7. It is a rough visual overlay, its GCPs cannot be transferred
to the Library of Congress master because the two images do not share an aspect ratio, and it
should not be used as a control source.

Worth knowing about: **Map Warper 109684** is Fielding Lucas Jr.'s 1836 plan of Baltimore, warped
from the Maryland State Archives scan with **151** control points and residuals mostly in the 8-35
range. Fifteen years off our sheet and the best independent period cross-check available.

Nothing else exists. David Rumsey does not hold this map at all. Allmaps has no city-scale
annotation for Baltimore of any date. The Library of Congress publishes the scan and no
georeferencing. NYPL's Map Warper is retired. Maryland State Archives, Digital Maryland and
JScholarship publish images, not georeferenced products. Full URLs and negative findings are in
`docs/GEOREFERENCING_METHOD.md` section 1.6.

So this is, as far as the machine-readable record goes, the first serious georeference of the
Sidney & Neff sheet.
