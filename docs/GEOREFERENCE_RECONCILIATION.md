# Reconciling five independent georeferences

Five period maps were georeferenced separately, by agents that did not see each
other's work, against the method in `docs/GEOREFERENCING_METHOD.md`. This file
compares the results and records what survives comparison.

Reconciled 2026-08-08. Numbers below were recomputed from the control-point
tables in `data/work/maps/`, not copied from the individual write-ups.

## Accuracy per map

Leave-one-out cross-validated RMSE. Fit residuals are deliberately not shown,
because a fit residual is training error and TPS drives it to zero by
construction.

| Map | GCPs | LOO affine | LOO poly 2 | LOO TPS |
|---|---:|---:|---:|---:|
| Poppleton 1822 | 28 | 24.4 m | 15.3 m | 13.3 m |
| Lucas 1836 | 42 | 21.4 m | 18.5 m | 15.1 m |
| Sidney & Neff 1851 | 54 | 15.9 m | 13.7 m | 11.4 m |
| City & County 1857 | 39 | 42.9 m | 35.0 m | 25.1 m |
| Directory map 1860 | 27 | 26.2 m | 26.0 m | 26.1 m |

The 1851 figure here (54 control points) differs from the headline in
`docs/GEOREFERENCE.md` (12.86 m) because that one uses the combined 68-point
network including the independent check points.

**1857 is the weakest and should be treated with caution.** It is a city *and
county* sheet, so the city occupies a smaller fraction of the image and every
pixel is worth more ground. 1860 is next weakest and has the fewest points.

## Do not read TPS winning four rows as TPS being the right choice

It is not, and the 1851 work is the reason we know. Thin plate spline was the
best model inside the control hull and the **worst** outside it, by a factor of
2.6, reaching 78.9 m at Fort McHenry. Its radial basis grows without bound
where there is nothing holding it down.

Leave-one-out cannot detect this, because every held-out point is by
construction surrounded by the others. Only check points placed deliberately
outside the control hull revealed it, and only the 1851 pass did that. So the
TPS column above is optimistic for exactly the areas where these maps are
weakest, which is the city edge.

Unless a map's own write-up did an out-of-hull test, prefer polynomial 2.

## The convergent finding

Four of the five maps independently measured how far the HUE c.1930 street file
sits from a modern survey, using different reference sources.

| Map | n | median | mean | max | reference used |
|---|---:|---:|---:|---:|---|
| 1822 | 28 | 2.40 m | 4.42 m | 26.3 m | modern centrelines |
| 1851 | 50 | 2.35 m | 3.06 m | 14.7 m | modern centrelines |
| 1857 | 39 | 2.31 m | 3.27 m | 11.8 m | OpenStreetMap |
| 1860 | 26 | 1.55 m | 3.03 m | 12.0 m | modern centrelines |

Four measurements, four maps, four agents working independently, two different
modern reference sources, all landing between 1.5 and 2.4 m median.

**The c.1930 base layer this project places every resident on is within a few
metres of a modern survey wherever the street grid survived.** That is not what
we assumed. The seventy-year gap between the base layer and the period being
mapped is not a meaningful source of error for most of the city, and earlier
statements on this site that implied otherwise were wrong.

Convergence across independent attempts is the reason to believe it. Any single
one of these numbers could be an artifact of one agent's choices. Four agreeing
to within a metre, on different maps, is not.

## What this does and does not license

**Does:** stop discounting the whole city for base-layer error. Where the grid
survived, HUE is fine and our placement error comes from the directories and the
interpolation, not from the streets.

**Does not:** extend to the places the grid did not survive. Those are specific
and identifiable rather than spread evenly:

- **The Jones Falls corridor.** Front Street no longer exists in any form. The
  1851 work measured the channel 33 to 45 m from the modern Fallsway while
  Front Street landed 220 to 260 m from HUE's `FRONT`.
- **The filled waterfront.** Baltimore's harbour was extensively filled, so
  shoreline geometry is not comparable across the period at all.
- **The city edge**, where all five control networks thin out and where TPS in
  particular fails.

These should be flagged individually on the maps rather than folded into a
global accuracy caveat.

## Still outstanding

The Johns Hopkins Sheridan Libraries publish a georeferenced 1851 Sidney & Neff
tile layer, produced in 2017 for Lawrence Jackson's own course (see
`docs/BALTIMORE_GEOGRAPHIES.md`). Comparing our 68-point transform against it is
a cheap independent test of both and has not been done yet.

Map Warper's Lucas 1836 georeference carries 151 control points at 18.8 m median
residual, against our 42 points at 18.5 m LOO. Those are close enough that
comparing the two would be informative about whether either has a systematic
offset.
