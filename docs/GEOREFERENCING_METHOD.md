# How historical map georeferencing is actually done, and what our first attempt got wrong

Written 2026-08-08. All external sources were fetched on 2026-08-08 and the URL is given
in each case.

This document has three jobs. First, to set out what cartographic and GIS practice
actually requires of a georeference, with citations. Second, to list bluntly what the
first pass at `scripts/georeference_1851.py` skipped. Third, to define the method that
`scripts/georeference_1851_v2.py` implements.

---

## 1. The standard

### 1.1 How many control points, and distributed how

The governing document in the United States is the **Federal Geographic Data Committee's
National Standard for Spatial Data Accuracy** (NSSDA), FGDC-STD-007.3-1998, part 3 of the
Geospatial Positioning Accuracy Standards.
Source: https://www.fgdc.gov/standards/projects/accuracy/part3/chapter3 (accessed 2026-08-08).

Three requirements matter here, quoted from that document:

> "A minimum of 20 check points shall be tested, distributed to reflect the geographic
> area of interest and the distribution of error in the dataset."

> "For a dataset covering a rectangular area that is believed to have uniform positional
> accuracy, check points may be distributed so that points are spaced at intervals of at
> least 10 percent of the diagonal distance across the dataset and at least 20 percent of
> the points are located in each quadrant of the dataset."

> "If fewer than twenty points can be identified for testing, use an alternative means to
> evaluate the accuracy of the dataset."

The 20-point minimum and the quadrant rule are about *check* points, not control points,
which is a distinction this project got wrong and which section 1.3 returns to.

On control points specifically, Esri's georeferencing documentation is the practitioner
standard and says the same thing about distribution.
Source: https://desktop.arcgis.com/en/arcmap/latest/manage-data/raster-and-images/fundamentals-for-georeferencing-a-raster-dataset.htm
(accessed 2026-08-08):

> "The number of links you need to create depends on the complexity of the transformation
> you plan to use... However, adding more links will not necessarily yield a better
> registration. **If possible, you should spread the links over the entire raster dataset
> rather than concentrating them in one area. Typically, having at least one link near each
> corner of the raster dataset and a few throughout the interior produces the best results.**"

And on the points-per-parameter question, from the same page:

> "The number of the noncorrelated control points required for this method must be one for
> a zero-order shift, three for a first-order affine, six for a second order, and 10 for a
> third order."

Those are *minimums*, at which the fit is exactly determined and the residuals are
identically zero. There is no formal rule of thumb such as "3n points for n parameters" in
the standards, but the cartographic-heritage literature is explicit that redundancy is what
makes the fit meaningful. Balletti, "Georeference in the analysis of the geometric content
of early maps," *e-Perimetron* 1(1), 2006, p. 34
(source: http://www.e-perimetron.org/Vol_1_1/Balletti/Balletti.pdf, accessed 2026-08-08):

> "the larger is the number of the control points used for the computation of the parameters
> the better statistical solution is achieved... In a computational process the number of the
> control points should be always more that the unknown parameters."

The practical consequence for a single map sheet: 20 or more well-distributed points, with
coverage of the convex hull rather than raw count as the binding constraint, and points near
each corner. Coverage matters because every global transform *extrapolates* outside the hull
of its control points, and extrapolation error grows without bound.

### 1.2 Which transformation, and when

The QGIS Georeferencer documentation is the clearest short statement of the menu and the
minimums. Source:
https://docs.qgis.org/latest/en/docs/user_manual/managing_data_source/georeferencer.html
(accessed 2026-08-08).

| Transform | Minimum GCPs | Free parameters (per axis) | What it can absorb |
|---|---|---|---|
| Linear (translation + scale) | 2 | 2 | position, uniform scale |
| Helmert (similarity) | 2 | 2 (4 total) | position, scale, rotation |
| Polynomial 1 (affine) | 3 | 3 | position, scale, rotation, shear, anisotropic scale |
| Projective | 4 | 4 (8 total) | central projection between two non-parallel planes |
| Polynomial 2 | 6 | 6 | smooth curvature across the whole sheet |
| Polynomial 3 | 10 | 10 | stronger smooth curvature |
| Thin plate spline | 10 (QGIS says "usually more") | n + 3 | arbitrary local deformation |

QGIS on polynomial 2 and 3: they "account for curvature and systematic warping" but
"straight lines may become curved" and they introduce edge distortion.

QGIS on thin plate spline, quoted:

> "TPS will precisely match all specified GCPs, but may introduce significant deformations
> between nearby GCPs with registration errors."

GDAL exposes the same choice. `gdalwarp -order` takes "order of polynomial used for warping
(1 to 3). The default is to select a polynomial order based on the number of GCPs" and
`gdalwarp -tps` will "Force use of Thin Plate Spline transformer based on available GCPs."
GDAL also has `-refine_gcps`, which "Refines the GCPs by automatically eliminating outliers,"
though it only works with polynomial interpolation.
Source: https://gdal.org/en/stable/programs/gdalwarp.html (accessed 2026-08-08).

The conceptual distinction that matters is global versus local. Balletti (2006), p. 34,
again:

> "It is called global the transformation due to which the best possible metric reference is
> assigned to the ungeoreferenced map, **without keeping unaltered, after the transformation,
> the coordinates of the control points**. On the other hand, **it is called local the
> transformation, which keeps unchanged the coordinates of the control points** after the
> transformation."

A hand-compiled 1851 city plan is not a projection of the ground through a single global
mathematical relation. It is a compilation of separately surveyed districts drawn, engraved
and printed, then aged on paper. Its errors are *local*: one block is out by 20 m, the block
next to it is out by 5 m in the other direction, and no six-parameter or twelve-parameter
global function can absorb both. That is the case for a local transform such as thin plate
spline, and it is why TPS is the normal choice for warping early maps for overlay.

The cost of TPS is stated plainly by Esri, and this is the sentence that matters most for
this project. Source as in 1.1:

> "**Although the RMS error is a good assessment of the transformation's accuracy, don't
> confuse a low RMS error with an accurate registration.** ... **Typically, the adjust and
> spline transformations give an RMS of nearly zero or zero; however, this does not mean that
> the image will be perfectly georeferenced.**"

TPS interpolates exactly. Its residual at every control point is zero by construction. An
RMSE computed on the fitting points is therefore not a number at all for TPS, and reporting
one would be a fabrication.

### 1.3 How accuracy is actually validated

This is the part our first pass did not do at all.

NSSDA defines RMSE against **an independent source of higher accuracy**, not against the data
used to build the product:

> "RMSE is the square root of the average of the set of squared differences between dataset
> coordinate values and coordinate values from an **independent source of higher accuracy** for
> identical points."

> "According to the Spatial Data Transfer Standard (SDTS), accuracy testing by an independent
> source of higher accuracy is the preferred test for positional accuracy."

Reporting is at the 95% confidence level, computed from the horizontal RMSE:

> "Accuracy_r = 2.4477 * RMSE_x = 2.4477 * RMSE_y = 2.4477 * RMSE_r / 1.4142 = **1.7308 * RMSE_r**"

and stated in the form "Tested ____ meters horizontal accuracy at 95% confidence level."

Fitting a transform to n points and then reporting the RMSE of that same transform at those
same n points is a training-set error. It is optimistically biased by construction, and the
bias grows with the number of free parameters. With 12 points and a 6-parameter-per-axis
second-order polynomial there are only 6 degrees of freedom per axis left, so the reported
number is close to meaningless as an estimate of accuracy anywhere else on the sheet.

Two accepted remedies:

1. **Held-out check points.** Locate more points than you fit. Fit on one subset, measure on
   a disjoint subset. This is what NSSDA's "independent" language amounts to when the only
   available higher-accuracy source is the same reference layer.
2. **Leave-one-out or k-fold cross validation.** Refit the transform n times, each time
   omitting one control point, and measure the error at the omitted point. The mean squared
   omitted-point error is an almost-unbiased estimate of the error the transform will make at
   a *new* point. This is standard practice in the recent literature on historical-map
   georeferencing: for example, the 2026 *Open Geosciences* paper on batch georeferencing of
   historical urban maps reports separate "validation points" distinct from the GCPs and
   quotes RMSE at those validation points, not at the fit
   (https://doi.org/10.1515/geo-2025-0919, accessed 2026-08-08). That paper's headline result
   is worth keeping in view as a benchmark: for urban maps at 1:5,000 to 1:20,000 it reports
   RMSE "between 25.96 m and 66.25 m," which is the band a 1851 Baltimore city plan should be
   expected to land in.

Cross validation also solves the TPS reporting problem. TPS has no fit residual, but it has a
perfectly well-defined leave-one-out error, and that number is directly comparable to the
leave-one-out error of the affine and polynomial fits. That comparison is the honest way to
decide whether TPS is buying anything real or only buying the appearance of precision.

### 1.4 Which features are stable over 175 years, and which are traps

NSSDA defines what qualifies:

> "For graphic maps and vector data, suitable well-defined points represent **right-angle
> intersections of roads, railroads, or other linear mapped features**, such as canals,
> ditches, trails, fence lines, and pipelines."

Note "right-angle." A crossing of two streets that meet at a shallow angle is intrinsically
harder to pick, because a small error along one line moves the apparent crossing a long way.

For Baltimore specifically, the ranking is:

**Reliable.**
- Standing masonry monuments from before 1851 that have never moved: the Washington Monument
  (1815-1829), the Battle Monument (1815-1825), the Phoenix Shot Tower (1828).
- Public squares whose boundaries are defined by the surrounding street grid and which were
  laid out before 1851: Union Square (1847), Franklin Square (1839).
- Fort McHenry's star, a masonry fortification of 1798-1803 whose geometry is fixed.
- Square street intersections in the built-up core where both streets survive under a
  traceable name.

**Use with care.**
- Named street intersections in the parts of the sheet that were *platted but not built* in
  1851. The engraver drew a projected grid; a projected grid is a proposal, and the built
  street may not have landed where the plat said. The far north of this sheet is almost
  entirely of this kind.
- Large building footprints. A church block is 40-80 m across, so picking its centre carries
  20-40 m of ambiguity before any map error.

**Traps.**
- **Shorelines.** Baltimore's harbour edge has been filled, cut and rebuilt continuously. The
  1851 shoreline is a historical fact, not a control feature.
- **Federal Hill.** The hill was quarried through the nineteenth century. Its 1851 outline is
  not its present outline. This is the reason no Federal Hill control point appears in the v2
  set, despite it being an obvious-looking landmark.
- **The Jones Falls.** Channelised and then culverted. The stream on the map and the Fallsway
  today are not the same object.
- **Parks that grew.** Patterson Park is 1900 m across today and was a small "Paterson Square"
  in 1851. Using the modern park's centroid against the 1851 square's centroid would inject a
  fabricated displacement of several hundred metres.
- **Cemeteries.** Boundaries drawn schematically, and several of the ones on this sheet were
  later moved.

### 1.5 What the reference layer should be, and the circularity question

If the research question is "how far does the 1851 map disagree with layer X," then layer X
must not be the source of the control coordinates. Fitting a least-squares transform to
control coordinates taken from X *drives the mean disagreement with X to zero by
construction*. The transform will absorb any translation, rotation, scale and shear that
separates the map from X, and the residuals that remain will be a mixture of map drafting
error, pixel-picking error and genuine local displacement, with no way to separate them.

The correct reference for control is an independent modern survey. For this project that
means:

- **Baltimore City road centrelines** (`data/raw/balt_streets.geojson`), a modern municipal
  survey product, for street intersections.
- **OpenStreetMap** geometry for standing monuments, forts and squares, queried via the
  Overpass API (https://overpass-api.de/api/interpreter, accessed 2026-08-08). Cross-checked
  where possible against the **Maryland Inventory of Historic Properties**
  (`data/raw/mihp_baltimore.geojson`, Maryland Historical Trust). For the Washington Monument,
  the Battle Monument and the Shot Tower the two sources agree to the fifth decimal of a
  degree, which is a useful independent confirmation that both are right.

Neither of these is the HUE c.1930 street file. That leaves HUE free to be *measured* rather
than assumed.

### 1.6 Is this map already georeferenced by someone else?

Yes, once, badly, and the search for it produced two things worth recording.

**Map Warper map 37609**, https://mapwarper.net/maps/37609, is titled "Baltimore 1851" and
described "Map of Baltimore, Sydney Neff." It is the same sheet. Status `warped`, created
2019-02-20. It has **five** ground control points, whose reported errors are 3.0, 98.7, 25.9,
42.6 and 27.3. One point is out by roughly 99 units. It was warped from a 4500x3650
derivative, not from the Library of Congress master (13414x10643), and the two do not share an
aspect ratio, so its GCPs cannot be transferred to the master image. GCPs are readable at
https://mapwarper.net/api/v1/maps/37609/gcps and tiles at
https://mapwarper.net/maps/tile/37609/{z}/{x}/{y}.png (all accessed 2026-08-08). It is useful
as a rough visual sanity overlay and as nothing else.

**Map Warper map 109684**, https://mapwarper.net/maps/109684, is Fielding Lucas Jr.'s *Plan of
the City of Baltimore*, 1836, warped from the Maryland State Archives scan
(https://msa.maryland.gov/msa/mdslavery/html/mapped_images/bacmap_lucas1836.html) with **151
GCPs** and residuals mostly in the 8-35 range. That is a serious piece of work and it is only
fifteen years off our sheet. It is the best available independent period cross-check, and its
GCPs are at https://mapwarper.net/api/v1/maps/109684/gcps.

Negative findings, all checked 2026-08-08:
- **David Rumsey** does not hold this map. Searching its Luna API for "Sidney Neff" returns 0
  results; "Poppleton" returns 0. Its Baltimore holdings are mostly small atlas maps at
  1:21,000 or coarser. Its Georeferencer instance now sits behind a Cloudflare challenge and
  its `/api/v1/maps` endpoint silently ignores query filters, so no claim about Rumsey's
  georeferenced holdings should be made from it.
- **Allmaps** has no city-scale annotation for Baltimore. Querying
  https://api.allmaps.org/maps.geojson for annotations intersecting Baltimore returns 96
  maps, of which the smallest spans 170.6 degrees of longitude. They are all world or
  continental maps that happen to overlap. The Library of Congress IIIF service for this sheet
  (https://tile.loc.gov/image-services/iiif/service:gmd:gmd384:g3844:g3844b:ct001132/info.json)
  is live and is a valid Allmaps target, so publishing a Georeference Annotation for it would
  be a genuine contribution.
- **The Library of Congress** provides the scan and nothing else: no GCPs, no navPlace, no
  GeoTIFF. Item metadata at https://www.loc.gov/item/2004629026/?fo=json. Rights: free to use
  and reuse.
- **NYPL Map Warper** is retired and now redirects to an Archive-It capture.
- **Maryland State Archives**, **Digital Maryland** and **JScholarship** publish images, not
  georeferenced products. Digital Maryland returns 0 results for "Sidney Neff."

So: no scholarly georeference of this sheet exists. Ours, done properly, would be the first.

---

## 2. What the first attempt skipped or got wrong

Stated bluntly, as requested. Six things.

### 2.1 Twelve control points, seven of them on one street

`data/work/maps/gcps_1851.csv` has 12 points. Seven of them (Charles, Calvert, Eutaw, Gay,
Broadway, Fremont, Poppleton, all crossed with Baltimore Street) lie within 60 preview pixels
of y=1100. The control network is close to collinear. A near-collinear network is well
conditioned along the line and poorly conditioned across it, so the reported RMSE is
effectively a Baltimore Street figure and says almost nothing about error to the north or
south of that corridor.

It also fails the NSSDA count (12 < 20) and fails the quadrant rule outright: the points span
preview x 1100-2413 of 3354 and y 498-1660 of 2661, which is roughly a quarter of the sheet's
area, entirely in the built-up core. Wards 19 and 20 in the west, wards 7 and 8 in the
north-east, Locust Point, Canton and Fort McHenry had **no control at all**, and every
placement in those areas was pure extrapolation.

The v1 documentation was honest that this was a weakness. It was not honest that it invalidates
the headline number.

### 2.2 The control points were picked on a 4x downsampled image

This is the error that was not previously identified, and it is the largest single one.

`georeference_1851.py` reads pixel positions off
`data/raw/maps/baltimore_1851_plan_preview.jpg`, which is 3354x2661, and then multiplies by 4
to reach the 13414x10643 master. Every pick therefore carries a *minimum* quantisation of 4
master pixels, and in practice much more, because street names are not legible on the preview
and the picks were made by eye against a coarse grid overlay.

Re-reading the master at full resolution shows the picks are not merely imprecise, they are
wrong. Eutaw Street crosses Baltimore Street at master pixel x≈5919. v1 recorded 6011. That is
92 pixels, about **57 m on the ground**, on a single point, and it is a misreading rather than
a map error: at full resolution the Eutaw Street corridor is unambiguous, 5900 to 5938, with
the Eutaw House hotel labelled on its north-west corner.

A 57 m pick error on one of twelve points, in a fit whose total reported RMSE is 56 m, is not
a detail.

### 2.3 The world coordinates came from the layer the map was supposed to be tested against

Every control coordinate in v1 was obtained by intersecting two named streets in the **HUE
c.1930 street file** via `geocode_1860.load_streets()`. The stated purpose of the exercise was
to measure how far the 1851 map disagrees with that same HUE file.

See section 3.2 below for exactly how much of the v1 displacement finding this destroys and
how much survives. The short version: it is fatal to any *absolute* displacement number and
it systematically understates displacement everywhere, because least squares drives the mean
disagreement with the reference to zero. It is not fatal to *relative* comparisons between two
features measured on the same fitted transform.

### 2.4 RMSE was computed on the fitting points

`fit_affine()` and `fit_poly2()` both compute residuals at the same 12 points used to solve the
normal equations, and `docs/GEOREFERENCE.md` reports those as "56m RMSE" and "49m". Those are
training errors. No held-out point, no cross validation, no independent check point was used
anywhere in v1.

The 49 m second-order figure is the worse of the two, because the second-order fit spends 6 of
its 12 available observations per axis on parameters. Its apparent improvement over the affine
is mostly the model fitting noise.

### 2.5 No local transform was tried

v1 fit a 6-parameter affine and a 12-parameter second-order polynomial, and shipped the affine.
Thin plate spline, the standard tool for exactly this problem, was never attempted, and the
tooling to do it (`gdalwarp -tps`) was already in use in the same script.

### 2.6 Two points were dropped for the wrong reason

v1 dropped Charles & Monument and Orleans & Front because *the HUE reference geometry* had gaps
there. Both are resolvable against modern geometry, and Charles & Monument in particular is the
Washington Monument, one of the best control features on the entire sheet: a 15 m square
masonry base, drawn on the map with a distinctive cross-hatched symbol, standing on the same
spot since 1829. Dropping it was a consequence of the circular reference choice, not of any
problem with the map.

---

## 3. The method used in v2

### 3.1 Control, in two independent passes

The redo was done twice over, by two passes working separately on the same Library of Congress
master, and that turned out to matter more than any single methodological choice.

**Pass one**, `scripts/georeference_1851_v2.py`, produced **54 control points**, written with
per-point fit and leave-one-out residuals to `data/work/maps/gcps_1851.csv`.

**Pass two**, `scripts/georeference_1851_v2_check.py`, produced **21 further points**, located
before the 54-point table was seen, and therefore usable as genuine NSSDA check points. Fourteen
are street crossings. Seven are standing physical structures with no dependence on street
naming at all: the Washington Monument, the Battle Monument, Union Square, Franklin Square, the
Fort McHenry star and the Mount Clare mansion.

Every point in both passes was located by cropping the **full-resolution** JPEG 2000 with
`gdal_translate -srcwin` and reading the crop back visually with a labelled pixel grid
overlaid. Nothing was carried over from v1 and nothing was inferred from a transform without
visual confirmation. Crop boxes are recorded per point so any pick can be re-opened and argued
with from the source image.

World coordinates come from modern sources only, never from HUE:

- Baltimore City road centrelines for street intersections.
- OpenStreetMap way geometry for the monuments, squares, fort and mansion, cross-checked against
  the Maryland Inventory of Historic Properties where both hold the feature. For the Washington
  Monument, the Battle Monument and the Shot Tower the two agree to the fifth decimal of a
  degree.

Coverage improves from roughly a quarter of the sheet to most of it. The control network spans
master x 2989-12528 and y 988-6653; adding the check points extends that to x 2600-12528 and
y 988-9251. v1 spanned x 4399-9651 and y 1992-6639.

The one substantial gap is the **bottom third of the sheet**. Pass one deliberately excluded
Locust Point, because almost none of its 1851 street names survive, so its control stops at
y=6653 on a sheet 10643 pixels tall. Everything below that line, including Whetstone Point,
Locust Point and the Middle Branch shore, is extrapolation. The Fort McHenry check point at
y=9251 is the only observation anywhere in that band, and section 3.4 reports what it costs.

### 3.2 Inter-operator agreement, and why it is the floor on any accuracy claim

Seven intersections were located by both passes independently. The distance between the two
picks is a direct measurement of the reading precision of the method, and no accuracy claim can
honestly be tighter than it.

| Intersection | Pixel distance between the two picks | On the ground |
|---|---:|---:|
| Gay & Baltimore | 1.0 px | 0.6 m |
| Broadway & Monument | 1.0 px | 0.6 m |
| Broadway & Baltimore | 3.6 px | 2.3 m |
| Eutaw & Baltimore | 5.0 px | 3.1 m |
| Chester & Baltimore | 6.1 px | 3.8 m |
| Charles & Cross | 9.2 px | 5.8 m |
| Charles & Baltimore | 35.8 px | 22.4 m |
| **median** | **5.0 px** | **3.1 m** |

Six of seven agree to within 6 pixels, under 4 m. That is the reading precision, and it is far
tighter than any of the fitted accuracies below, which means the residuals are dominated by the
map's own error rather than by our picking.

The outlier is instructive. Both passes independently noted that Charles Street reads as a pale
vertical band rather than a crisp corridor, because **the sheet join runs down Charles Street**.
Two readers, working separately, put the corridor centre 36 pixels apart, and both flagged the
x-coordinate as the weaker one before comparing notes. That is a property of the artefact, not
of the operators.

The agreement also settles the question of the v1 pick error at Eutaw & Baltimore. Pass one read
x=5915, pass two read x=5919. v1 recorded x=6011. Two independent full-resolution readings agree
to 4 pixels with each other and disagree with v1 by about 95 pixels, roughly 60 m. v1 is wrong
there, and it is wrong because it was read on a 4x downsampled preview.

### 3.3 The circularity question, answered

**Is v1's displacement finding invalid? Partly, and in a specific way.**

What is destroyed:

- Any *absolute* statement of the form "the 1851 map places feature F at coordinate C." The v1
  transform inherits whatever datum offset, rotation and scale error the HUE digitisation
  carries, because the fit absorbed all of it into its six parameters.
- Any statement about the *average* magnitude of 1851-versus-1930 displacement. Least squares
  sets the mean residual to zero. The average displacement v1 could measure was zero by
  construction, whatever the truth.
- The interpretation of the 56 m RMSE as "map accuracy." It is not. It is a mixture of map
  drafting error, pick error (see 2.2, which contributes tens of metres on at least one point)
  and real 1851-to-1930 street movement, and v1 has no way to separate the three. Reporting it
  as accuracy and then separately reporting displacement double-counts the same quantity.

What survives:

- **Relative comparisons between two features measured through the same transform.** The v1
  finding that the Jones Falls channel lands 33-45 m from the modern Fallsway while Front
  Street lands 220-260 m from HUE's `FRONT` is a *differential* statement. A global affine
  cannot introduce a 200 m difference between two features a few hundred metres apart, because
  it has no local freedom at all. So the qualitative finding, that the Falls corridor's street
  geometry has moved far more than the channel, is real and is not an artefact of the
  circularity. Its numbers should be treated as lower bounds.

The v2 method removes the circularity by sourcing control from modern surveys only. That makes
three separate, non-circular measurements possible, and v2 reports all three:

1. **Map accuracy**: leave-one-out error of the fitted transform against modern reference
   geometry. This is the number that belongs in the accuracy statement.
2. **HUE against modern**: at the same named intersections, the distance between the HUE c.1930
   crossing and the modern city-centreline crossing. No map involved at all. This isolates how
   much of the project's placement error is the base layer's rather than the directory's.
3. **1851 against HUE**: the georeferenced 1851 position compared to HUE. Now interpretable,
   because the transform was never fitted to HUE.

**Measurement 2 came back with a result that changes what this whole exercise was for.** At the
50 control intersections where both files carry the streets, the HUE c.1930 crossing sits a
**median of 2.4 m** from the modern city-centreline crossing, mean 3.1 m, 90th percentile 5.2 m,
worst case 14.7 m at Light & Hughes. Those figures are in `data/work/maps/gcps_1851.csv`, column
`hue_offset_m`.

The c.1930 base layer this project places residents against is therefore, at street
intersections in the built city, **within a few metres of a modern survey**. It is not the source
of the project's positional error. That was the open question the georeference was commissioned
to answer, and the answer is that the seventy-year gap costs almost nothing where the street grid
survives. What it costs is confined to the places where the grid did *not* survive, which is a
much smaller and much more identifiable problem: the Jones Falls corridor, where Front Street no
longer exists at all, and the filled waterfront.

It also relocates the blame for v1's 56 m. Since HUE is only ~3 m from modern, almost none of
that 56 m was HUE's error. It was v1's own: the downsampled picks of section 2.2 and the
collinear network of section 2.1.

### 3.4 Transforms fitted, and the result

Four, all fitted pixel to EPSG:6487 metres:

- **Helmert / similarity** (4 parameters): translation, rotation, one uniform scale. Note that
  raster rows count downwards while northings count upwards, so the pixel frame is left-handed
  with respect to the world frame and the row axis must be negated before fitting. A pure
  rotation has determinant +1 and cannot express that flip. Getting this wrong does not produce
  a slightly worse fit, it produces kilometre-scale nonsense, which is how the bug was caught.
- **Affine, polynomial order 1** (6 parameters per axis).
- **Polynomial order 2** (6 terms per axis).
- **Thin plate spline** (n + 3 parameters), implemented directly with the standard
  `U(r) = r^2 log r^2` radial basis so it can be cross validated with the same code as the
  others, and reproducible in GDAL with `gdalwarp -tps`.

**The independent check-point test.** Fit on the 54 control points only, then predict the 21
check points that were never used in the fit. In-hull and out-of-hull are reported separately
so the cost of extrapolation is visible rather than averaged away.

| Model | Check-point RMSE | In hull (15 pts) | Outside hull (6 pts) | Worst point | NSSDA 95% |
|---|---:|---:|---:|---:|---:|
| Helmert | 16.11 m | 14.78 m | 19.04 m | 26.6 m | 27.88 m |
| Affine | 16.42 m | 14.46 m | 20.51 m | 36.3 m | 28.42 m |
| **Polynomial 2** | **12.37 m** | **11.39 m** | **14.54 m** | **23.9 m** | **21.41 m** |
| Thin plate spline | 22.76 m | 12.15 m | 38.00 m | 78.9 m | 39.39 m |

**This is the finding that only an independent check could produce.** TPS is the best model
inside the control hull, 12.15 m against polynomial 2's 11.39 m, essentially a tie. Outside the
hull it is the worst by a wide margin: 38.00 m against 14.54 m, and 78.9 m at Fort McHenry. That
is not a surprise once stated, because the TPS radial basis `r^2 log r^2` grows without bound
away from the control points and has nothing to hold it down, whereas a second-order polynomial
degrades gracefully. But no fit RMSE and no leave-one-out figure would ever have shown it,
because both only ever ask about points surrounded by other points.

So the sheet is warped with **polynomial order 2**, on the evidence of the check points, not
with the model that fits the control best.

**Leave-one-out cross validation on the combined network.** The 54 control points plus the 14
check points that are more than 120 pixels from any control point, 68 in total. The other 7 are
held back: feeding a thin plate spline two near-coincident points with slightly different world
coordinates forces it to interpolate exactly through both, which demands an unbounded gradient
over a few pixels. The first run of the script did exactly that and TPS leave-one-out error blew
out to 96.7 m RMSE with a 735 m worst point. Deduplication is not tidying, it is a requirement
of the model.

| Model | Fit RMSE (training) | LOOCV RMSE | NSSDA 95% | Worst LOO point |
|---|---:|---:|---:|---:|
| Helmert | 15.89 m | 16.36 m | 28.31 m | 38.8 m |
| Affine | 15.42 m | 16.22 m | 28.06 m | 38.6 m |
| **Polynomial 2** | 11.80 m | **12.86 m** | **22.26 m** | 35.6 m |
| Thin plate spline | 0.00 m | 14.35 m | 24.83 m | 66.0 m |

The gap between fit RMSE and LOOCV RMSE is the optimism of the training error, and it is small
here, about 1 m, precisely because 68 points is a lot of redundancy against 6 parameters. It was
not small in v1, where 12 points fed 6 parameters. And the TPS row is the whole argument for
cross validation in one line: a fit RMSE of exactly zero, and a real error of 14.35 m.

**Headline accuracy.** Polynomial 2, leave-one-out RMSE **12.9 m**, which in NSSDA form is
**tested 22.3 m horizontal accuracy at 95% confidence level**.

**Sheet geometry.** From the Helmert fit, 0.6262 m per master pixel and a rotation of 2.666
degrees. Against the Library of Congress sheet dimension of 108 cm on the long axis, that is a
publication scale of roughly **1:7,800**. The rotation independently reproduces v1's figure of
2.67 degrees, which is reassuring: that one thing v1 got right, because rotation is exactly the
parameter a collinear east-west control network *can* constrain.

### 3.5 Outputs

Written to `data/work/maps/` with a `_v2` suffix. Nothing here overwrites a v1 artefact.

- `checkpoints_1851_v2.csv` — the 21 independent check points, their world coordinates and
  provenance, whether each falls inside the control hull, per-model error, and the
  `gdal_translate -srcwin` crop box each pick was read from.
- `gcps_1851_v2_combined.csv` — all 68 points of the final network with per-point leave-one-out
  error for each model, so a bad point is visible rather than buried in a summary.
- `accuracy_1851_v2.json` — every statistic quoted above, machine readable.
- `baltimore_1851_v2.points` — QGIS Georeferencer format, EPSG:6487.
- `baltimore_1851_georef_v2.tif` — the warped raster, polynomial 2, EPSG:4326, 27.2 MB, under
  the repository's 90 MB commit cap.
