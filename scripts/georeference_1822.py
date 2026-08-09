#!/usr/bin/env python3
"""Georeference Poppleton's 1822 Plan of the City of Baltimore, and measure how
far it disagrees with the circa-1930 HUE street file that every resident in this
project is currently placed against.

Source scan
-----------
data/raw/maps/baltimore_1822_poppleton.jp2, 6975 x 5506 px.
Library of Congress, "Plan of the city of Baltimore", surveyed by Thomas H.
Poppleton, published by Fielding Lucas Jr., 1822. LC call no. G3844.B2 1822 .L8.
https://www.loc.gov/item/2002624027/   (accessed 2026-08-08)

Why this map. Poppleton was commissioned in 1818 to survey and fix the city's
streets, so this sheet is the legal plat Baltimore was actually built from. It
is contemporary with the 1819 and 1822 directory cohorts, which are the years
the project currently places worst.

What is different from scripts/georeference_1851.py
---------------------------------------------------
1. CONTROL NETWORK. 33 points read off the sheet, 28 of which survive to the
   fit, against 12 in the 1851 attempt, and deliberately spread rather than
   strung along one street. Nine sit on Baltimore Street, so a third of the
   network rather than the 1851 attempt's seven twelfths. The set reaches
   Biddle Street in the north, Clement Street in the south, Amity Street in
   the west and Washington Street in Fells Point in the east.
2. HONEST ERROR. The headline number is leave-one-out cross validation: fit on
   n-1 points, predict the held-out point, repeat. Fit RMSE is reported too but
   is training error and is optimistically biased by construction. For the thin
   plate spline the fit residual is exactly zero because a TPS interpolates its
   control points, so for TPS the fit RMSE is not an accuracy measure at all.
3. NON-CIRCULAR REFERENCE. The 1851 attempt took its control coordinates from
   the HUE c.1930 street file, which is the very layer the result was meant to
   be compared against, so its displacement figure was partly circular. Here the
   control coordinates come from a modern Baltimore centreline file
   (data/raw/balt_streets.geojson), which is independent of HUE. HUE positions
   for the same corners are computed separately and only ever used as the thing
   being measured, never as the thing being fit to. A parallel fit against HUE
   is also reported so the two references can be compared directly.

Discipline on the control points themselves. Every pixel coordinate below was
read off the full-resolution scan by cropping the neighbourhood with Pillow and
looking at it. Nothing here is interpolated from a street grid model. The crop
box that each point was read from is recorded in the `crop` field so the read is
re-checkable. Points that could not be confirmed were left out rather than
guessed, and are listed in NOT_USED with the reason.

Two traps specific to this sheet, both found the hard way:
  * The scan is of a DISSECTED map, cut into sections and mounted on linen.
    The section seams show as dark vertical and horizontal lines at
    x = 867, 1735, 2606, 3478, 4350, 5232 and y = 1275, 2715, 4155. The seam at
    x=2606 runs straight down Paca Street and the seam at x=4350 runs down Bond
    Street, so both of those streets were avoided as control points: the seam
    hides the street edges and the sections may be very slightly misregistered
    against each other.
  * Harford Run, a real watercourse, is drawn as a hatched vertical band at
    x is about 4090 and reads like a street at low zoom. It was culverted long
    ago and is not a control feature.

Outputs
  data/work/maps/gcps_1822.csv               control points, per-point residuals,
                                             per-point leave-one-out errors
  data/work/maps/baltimore_1822_georef.tif   warped GeoTIFF, EPSG:6487
  data/work/maps/baltimore_1822.points       QGIS georeferencer format, written
                                             ONLY if GDAL cannot be reached
  docs/georef/1822.md                        written separately, not by this script

The affine coefficients are printed to stdout rather than written to a file:
the GeoTIFF is the deliverable and the CSV carries every control point, so a
third artefact would only be one more thing to keep in step.
"""

import csv

import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import geocode_1860 as g  # noqa: E402  (sys.path must be set up first)

MAPS = ROOT / "data" / "raw" / "maps"
WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

JP2 = MAPS / "baltimore_1822_poppleton.jp2"
FULL_SIZE = (6975, 5506)          # gdalinfo on the jp2
CRS_EPSG = 6487                   # NAD83(2011) / Maryland, metres, project standard

SOURCE_URL = "https://www.loc.gov/item/2002624027/"
ACCESS_DATE = "2026-08-08"

# Dissection seams measured off the blank margins of the scan (see module
# docstring). Kept here so a later reader can see which points sit near one.
SEAMS_X = (867, 1735, 2606, 3478, 4350, 5232)
SEAMS_Y = (1275, 2715, 4155)

# Bounding box, in EPSG:4326, used to clip both reference street files before
# any name is merged. Without it, "ST CHARLES AV" in the northern county merges
# into the CHARLES bucket and "WASHINGTON BLVD" into WASHINGTON.
CLIP_BBOX = (-76.66, 39.24, -76.55, 39.33)

# ---------------------------------------------------------------------------
# Ground control points.
#
# (name, street_a_core, street_b_core, pixel_x, pixel_y, crop, note)
#
# pixel_x / pixel_y are FULL RESOLUTION pixels on the jp2 (6975 x 5506), taken
# at the centre of the crossing of the two street corridors as drawn.
# `crop` is the full-res box the point was read from, as x0,y0,x1,y1, so the
# read can be repeated.
# ---------------------------------------------------------------------------
GCPS = [
    # --- north ---------------------------------------------------------------
    ("Charles & Biddle",      "CHARLES",   "BIDDLE",    3076, 1001, "2950,950,3350,1250", ""),
    ("Calvert & Biddle",      "CALVERT",   "BIDDLE",    3243, 1001, "2950,950,3350,1250", ""),
    ("Charles & Chase",       "CHARLES",   "CHASE",     3076, 1093, "2950,950,3350,1250", ""),
    ("Eutaw & Madison",       "EUTAW",     "MADISON",   2682, 1411, "2500,1300,2900,1600", ""),
    ("Broadway & Monument",   "BROADWAY",  "MONUMENT",  4472, 1499, "4300,1380,4700,1680", ""),
    ("Charles & Centre",      "CHARLES",   "CENTRE",    3078, 1616, "2950,1400,3350,1700", ""),
    # --- north-west of centre ------------------------------------------------
    ("Pine & Franklin",       "PINE",      "FRANKLIN",  2296, 1736, "2150,1550,2550,1850", ""),
    ("Pearl & Franklin",      "PEARL",     "FRANKLIN",  2456, 1736, "2150,1550,2550,1850", ""),
    # --- Baltimore Street, west to east --------------------------------------
    ("Amity & Baltimore",     "AMITY",     "BALTIMORE", 1874, 2187, "1750,2100,2150,2400", "platted, not yet built in 1822"),
    ("Poppleton & Baltimore", "POPPLETON", "BALTIMORE", 1928, 2187, "1750,2100,2150,2400", "platted, not yet built in 1822"),
    ("Scott & Baltimore",     "SCOTT",     "BALTIMORE", 2128, 2187, "1750,2100,2150,2400", "platted, not yet built in 1822"),
    ("Eutaw & Baltimore",     "EUTAW",     "BALTIMORE", 2697, 2190, "2620,2100,2820,2270", ""),
    ("Charles & Baltimore",   "CHARLES",   "BALTIMORE", 3088, 2187, "2950,2060,3250,2310", ""),
    ("Calvert & Baltimore",   "CALVERT",   "BALTIMORE", 3260, 2184, "3150,2050,3450,2300", ""),
    ("Gay & Baltimore",       "GAY",       "BALTIMORE", 3466, 2185, "3350,2050,3750,2350", "seam at x=3478 is close"),
    ("Eden & Baltimore",      "EDEN",      "BALTIMORE", 4157, 2074, "4100,1950,4500,2250", ""),
    ("Caroline & Baltimore",  "CAROLINE",  "BALTIMORE", 4272, 2073, "4100,1950,4500,2250", ""),
    ("Broadway & Baltimore",  "BROADWAY",  "BALTIMORE", 4480, 2075, "4350,1980,4650,2330", ""),
    # --- Pratt Street --------------------------------------------------------
    ("Poppleton & Pratt",     "POPPLETON", "PRATT",     1924, 2438, "1850,2350,2250,2650", "platted, not yet built in 1822"),
    ("Eutaw & Pratt",         "EUTAW",     "PRATT",     2701, 2439, "2550,2320,2950,2620", ""),
    ("Charles & Pratt",       "CHARLES",   "PRATT",     3091, 2446, "2950,2320,3350,2620", ""),
    ("Broadway & Pratt",      "BROADWAY",  "PRATT",     4480, 2251, "4350,1980,4650,2330", ""),
    # --- Fells Point and the east --------------------------------------------
    ("Wolfe & Bank",          "WOLFE",     "BANK",      4708, 2485, "4550,2350,4950,2650", ""),
    ("Broadway & Aliceanna",  "BROADWAY",  "ALICEANNA", 4480, 2731, "4250,2650,4650,2950", ""),
    ("Washington & Aliceanna", "WASHINGTON", "ALICEANNA", 4790, 2721, "4650,2620,5050,2880", ""),
    ("Ann & Thames",          "ANN",       "THAMES",    4628, 2878, "4500,2780,4900,3020", ""),
    # --- south ---------------------------------------------------------------
    ("Sharp & Conway",        "SHARP",     "CONWAY",    2903, 2630, "2700,2550,3100,2850", ""),
    ("Hanover & Conway",      "HANOVER",   "CONWAY",    2998, 2630, "2700,2550,3100,2850", ""),
    ("Sharp & Barre",         "SHARP",     "BARRE",     2903, 2709, "2700,2550,3100,2850", ""),
    ("Charles & Hamburg",     "CHARLES",   "HAMBURG",   3086, 3182, "2950,3150,3350,3450", ""),
    ("Charles & Cross",       "CHARLES",   "CROSS",     3086, 3270, "2950,3150,3350,3450", ""),
    ("Hanover & Clement",     "HANOVER",   "CLEMENT",   3004, 3549, "3000,3450,3400,3750", ""),
    ("Charles & Clement",     "CHARLES",   "CLEMENT",   3085, 3549, "3000,3450,3400,3750", ""),
]

# Intersections used only to audit the two reference layers against each other.
# These are never fit to and never read off the 1822 sheet: they exist so the
# HUE-vs-modern comparison can be run in the Jones Falls corridor and other
# places the control network does not reach.
AUDIT_PAIRS = [
    # Jones Falls corridor, the place this project has previously measured
    # 200 m plus of displacement
    ("FRONT", "BALTIMORE"), ("FRONT", "LOMBARD"), ("FRONT", "FAYETTE"),
    ("EXETER", "BALTIMORE"), ("EXETER", "LOMBARD"),
    ("CENTRAL", "BALTIMORE"), ("CENTRAL", "PRATT"), ("CENTRAL", "LOMBARD"),
    ("HOLLIDAY", "FAYETTE"), ("GAY", "MONUMENT"), ("GAY", "ORLEANS"),
    # elsewhere, for contrast
    ("EUTAW", "LOMBARD"), ("EUTAW", "FAYETTE"), ("CHARLES", "LOMBARD"),
    ("CHARLES", "FAYETTE"), ("CHARLES", "SARATOGA"), ("CHARLES", "MULBERRY"),
    ("CAREY", "BALTIMORE"), ("FREMONT", "BALTIMORE"), ("GILMOR", "BALTIMORE"),
    ("MOUNT", "BALTIMORE"), ("BROADWAY", "FLEET"), ("BROADWAY", "GOUGH"),
    ("CHESTER", "BANK"), ("WOLFE", "MONUMENT"), ("CAROLINE", "PRATT"),
    ("LIGHT", "CROSS"), ("LIGHT", "MONTGOMERY"), ("WILLIAM", "CROSS"),
    ("CHARLES", "PRESTON"), ("CHARLES", "EAGER"), ("EUTAW", "DOLPHIN"),
]

# Points that were located on the sheet but deliberately left out, with why.
NOT_USED = [
    ("Greene & Baltimore (2508, 2186)",
     "Read cleanly off crop 2420,2100,2620,2270, but N/S GREENE ST is absent "
     "from data/raw/balt_streets.geojson, so there is no independent modern "
     "coordinate for it. Left out rather than fall back to HUE for one point "
     "and thereby reintroduce the circularity this script exists to avoid."),
    ("Paca & Baltimore (approx 2600, 2185)",
     "A dissection seam in the scan runs straight down Paca Street at x=2606, "
     "hiding the street edges. The corridor measures 42 px wide where Paca "
     "should be about 16 px, so the read is not trustworthy."),
    ("Bond & Aliceanna (approx 4359, 2731)",
     "Same problem: the seam at x=4350 runs down Bond Street."),
    ("Sharp & Baltimore",
     "The sheet shows N Sharp and S Sharp crossing Baltimore Street. North of "
     "Baltimore that line is Liberty Street today, so a modern SHARP ST "
     "intersection would not be the same corner."),
    ("Washington Monument, Battle Monument and other landmark symbols",
     "Both monuments were found on the sheet (74 at 3076,1501 and 75 near "
     "3252,2108) and both still stand, so they are tempting. They were not "
     "used because the map draws them as small reference squares whose "
     "relationship to the modern surveyed monument point is a guess of "
     "perhaps 20 m, and the street network already covers those two spots."),
    ("The north-west projected grid (Pennsylvania Avenue and north of Dolphin)",
     "Poppleton drew that quadrant as a diagonal lattice of streets that were "
     "platted but not built. The district as actually built does not follow "
     "that lattice, so its corners are not the same corners. This leaves a "
     "real hole in the control network in the north-west, stated plainly in "
     "docs/georef/1822.md rather than filled with invented points."),
]


# ---------------------------------------------------------------------------
# Reference geometry
# ---------------------------------------------------------------------------

def _merge_by_core(gdf, name_field):
    """One merged geometry per normalised street core name.

    Reuses geocode_1860.norm_street so this script matches names the same way
    the rest of the project does, rather than inventing a second convention."""
    from shapely.ops import unary_union
    buckets = defaultdict(list)
    for name, geom in zip(gdf[name_field], gdf.geometry):
        if not name:
            continue
        core, _ = g.norm_street(name)
        if core:
            buckets[core].append(geom)
    return {core: unary_union(geoms) for core, geoms in buckets.items()}


def load_reference(which):
    """Return {core_name: geometry} in EPSG:6487 for one reference source.

    which == 'modern' -> data/raw/balt_streets.geojson, independent of HUE.
    which == 'hue'    -> the c.1930 HUE street file, i.e. the layer this
                         project currently places residents against.
    Both are clipped to CLIP_BBOX first so that same-named streets elsewhere in
    the county cannot merge into a downtown bucket."""
    import geopandas as gpd
    from shapely.geometry import box

    if which == "modern":
        gdf = gpd.read_file(ROOT / "data" / "raw" / "balt_streets.geojson")
        field = "ROAD_NAME"
    elif which == "hue":
        gdf = gpd.read_file(g.HUE_SHP)
        field = "Full_Name"
    else:
        raise ValueError(which)

    gdf = gdf[gdf[field].notna()].to_crs(epsg=4326)
    gdf = gdf[gdf.intersects(box(*CLIP_BBOX))]
    gdf = gdf.to_crs(epsg=CRS_EPSG)
    return _merge_by_core(gdf, field)


SNAP_TOL_M = 30.0   # see crossing_candidates()


def crossing_candidates(streets, core_a, core_b):
    """All the points at which two named streets cross, as (x, y, snap_m).

    If the two geometries do not actually touch, they are snapped together when
    the gap is under SNAP_TOL_M. This is not a fudge for a missing street: the
    modern centreline file used here is a partial extract, and several of its
    lines simply stop a few metres short of the corner they clearly form (for
    example N Pine St ends about 20 m south of W Franklin St). A real absence
    produces no geometry at all and is reported as a miss, not snapped. The gap
    used is written into the CSV as snap_m so any point that leaned on this can
    be audited."""
    from shapely.ops import nearest_points
    ga, gb = streets.get(core_a), streets.get(core_b)
    if ga is None or gb is None:
        return []
    inter = ga.intersection(gb)
    if not inter.is_empty:
        pts = []
        for part in getattr(inter, "geoms", [inter]):
            if part.geom_type == "Point":
                pts.append((part.x, part.y, 0.0))
            else:                   # overlapping collinear stretch: use midpoint
                c = part.centroid
                pts.append((c.x, c.y, 0.0))
        return pts
    gap = ga.distance(gb)
    if gap <= SNAP_TOL_M:
        pa, pb = nearest_points(ga, gb)
        return [((pa.x + pb.x) / 2, (pa.y + pb.y) / 2, float(gap))]
    return []


# ---------------------------------------------------------------------------
# Transforms. Each returns predict(P) where P is an (n,2) array of pixel coords.
# ---------------------------------------------------------------------------

def _design_affine(P):
    return np.column_stack([np.ones(len(P)), P[:, 0], P[:, 1]])


def _design_poly2(P):
    x, y = P[:, 0], P[:, 1]
    return np.column_stack([np.ones(len(P)), x, y, x * x, x * y, y * y])


def _fit_poly(P, W, design):
    """Least-squares polynomial fit from pixel to world, one solve per axis."""
    A = design(P)
    cx, *_ = np.linalg.lstsq(A, W[:, 0], rcond=None)
    cy, *_ = np.linalg.lstsq(A, W[:, 1], rcond=None)

    def predict(Q):
        B = design(Q)
        return np.column_stack([B @ cx, B @ cy])

    predict.coeffs = (cx, cy)
    return predict


def fit_affine(P, W):
    return _fit_poly(P, W, _design_affine)


def fit_poly2(P, W):
    return _fit_poly(P, W, _design_poly2)


def fit_tps(P, W):
    """Thin plate spline. Interpolates the control points exactly, so its fit
    residual is ~0 by construction and says nothing about accuracy. Only its
    leave-one-out error is meaningful.

    Pixel coordinates are scaled to order 1 before fitting: an unscaled TPS on
    coordinates of order 5000 is numerically miserable."""
    from scipy.interpolate import RBFInterpolator
    mu, sd = P.mean(axis=0), P.std(axis=0)
    rbf = RBFInterpolator((P - mu) / sd, W, kernel="thin_plate_spline",
                          smoothing=0.0, degree=1)

    def predict(Q):
        return rbf((Q - mu) / sd)

    return predict


FITTERS = {"affine": fit_affine, "poly2": fit_poly2, "tps": fit_tps}
MIN_POINTS = {"affine": 3, "poly2": 6, "tps": 3}


def residuals(fitter, P, W):
    pred = fitter(P, W)(P)
    return np.hypot(*(pred - W).T)


def loocv(fitter_name, P, W):
    """Leave-one-out error per point, in metres. The honest accuracy estimate."""
    fitter = FITTERS[fitter_name]
    n = len(P)
    out = np.full(n, np.nan)
    if n <= MIN_POINTS[fitter_name]:
        return out
    for i in range(n):
        keep = np.arange(n) != i
        pred = fitter(P[keep], W[keep])(P[i:i + 1])[0]
        out[i] = float(np.hypot(*(pred - W[i])))
    return out


def rmse(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(np.sqrt(np.mean(v ** 2))) if len(v) else float("nan")


# ---------------------------------------------------------------------------
# Building the control table
# ---------------------------------------------------------------------------

def resolve_world(streets, label):
    """Attach a world coordinate to every GCP against one reference source.

    Streets can cross more than once, so ambiguity is resolved by bootstrapping:
    fit an affine on the points whose crossing is already unique, then for each
    ambiguous point take the candidate closest to where that affine predicts it.
    Iterated twice, which is enough for a network this size."""
    cand = {}
    for name, a, b, px, py, *_ in GCPS:
        cand[name] = crossing_candidates(streets, a, b)

    chosen = {n: c[0] for n, c in cand.items() if len(c) == 1}
    missing = [n for n, c in cand.items() if not c]

    for _ in range(2):
        rows = [(n, px, py) for n, _a, _b, px, py, *_ in GCPS if n in chosen]
        if len(rows) < 4:
            break
        P = np.array([[px, py] for _n, px, py in rows], float)
        W = np.array([chosen[n][:2] for n, _px, _py in rows], float)
        predict = fit_affine(P, W)
        for name, _a, _b, px, py, *_ in GCPS:
            c = cand[name]
            if len(c) <= 1:
                continue
            guess = predict(np.array([[px, py]], float))[0]
            chosen[name] = min(c, key=lambda p: (p[0] - guess[0]) ** 2 + (p[1] - guess[1]) ** 2)

    if missing:
        print(f"  [{label}] no crossing found for: {', '.join(sorted(missing))}")
    multi = sorted(n for n, c in cand.items() if len(c) > 1)
    if multi:
        print(f"  [{label}] {len(multi)} pair(s) crossed more than once, "
              f"resolved by nearest prediction: {', '.join(multi)}")
    return chosen, cand


def build_table():
    print("Loading reference geometry ...")
    modern = load_reference("modern")
    hue = load_reference("hue")
    print(f"  modern: {len(modern)} street names   HUE: {len(hue)} street names")

    modern_xy, modern_cand = resolve_world(modern, "modern")
    hue_xy, _hue_cand = resolve_world(hue, "hue")

    rows = []
    for name, a, b, px, py, crop, note in GCPS:
        if name not in modern_xy:
            continue                       # no independent coordinate, cannot use
        mx, my, snap = modern_xy[name]
        hx, hy, _ = hue_xy.get(name, (np.nan, np.nan, np.nan))
        rows.append({
            "name": name, "street_a": a, "street_b": b,
            "pixel_x": float(px), "pixel_y": float(py),
            "crop": crop, "note": note,
            "modern_x": mx, "modern_y": my, "snap_m": snap,
            "hue_x": hx, "hue_y": hy,
            "n_modern_candidates": len(modern_cand[name]),
            "near_seam": _near_seam(px, py),
        })
    dropped = [n for n, *_ in GCPS if n not in modern_xy]
    if dropped:
        print(f"  dropped for lack of a modern coordinate: {', '.join(dropped)}")
    return rows, modern, hue


def audit_references(modern, hue):
    """How far apart the two reference layers put the same street corner.

    This is the non-circular part of the displacement question: it is measured
    entirely between the two street files and does not involve the 1822 scan at
    all, so it can be run in places the control network does not reach, notably
    the Jones Falls corridor."""
    out = []
    for a, b in AUDIT_PAIRS:
        mc = crossing_candidates(modern, a, b)
        hc = crossing_candidates(hue, a, b)
        if not mc or not hc:
            out.append((f"{a} & {b}", np.nan, "missing in "
                        + ("modern" if not mc else "HUE")))
            continue
        # pair up the nearest candidates: with one crossing each this is exact,
        # and where a street crosses twice it keeps the comparison local
        best = min(((m, h) for m in mc for h in hc),
                   key=lambda mh: (mh[0][0] - mh[1][0]) ** 2 + (mh[0][1] - mh[1][1]) ** 2)
        d = float(np.hypot(best[0][0] - best[1][0], best[0][1] - best[1][1]))
        out.append((f"{a} & {b}", d, ""))
    return out


def _near_seam(px, py, tol=25):
    """Flag control points sitting within `tol` px of a dissection seam."""
    hits = [f"x={s}" for s in SEAMS_X if abs(px - s) <= tol]
    hits += [f"y={s}" for s in SEAMS_Y if abs(py - s) <= tol]
    return ";".join(hits)


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def write_csv(rows, path):
    cols = ["name", "street_a", "street_b", "pixel_x", "pixel_y",
            "modern_x_epsg6487", "modern_y_epsg6487",
            "hue_x_epsg6487", "hue_y_epsg6487",
            "res_affine_m", "res_poly2_m", "res_tps_m",
            "loo_affine_m", "loo_poly2_m", "loo_tps_m",
            "hue_vs_modern_m", "map1822_vs_hue_m",
            "snap_m", "n_modern_candidates", "near_seam", "crop", "note"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({
                "name": r["name"], "street_a": r["street_a"], "street_b": r["street_b"],
                "pixel_x": f"{r['pixel_x']:.0f}", "pixel_y": f"{r['pixel_y']:.0f}",
                "modern_x_epsg6487": f"{r['modern_x']:.2f}",
                "modern_y_epsg6487": f"{r['modern_y']:.2f}",
                "hue_x_epsg6487": "" if np.isnan(r["hue_x"]) else f"{r['hue_x']:.2f}",
                "hue_y_epsg6487": "" if np.isnan(r["hue_y"]) else f"{r['hue_y']:.2f}",
                "res_affine_m": f"{r['res_affine']:.1f}",
                "res_poly2_m": f"{r['res_poly2']:.1f}",
                "res_tps_m": f"{r['res_tps']:.1f}",
                "loo_affine_m": f"{r['loo_affine']:.1f}",
                "loo_poly2_m": f"{r['loo_poly2']:.1f}",
                "loo_tps_m": f"{r['loo_tps']:.1f}",
                "hue_vs_modern_m": "" if np.isnan(r["hue_vs_modern"]) else f"{r['hue_vs_modern']:.1f}",
                "map1822_vs_hue_m": "" if np.isnan(r["map1822_vs_hue"]) else f"{r['map1822_vs_hue']:.1f}",
                "snap_m": f"{r['snap_m']:.1f}",
                "n_modern_candidates": r["n_modern_candidates"],
                "near_seam": r["near_seam"], "crop": r["crop"], "note": r["note"],
            })


def write_points_file(rows, path):
    """QGIS Georeferencer .points format. QGIS stores pixel row as negative."""
    with open(path, "w") as f:
        f.write(f"#CRS: EPSG:{CRS_EPSG}\n")
        f.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in rows:
            f.write(f"{r['modern_x']:.3f},{r['modern_y']:.3f},"
                    f"{r['pixel_x']:.3f},{-r['pixel_y']:.3f},1\n")


def find_gdal():
    """Locate the GDAL binaries, preferring the QGIS bundle since this Mac has
    no system GDAL (see scripts/qgis_env.sh)."""
    env = os.environ.copy()
    if shutil.which("gdal_translate") and shutil.which("gdalwarp"):
        return "gdal_translate", "gdalwarp", env
    qgis = Path("/Applications/QGIS-final-4_2_1.app/Contents/MacOS")
    if (qgis / "gdal_translate").exists() and (qgis / "gdalwarp").exists():
        env["PATH"] = str(qgis) + os.pathsep + env.get("PATH", "")
        res = "/Applications/QGIS-final-4_2_1.app/Contents/Resources"
        env["GDAL_DATA"] = f"{res}/qgis/gdal"
        env["PROJ_LIB"] = f"{res}/qgis/proj"
        env["PROJ_DATA"] = f"{res}/qgis/proj"   # PROJ 9 renamed PROJ_LIB
        return str(qgis / "gdal_translate"), str(qgis / "gdalwarp"), env
    return None, None, env


def build_geotiff(rows, method, out_path, max_mb=90):
    """Attach the GCPs with gdal_translate, then warp to a real EPSG:6487
    raster. `method` is 'tps' or a polynomial order. Downsamples if the result
    would break the repo's 90 MB cap."""
    translate, warp, env = find_gdal()
    if translate is None:
        print("GDAL not found. GeoTIFF skipped; the .points file and the "
              "coefficients in the CSV are enough to redo this in QGIS.")
        return None

    gcp_args = []
    for r in rows:
        gcp_args += ["-gcp", f"{r['pixel_x']:.3f}", f"{r['pixel_y']:.3f}",
                     f"{r['modern_x']:.3f}", f"{r['modern_y']:.3f}"]

    tmp = WORK / "_tmp_1822_gcp.tif"
    subprocess.run([translate, "-of", "GTiff", "-a_srs", f"EPSG:{CRS_EPSG}",
                    *gcp_args, str(JP2), str(tmp)], env=env, check=True)

    warp_method = ["-tps"] if method == "tps" else ["-order", str(method)]
    for outsize in (100, 70, 50):
        cmd = [warp, "-r", "cubic", *warp_method,
               "-t_srs", f"EPSG:{CRS_EPSG}",
               "-co", "COMPRESS=JPEG", "-co", "JPEG_QUALITY=85",
               "-co", "TILED=YES", "-co", "PHOTOMETRIC=YCBCR",
               "-overwrite", str(tmp), str(out_path)]
        if outsize != 100:
            # gdalwarp has no -outsize, so scale via target resolution instead
            cmd[1:1] = ["-ts", str(int(FULL_SIZE[0] * outsize / 100)), "0"]
        subprocess.run(cmd, env=env, check=True)
        mb = out_path.stat().st_size / 1e6
        if mb <= max_mb:
            print(f"GeoTIFF: {out_path}  {mb:.1f} MB  "
                  f"({outsize}% of source width, warp={method})")
            break
        print(f"  {mb:.1f} MB at {outsize}% is over the {max_mb} MB cap, downsampling")
    tmp.unlink(missing_ok=True)
    for aux in WORK.glob("_tmp_1822_gcp.tif.*"):
        aux.unlink(missing_ok=True)
    return out_path


# ---------------------------------------------------------------------------

def main():
    rows, modern, hue = build_table()
    P = np.array([[r["pixel_x"], r["pixel_y"]] for r in rows], float)
    W = np.array([[r["modern_x"], r["modern_y"]] for r in rows], float)
    n = len(rows)
    print(f"\n{n} usable ground control points\n")

    summary = {}
    for kind in ("affine", "poly2", "tps"):
        res = residuals(FITTERS[kind], P, W)
        loo = loocv(kind, P, W)
        for r, a, b in zip(rows, res, loo):
            r[f"res_{kind}"] = float(a)
            r[f"loo_{kind}"] = float(b)
        summary[kind] = {"fit_rmse": rmse(res), "loo_rmse": rmse(loo),
                         "loo_median": float(np.nanmedian(loo)),
                         "loo_max": float(np.nanmax(loo))}
        print(f"{kind:>7}  fit RMSE {summary[kind]['fit_rmse']:7.1f} m   "
              f"LOOCV RMSE {summary[kind]['loo_rmse']:7.1f} m   "
              f"LOOCV median {summary[kind]['loo_median']:6.1f} m   "
              f"LOOCV worst {summary[kind]['loo_max']:7.1f} m")

    best = min(summary, key=lambda k: summary[k]["loo_rmse"])
    print(f"\nLowest leave-one-out error: {best}")

    # How far the c.1930 HUE geometry sits from the same corner, and how far
    # the georeferenced 1822 map sits from HUE. Neither number is circular:
    # the transform was fit against modern centrelines, not against HUE.
    #
    # The 1822-vs-HUE figure uses the LEAVE-ONE-OUT prediction of each corner,
    # not the in-sample one. With a thin plate spline the in-sample prediction
    # is the control point itself, so an in-sample comparison would collapse
    # into the HUE-vs-modern number and say nothing extra.
    loo_pred = np.full_like(W, np.nan)
    fitter = FITTERS[best]
    for i in range(n):
        keep = np.arange(n) != i
        loo_pred[i] = fitter(P[keep], W[keep])(P[i:i + 1])[0]
    for r, p in zip(rows, loo_pred):
        if np.isnan(r["hue_x"]):
            r["hue_vs_modern"] = np.nan
            r["map1822_vs_hue"] = np.nan
        else:
            r["hue_vs_modern"] = float(np.hypot(r["hue_x"] - r["modern_x"],
                                                r["hue_y"] - r["modern_y"]))
            r["map1822_vs_hue"] = float(np.hypot(p[0] - r["hue_x"], p[1] - r["hue_y"]))

    hvm = np.array([r["hue_vs_modern"] for r in rows], float)
    mvh = np.array([r["map1822_vs_hue"] for r in rows], float)
    print(f"\nHUE c.1930 vs modern, same corner:  median {np.nanmedian(hvm):.0f} m  "
          f"max {np.nanmax(hvm):.0f} m   (n={int(np.isfinite(hvm).sum())})")
    print(f"1822 map (held-out prediction) vs HUE: median {np.nanmedian(mvh):.0f} m  "
          f"max {np.nanmax(mvh):.0f} m")

    print("\nReference-layer audit, HUE c.1930 against modern centrelines, at "
          "corners NOT used as control:")
    audit = audit_references(modern, hue)
    for label, d, why in sorted(audit, key=lambda t: -(t[1] if np.isfinite(t[1]) else -1)):
        print(f"   {label:<26}{'      n/a' if not np.isfinite(d) else format(d, '9.1f')} m  {why}")
    ad = np.array([d for _l, d, _w in audit], float)
    print(f"   -> median {np.nanmedian(ad):.1f} m over "
          f"{int(np.isfinite(ad).sum())} audited corners")

    print(f"\n{'point':<24}{'affine':>8}{'poly2':>8}{'tps':>8}"
          f"{'LOOaff':>8}{'LOOpol':>8}{'LOOtps':>8}{'HUEoff':>8}")
    for r in sorted(rows, key=lambda r: -r["loo_affine"]):
        print(f"{r['name']:<24}{r['res_affine']:8.1f}{r['res_poly2']:8.1f}"
              f"{r['res_tps']:8.1f}{r['loo_affine']:8.1f}{r['loo_poly2']:8.1f}"
              f"{r['loo_tps']:8.1f}"
              f"{'' if np.isnan(r['hue_vs_modern']) else format(r['hue_vs_modern'], '8.1f')}")

    # Extrapolation check. LOOCV only measures accuracy INSIDE the control
    # network. The parts of the sheet with no control near them (the north-west
    # projected grid, Canton, Locust Point, the sheet corners) are the places a
    # flexible transform can misbehave without any warning from LOOCV, so the
    # three models are compared directly out there.
    hull_probe = [
        ("NW projected grid",   1800, 1000),
        ("Canton, far east",    5400, 2700),
        ("Locust Point, south", 5000, 4300),
        ("sheet corner NW",        0,    0),
        ("sheet corner NE",     6975,    0),
        ("sheet corner SW",        0, 5506),
        ("sheet corner SE",     6975, 5506),
    ]
    print("\nDisagreement between transforms outside the control network "
          "(metres from the affine):")
    Q = np.array([[x, y] for _l, x, y in hull_probe], float)
    base = fit_affine(P, W)(Q)
    d2 = np.hypot(*(fit_poly2(P, W)(Q) - base).T)
    dt = np.hypot(*(fit_tps(P, W)(Q) - base).T)
    for (label, _x, _y), a, b in zip(hull_probe, d2, dt):
        print(f"   {label:<22}poly2 {a:9.0f}   tps {b:9.0f}")

    # Sanity check on the fitted affine: does it imply a plausible map scale
    # and rotation? A 1822 city plan at 100 perches to 1.5 inches, scanned at
    # this size, should come out near 1.2 m per pixel with a small rotation.
    cx, cy = fit_affine(P, W).coeffs
    scale_x = float(np.hypot(cx[1], cy[1]))
    scale_y = float(np.hypot(cx[2], cy[2]))
    rot = float(np.degrees(np.arctan2(-cy[1], cx[1])))
    print(f"\naffine implies {scale_x:.3f} m/px across, {scale_y:.3f} m/px down, "
          f"rotation {rot:+.2f} deg")

    write_csv(rows, WORK / "gcps_1822.csv")
    print(f"\nWrote {WORK / 'gcps_1822.csv'}")

    # Print, rather than write, the affine coefficients: the GeoTIFF below is
    # the deliverable, and the CSV already carries every control point, so a
    # third file would only be one more thing to keep in step.
    print(f"affine coefficients, world = c0 + c1*px + c2*py, EPSG:{CRS_EPSG}")
    print(f"  x: {cx[0]:.4f} {cx[1]:+.6f} {cx[2]:+.6f}")
    print(f"  y: {cy[0]:.4f} {cy[1]:+.6f} {cy[2]:+.6f}")

    method = "tps" if best == "tps" else (2 if best == "poly2" else 1)
    made = build_geotiff(rows, method, WORK / "baltimore_1822_georef.tif")
    if made is None:
        # Only when GDAL is unreachable is a QGIS control-point file worth
        # having: it lets the warp be redone by hand without repeating any of
        # the reading-off-the-scan work.
        write_points_file(rows, WORK / "baltimore_1822.points")
        print(f"Wrote {WORK / 'baltimore_1822.points'} (GDAL unavailable)")


if __name__ == "__main__":
    main()
