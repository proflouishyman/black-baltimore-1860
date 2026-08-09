# The georeferenced series, 1822 to 1860: what it shows and what to do about it

Written 2026-08-08. This file synthesises five independently produced
georeferences (1822, 1836, 1851, 1857, 1860), each of which was separately
audited by a reviewer who recomputed the arithmetic from the control tables and
re-read control points off the scans. It is a synthesis, not a new
georeference. Every number below was either recomputed here from
`data/work/maps/gcps_*.csv` and `data/baltimore.db`, or is carried forward from
a review that verified it independently. Where I carried a number forward
rather than recomputing it, the text says so.

The question the series was built to answer: the project places every resident
against the HUE c.1930 street file (ICPSR 35617), which is seventy years later
than the earliest year we map, and an earlier pass had measured 220 to 260 m of
apparent displacement in the Jones Falls corridor. Is the c.1930 base layer the
project's dominant source of error?

**It is not, and the 220 to 260 m figure was a bug in our own reference
loader.** The rest of this file is the evidence and what follows from it.

---

## 1. The series at a glance

Headline is leave-one-out cross-validated RMSE for the shipped transform. Fit
RMSE is shown alongside because the gap between them is the honest measure of
how much a model is memorising its control points. TPS fit RMSE is 0.0 m on
every sheet by construction and is not an accuracy measure.

| Year | Sheet | GCPs | Shipped | Fit RMSE | **LOO RMSE** | LOO median | Blocked / held-out | Verdict |
|---|---|---:|---|---:|---:|---:|---:|---|
| 1822 | Poppleton, *Plan of the City of Baltimore* | 28 | TPS | 0.0 | **13.3 m** | 9.7 m | 16.9 m at 553 m control gap | Sound |
| 1836 | Lucas, *Plan of the City of Baltimore* | 42 | affine | 19.7 | **21.4 m** | 17.4 m | 25.8 m, 5 independent points | Sound |
| 1851 | Sidney & Neff, *Plan of the City of Baltimore* | 54 | poly 2 | 12.1 | **13.8 m** | 9.1 m | 12.4 m, 21 independent check points | **Best in series** |
| 1857 | Taylor, *Map of the City and County of Baltimore* | 39 | TPS | 0.0 | **25.1 m** | 19.4 m | 37.3 m at 400 m exclusion radius | **Weakest. Overstated headline** |
| 1860 | Woods / Sides, directory map | 27 | affine | 23.0 | **26.2 m** | 22.6 m | 29.7 m leave-one-cluster-out | Sound but coarse |

All three transforms, for comparison. Every one of these was reproduced from
the control tables by a reviewer working independently of the agent who
produced it, and agreed to within 0.06 m per point.

| Year | LOO affine | LOO poly 2 | LOO TPS | m per scan px | LOO TPS in scan px |
|---|---:|---:|---:|---:|---:|
| 1822 | 24.4 | 15.3 | 13.3 | 1.308 | 10.2 |
| 1836 | 21.4 | 18.5 | 15.1 | 1.308 | 11.5 |
| 1851 | 15.9 | 13.8 | 11.4 | 0.625 | 18.2 |
| 1857 | 42.9 | 35.0 | 25.1 | 1.681 | 14.9 |
| 1860 | 26.2 | 26.0 | 26.1 | 2.182 | 12.0 |

Network quality. The 1851 v1 attempt is included as the control case for what
a bad network looks like. Max leverage is the largest diagonal of the affine
hat matrix, that is, how much of the fit a single point can move.

| Year | GCPs | Control hull | Max leverage | Anisotropy | Busiest street | Residents in hull | Median resident distance to nearest GCP |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1822 | 28 | 8.12 km² | 0.168 | 1.22 | Baltimore 9/28 (32%) | 89.1% (1822) | 272 m |
| 1836 | 42 | 13.17 km² | 0.149 | 1.54 | Baltimore 9/42 (21%) | 92.6% (1842) | 359 m |
| 1851 | 54 | 13.94 km² | 0.101 | 1.67 | Baltimore 17/54 (31%) | 92.5% (1851) | 316 m |
| 1857 | 39 | 12.25 km² | 0.143 | 1.66 | Baltimore 8/39 (21%) | 90.3% (1860) | 379 m |
| 1860 | 27 | 13.99 km² | 0.186 | 1.67 | Baltimore 7/27 (26%) | 90.4% (1860) | 449 m |
| *1851 v1* | *12* | *5.60 km²* | *0.467* | *1.36* | *Baltimore 7/12 (58%)* | *not computed* | *not computed* |

### Where each result is weakest

Reading these honestly matters more than the headline numbers.

**1857 is the weakest sheet and its published headline is optimistic.** It is a
city *and county* map, so the city occupies a small fraction of a large sheet
and every scan pixel is worth 1.68 m of ground. The reviewer re-ran cross
validation with a spatial exclusion buffer, dropping every control point within
radius r of the held-out point, and got 25.1 m at r = 0, 28.1 m at 250 m,
37.3 m at 400 m and 59.9 m at 900 m. Residents sit a median 379 m from the
nearest control point, so **the defensible figure for 1857 is about 35 m RMSE,
not 25 m.** Separately, 10 of its 39 control points sit in the western zone
which the scan shows drawn as unhatched uniform rectangles with projected
street names, that is, platted but unbuilt. Those points anchor to a paper plat
rather than to a survey, and they are very likely the real cause of the
coherent 45 to 90 m western error the write-up attributes to plate distortion.

**1860 is the coarsest scan** at 2.18 m per pixel, and its 27-point network
collapses to only 12 distinct locations under single-linkage clustering at
250 px, because four pairs sit 50 to 60 px apart. Leave-one-cluster-out gives
29.7 m rather than 26.2 m. The reviewer also tested and rejected the
write-up's "coherent north-south bow consistent with a folded insert" story:
the residual field shows significant spatial autocorrelation only below 200 px,
which is the duplicate-pair scale, and none at 400 px and above.

**1822's headline is honest for the built core and not for the periphery.**
Spatial-block cross validation gives 13.3 m at a 247 m control gap, 16.9 m at
553 m and 38.6 m at 1186 m. Its control network is also more north-west
weighted than the write-up states: the actual quadrant split about the sheet
centre is 16 NW, 7 NE, 4 SW, 1 SE, not the 8 / 8 / 9 / 3 reported.

**1851 is the strongest result in the series** and is the only one carrying an
independent check-point set (21 points read by a second operator and never used
in the fit). Those check points favour poly 2 over affine both inside the
control hull (11.4 vs 14.5 m) and outside it (14.5 vs 20.5 m), and the shipped
model is now poly 2. Two hygiene problems remain in the repo: the superseded
`scripts/georeference_1851.py` still writes to the same output paths that the
v2 pass owns, so re-running it silently clobbers the better result, and
`docs/GEOREFERENCE.md` still asserts the 220 to 260 m Jones Falls displacement
that section 2 below shows to be an artifact. Neither file is mine to change.

---

## 2. How the mapped geometry drifts from the c.1930 street file

This is the research contribution, and the answer is a negative result on both
of the hypotheses that motivated the work.

### 2.1 The c.1930 file is not displaced from the modern survey

Four of the five georeferences carry an independently computed column comparing
the HUE c.1930 centrelines with a modern reference at the same named crossings.
None of these comparisons involves any period map or any fitted transform, so
they are not circular.

| Sheet | Modern reference | n | Median | p90 | Max |
|---|---|---:|---:|---:|---:|
| 1822 | Baltimore City centrelines | 28 | 2.4 m | 8.8 m | 26.3 m |
| 1851 | Baltimore City 911 StreetCity | 50 | 2.3 m | 4.9 m | 14.7 m |
| 1857 | OpenStreetMap | 39 | 2.3 m | 8.5 m | 11.8 m |
| 1860 | Baltimore City centrelines | 26 | 1.6 m | 8.8 m | 12.0 m |

One reviewer widened the 1851 test from the 40 hand-picked crossings to every
unambiguous same-name crossing inside the control bounding box, n = 2,085, and
got median 2.5 m, mean 4.9 m, p90 8.3 m, 92 percent under 10 m. A second
reviewer did the same inside the 1846-1860 ward boundary, n = 2,393, median
2.4 m, p90 11.2 m. There is a fat tail. The 1851 reviewer found p99 at 41.9 m
and 17 crossings over 50 m, worst Howard & Park at 332 m, and the 1857 reviewer
found a maximum of 3,509 m from name collisions such as Frederick Rd against
Frederick St. So HUE is typically excellent and occasionally grossly wrong at
individual crossings, which argues for a per-street sanity check rather than
for abandoning the layer.

The one caveat that survives: HUE's own metadata lists Census MAF/TIGER 2007 in
its lineage, which would make "HUE agrees with modern" tautological if HUE were
re-labelled TIGER geometry. It is not. Clipped to the 1846-1860 ward boundary,
HUE is 625.15 km of hand-digitised "CPE Overlay" against 0.87 km of TIGER2007,
that is, 99.86 percent hand-digitised, and all 78 segments carrying the 1857
control crossings are CPE Overlay. The TIGER content lives in the county and
the later annexations, outside the area this project maps.

### 2.2 The 220 to 260 m Jones Falls displacement was our bug

Two reviewers, working separately, traced it to the same place. It is not
ground movement and it is not a HUE error. `geocode_1860.load_streets()`
applies a ward clip and then a longest-connected-component merge, which returns
`('FRONT','N')` as a fragment spanning only y 180622 to 180906 in EPSG:6487.
The Jones Falls channel pixels on the period sheets sit at y 181076 to 181269,
north of where that truncated fragment ends, so a nearest-point distance to it
comes out at 188 to 393 m. Raw HUE's N Front St actually spans y 180281 to
181101.

The corridor checks that do not depend on the fit:

| Test | Result |
|---|---|
| 1836 sheet, 4 Falls channel pixels (never control points) to modern Fallsway centreline | 12.3, 8.2, 4.4, 10.6 m |
| 1851 sheet, reviewer's own reading of drawn Front Street at 3 points to HUE Front Street | 21.3, 12.4, 2.6 m |
| HUE Front St against modern Front St, sampled at 520 points along the corridor | median 0.6 m, max 3.6 m |

The 1851 sheet's channel readings sit 47 to 73 m from HUE Front Street and 7 to
257 m from the modern Fallsway, the divergence growing northward. That is
correct and expected. The Fallsway is a twentieth-century road built over the
culverted channel and it does not follow the old watercourse. Comparing an 1851
watercourse to the Fallsway is the mistake that produced the original number.

### 2.3 Displacement is not a function of date

If the city were being progressively resurveyed, earlier sheets should disagree
with the modern grid more than later ones. They do not. Pooling all 190 control
points and testing the five sheets:

| Predictor of LOO TPS RMSE | Spearman rho | p |
|---|---:|---:|
| Date of the map | **+0.70** | 0.188 |
| Metres of ground per scan pixel | **+0.97** | 0.005 |
| Number of control points | −0.70 | 0.188 |

The correlation with date is not significant at n = 5, and its sign is the
*opposite* of the resurvey hypothesis: the later sheets in this series are the
worse ones. What actually predicts accuracy is scan resolution. A linear fit
gives

> LOO TPS RMSE ≈ 2.8 m + 10.8 × (metres per scan pixel)

which reads as roughly eleven scan pixels of corridor-reading error plus a 3 m
floor. Expressed in scan pixels, all five sheets land in a narrow band of 10 to
18 px. After removing the scan-resolution effect the residual date effect is
+3.7 to −4.1 m and not significant (r = 0.81, p = 0.10, n = 5). **The limiting
factor across the whole series is how many pixels wide a street corridor is on
the scan, not the competence of the surveyor or the passage of time.**

The similarity parameters say the same thing more directly. Fitting each sheet
to the modern grid as a 4-parameter Helmert transform:

| Year | Scale (m/px) | Rotation | Anisotropy of the affine | Shear | Helmert LOO RMSE |
|---|---:|---:|---:|---:|---:|
| 1822 | 1.308 | −2.45° | 1.0032 | 0.16° | 23.4 m |
| 1836 | 1.308 | −2.73° | 1.0166 | 0.94° | 25.7 m |
| 1851 | 0.625 | −2.74° | 1.0054 | 0.14° | 16.3 m |
| 1857 | 1.681 | −3.34° | 1.0474 | 0.09° | 56.4 m |
| 1860 | 2.182 | −3.08° | 1.0072 | 0.01° | 25.9 m |

Every sheet from 1822 onward maps onto the modern grid under a near-pure
similarity. Axis scale anisotropy is 1.003 to 1.047 and shear is under one
degree everywhere. Poppleton's 1822 plat, the earliest and most remote from the
c.1930 file, is the *least* distorted of the five (anisotropy 1.0032, shear
0.16°) and reproduces 28 crossings across 8 km² at 24.4 m under a 6-parameter
affine. Baltimore's street grid in the built city has not moved measurably
between 1822 and now.

### 2.4 Nor is it dominated by the Jones Falls or the filled harbor

I classified all 190 control points across the five sheets by zone: within
300 m of the Fallsway / Central Avenue line, within 250 m of the modern
waterfront streets (Key Hwy, Thames, Boston, Aliceanna, Light south of Pratt),
or inland. Errors are affine LOO in metres, which is the transform-independent
comparison since three of the five sheets ship a different model.

| Zone | n | Median | Mean | vs inland |
|---|---:|---:|---:|---|
| Jones Falls corridor | 20 | **13.4 m** | 13.9 m | *better*, Mann-Whitney p = 0.031 |
| Waterfront | 48 | 20.6 m | 21.8 m | no difference, p = 0.448 |
| Inland | 122 | 18.0 m | 23.1 m | reference |

Per sheet, affine LOO median by zone:

| Year | Jones Falls | Waterfront | Inland |
|---|---:|---:|---:|
| 1822 | 13.3 | 23.1 | 23.1 |
| 1836 | 21.8 | 17.5 | 15.0 |
| 1851 | 11.1 | 11.7 | 10.8 |
| 1857 | 19.1 | 27.8 | 34.1 |
| 1860 | 9.2 | 29.8 | 23.4 |

Error *increases* with distance from the Jones Falls (Spearman +0.30,
p < 0.0001, n = 190), and it survives controlling for distance from the control
centroid (partial rank correlation +0.28, p = 0.0001), so it is not simply
"downtown is better sampled". The Falls corridor is the best-fitting part of
the city in this series, not the worst. This is the reverse of the finding that
motivated the whole exercise.

The waterfront result needs a caveat that the zone table cannot supply. All
five georeferences deliberately avoided shoreline and watercourse control
points, because those features genuinely did move. So the honest statement is
not "harbor fill causes no displacement" but "**we did not test it, because
there is no stable feature on filled land to test with**". The real filled-land
risk is not displacement at all, it is anachronism: HUE c.1930 contains streets
on land that was open water in 1822, and a resident whose address matches one
of those names by accident would be placed on water. That risk did not
materialise in the current data. Testing every geocoded resident against the
HUE period ward polygon for their own cohort:

| Cohort | n geocoded | Outside the period city | Max overshoot |
|---|---:|---:|---:|
| 1819 | 92 | 0 (0.0%) | 0 m |
| 1822 | 230 | 0 (0.0%) | 0 m |
| 1842 | 744 | 0 (0.0%) | 0 m |
| 1845 | 1,527 | 4 (0.3%) | 0 m |
| 1851 | 1,631 | 3 (0.2%) | 0 m |
| 1860 | 3,054 | 9 (0.3%) | 0 m |
| 1868 | 6,070 | 12 (0.2%) | 0 m |

### 2.5 The number that actually matters

Nothing above measures absolute displacement, and nothing can. Least squares
drives the mean disagreement between a warped sheet and its reference to zero
by construction, so no fit of this kind can detect a global shift, only local
distortion. Every reviewer flagged this independently and they are right. Two
of the write-ups present a "map vs HUE" row as though it were an independent
displacement measurement when it is arithmetically the fit residual
re-expressed. The 1822 reviewer quantified the leak precisely: `corr(loo_tps,
map1822_vs_hue) = 0.928`, mean absolute difference 1.88 m, medians 9.65 against
9.95.

What we can state, and what the project needs, is the operational quantity:
**how far would a resident move if you re-placed them on a period map instead
of on HUE?** That is bounded by the period map's own local disagreement with
the reference at the same crossings.

| Year | Measured map-vs-HUE at control crossings | Bound from fit residual |
|---|---|---|
| 1822 | median 9.9 m, p90 20.0, max 35.6 | 12.6 m RMSE (poly 2) |
| 1836 | not computed | 19.7 m RMSE (affine) |
| 1851 | not computed | 12.1 m RMSE (poly 2) |
| 1857 | not computed | 28.9 m RMSE (poly 2) |
| 1860 | median 22.4 m, p90 33.8, max 37.4 | 23.0 m RMSE (affine) |

**Ten to twenty-five metres. That is the entire prize for re-placing every
resident in the project on a period base layer.** Section 3 puts that next to
the errors already in the data.

---

## 3. Recommendation on the base layer

**Option (a). Keep the c.1930 HUE geometry as the coordinate base, state the
measured error, and spend the effort saved on the address ladder instead.**

The tradeoff in one sentence: keeping the c.1930 base costs nothing and leaves
a base-layer error of about 2 m median against a modern survey, whereas
re-placing every resident against a period sheet would cost weeks of work,
would move each person by only 10 to 25 m, and would move them in a direction
we cannot demonstrate is correct, because the fitted transform absorbs any
global offset by construction and the period sheets' own drafting error is the
same size as the correction they would supply.

Here is the error budget that makes this decision obvious. All three figures
are from this project's own data.

| Error source | Magnitude | Basis |
|---|---:|---|
| Base layer, HUE c.1930 against modern survey | **~2 m median** | 143 control crossings across four sheets, plus 2,085- and 2,393-crossing independent replications |
| Georeferencing a period sheet | **11 to 37 m** | LOO and blocked CV, this file, section 1 |
| Placing an address on the right stretch of street | **hundreds of metres** | see below |

The third row is the one that dominates, and it is an order of magnitude larger
than either of the others. Of 102 residents checked against the census in
`data/work/validation_summary.json`, 38 were found. Of those 38, **22 matched
the census ward exactly, 13 landed in an adjacent ward, and 3 landed neither**.
The median 1846-1860 ward has an area of 0.54 km², an equivalent diameter of
830 m. So roughly a third of externally validated placements are wrong by
several hundred metres. And that is with the easiest cases: 69 percent of the
1860 cohort and 71 percent of the 1868 cohort are placed by `street_proportional`,
which interpolates a house number along the whole length of a street rather
than between two known cross-street anchors.

Swapping a 2 m base-layer error for a 15 m period-map error, while a 400 m
address error sits untouched in the same pipeline, is not an improvement. It is
a category error about where the uncertainty lives.

Three things follow, and none of them is a second option.

1. **Publish the error, do not bury it.** The exhibit and `docs/` should carry a
   single sentence: street geometry is c.1930 and agrees with the modern survey
   to about 2 m in the built city, and individual placements are accurate to
   roughly a block, not to a house.
2. **Keep the georeferenced rasters, and use them as overlays and as evidence,
   not as a base.** They are what allows a visitor to see the 1851 city under
   the dots, and they are what allowed us to falsify the 220 m claim. That is
   worth the work already done. Publishing them as tile overlays costs a day.
3. **Reject option (c) explicitly.** Digitising period centrelines from the
   georeferenced sheets would inherit every one of the errors in section 1,
   so the resulting "period base layer" would be a c.1930 grid displaced by 11
   to 37 m of drafting and reading noise, plus weeks of tracing. What the
   period sheets *can* usefully supply is not geometry but topology: which
   streets existed in a given year, and how far they ran. That is a cheap read
   off the rasters and it attacks the 400 m error rather than the 2 m one.

---

## 4. What is still missing

### 4.1 Years with no georeferenced sheet

| Cohort | Residents geocoded | Share of the corpus | Nearest georeferenced sheet | Gap |
|---|---:|---:|---|---:|
| 1819 | 92 | 0.7% | 1822 Poppleton | 3 years |
| 1822 | 230 | 1.7% | 1822 Poppleton | 0 |
| 1842 | 744 | 5.6% | 1836 Lucas | 6 years |
| 1845 | 1,527 | 11.4% | 1851 Sidney & Neff | 6 years |
| 1851 | 1,631 | 12.2% | 1851 Sidney & Neff | 0 |
| 1860 | 3,054 | 22.9% | 1860 directory map | 0 |
| **1868** | **6,070** | **45.5%** | **none** | **—** |

**The single largest gap in the project is 1868.** It is the largest cohort by
a wide margin, 45.5 percent of all geocoded residents, and it is the only year
with no georeferenced period sheet at all. Everything the series has
established about the 1820s to 1860 is unverified for the year that carries
almost half the people on the map.

### 4.2 Scans on disk that have not been georeferenced

All eleven scans in `data/raw/maps/` were checked for pixel dimensions.

| Scan | Pixels | Status | Assessment |
|---|---|---|---|
| `baltimore_1856_full.jp2` Scott's map, LoC [2002624007](https://www.loc.gov/item/2002624007/) | 18,170 × 14,666 | **not georeferenced** | City only, ward-coloured, full street grid. The city body occupies roughly 70 percent of the sheet width, so about 0.7 m per pixel, comparable to the 1851 sheet and 2.4× finer than the 1857 sheet currently serving 1860. **This is the largest missed opportunity in the collection.** |
| `baltimore_1866_full.jp2` Woods / Sides, LoC [2020587113](https://www.loc.gov/item/2020587113/) | 6,073 × 4,450 | **not georeferenced** | Direct successor to the 1860 directory map, same surveyor and publisher, city only with the redrawn wards. About 2.2 m per pixel, the same class as the 1860 sheet that reached 26 m. **This is the sheet that closes the 1868 gap.** |
| `baltimore_1823_full.jp2` LoC [77691538](https://www.loc.gov/item/77691538/) | 15,196 × 13,376 | not georeferenced | 2.2× the linear resolution of the 1822 scan already used, one year later. Would roughly halve the 1822 cohort's error if the 10.8 m per m/px relation in section 2.3 holds. |
| `baltimore_1876_full.jp2` LoC [2020587065](https://www.loc.gov/item/2020587065/) | 6,477 × 4,592 | not georeferenced | Eight years after the last cohort. Low priority. |
| `baltimore_1844_full.jp2` LoC [2020587086](https://www.loc.gov/item/2020587086/) | 3,816 × 3,936 | not usable at this resolution | One year before the 1845 cohort, which is what makes it tempting, but at roughly 2.5 m per pixel over a smaller sheet it would not beat the 1851 result the 1845 cohort already uses. Worth re-requesting at higher resolution from LoC. |
| `baltimore_1804_full.jp2` LoC [77691636](https://www.loc.gov/item/77691636/) | 3,703 × 2,932 | not usable | Fifteen years before the first cohort and too coarse. Context only. |
| `baltimore_1869_full.jp2` Sachse bird's eye, LoC [75694535](https://www.loc.gov/item/75694535/) | 39,440 × 19,008 | **cannot be georeferenced** | Oblique perspective view, not planimetric. No 2D polynomial or spline models a bird's eye projection, and fitting one would produce a confident-looking result that is wrong everywhere off the control points. It is a superb illustration and a trap as a base layer. |
| `maryland_1819_with_baltimore_inset.jpg` Digital Maryland [cator/163](https://collections.digitalmaryland.org/digital/collection/cator/id/163) | small inset | not usable | Baltimore appears as a state-map inset. |

### 4.3 What would most improve the result, in order

1. **Georeference the 1866 Woods / Sides sheet.** It is already on disk. It
   closes the 1868 gap, which covers 45.5 percent of the corpus and currently
   has nothing. Expected accuracy about 26 to 30 m by analogy with the 1860
   sheet at the same scale. One agent, one day, following
   `docs/GEOREFERENCING_METHOD.md`.
2. **Georeference Scott's 1856 map and retire the 1857 city-and-county sheet
   for the 1860 cohort.** Also already on disk, at 2.4× the ground resolution,
   city only, so it should reach roughly 12 to 15 m against 1857's honest 35 m.
   This is the largest single accuracy gain available anywhere in the series
   for zero acquisition cost.
3. **Fix the address ladder, not the base layer.** Sixty-nine percent of 1860
   and 71 percent of 1868 residents are placed proportionally along a whole
   street. Reading period street extents off the georeferenced rasters, so that
   proportional interpolation runs along the stretch that existed in that year
   rather than along the full modern street, attacks the 400 m error that
   section 3 identifies as dominant. This is worth more than everything else on
   this list combined.
4. **Expand the external validation set.** Thirty-eight census-confirmed
   residents is a thin basis for the only end-to-end accuracy figure the
   project has. Two hundred would let the ward-match rate be reported per
   confidence tier with a usable confidence interval.
5. **Add independent check points to the other four sheets.** Only 1851 has a
   second-operator check set, and it is the reason 1851 is the one result whose
   accuracy claim rests on genuinely held-out data rather than on cross
   validation of the fit set. Seven of its check points were read at crossings
   that were also control points, and the inter-operator disagreement was a
   median 5 px and a maximum 36 px, which is the only direct measurement of
   pixel-reading uncertainty anywhere in the series.
6. **Repo hygiene, for whoever owns those files.** `scripts/georeference_1851.py`
   (v1) writes to the same `gcps_1851.csv` and `baltimore_1851_georef.tif`
   paths that the v2 pass now owns, so re-running it silently destroys the best
   result in the series. And `docs/GEOREFERENCE.md` still states the 220 to
   260 m Jones Falls displacement and that "Front Street no longer exists in
   any form", both of which section 2.2 refutes.

### 4.4 The limits of all of this

Three things this series cannot do, stated plainly so nobody claims otherwise
later.

- **It cannot measure absolute displacement.** Least squares zeroes the mean
  disagreement with the reference by construction. Every accuracy number here
  is local, relative distortion after fitting. A uniform shift of the whole
  1930 survey, or of the whole 1851 sheet, would leave no trace in any residual
  in any table above.
- **It cannot say whether HUE faithfully represents 1930 geometry.** HUE is a
  modern GIS digitisation of c.1930 sheets. Showing that it agrees with today's
  centrelines establishes that it is correctly georeferenced, not that its
  source sheets were accurate. That is enough for this project's purpose and it
  is less than the phrase "validated against 1930" would imply.
- **It cannot speak to filled land.** All five georeferences deliberately
  avoided shoreline and watercourse control points because those features moved.
  The consequence is that harbor fill is untested rather than cleared. The
  waterfront zone in section 2.4 is made of inland street crossings near the
  modern shore, not of points on made ground.

---

## Sources and reproduction

Control tables and rasters are in `data/work/maps/`. Per-map write-ups are in
`docs/georef/1822.md`, `1836.md`, `1851.md`, `1857.md`, `1860.md`, and the
cross-map reconciliation is in `docs/GEOREFERENCE_RECONCILIATION.md`. Scans are
in `data/raw/maps/` with Library of Congress and Digital Maryland item URLs
recorded in `scripts/build_maps_page.py` and reproduced in section 4.2.

Numbers computed for this file, rather than carried forward from a review:
the zone classification and all of section 2.4, the trend tests in section 2.3,
the Helmert and affine geometry table, the leverage and hull figures in section
1, the resident coverage and distance-to-control figures, the period-ward
containment test, and the fit-residual column in section 2.5. Reference
geometry used: `data/raw/balt_streets.geojson` for the modern centrelines and
`data/raw/hue/HUE_Baltimore_Wards/` for the period wards, both reprojected to
EPSG:6487. Resident coordinates were read read-only from `data/baltimore.db`. Working
scripts for the recomputation are in the session scratchpad and are not part of
the repo.
